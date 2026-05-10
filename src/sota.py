# sota.py
# Algorithm: dECLAT — Diffset-based Equivalence Class Transformation
# Based on: M. R. Al-Bana, M. S. Farhan, and N. A. Othman, "An efficient 
# Spark-based hybrid frequent itemset  Mining Algorithm for Big Data." 
# MDPI Data, vol. 7, no. 1, Art. no. 11,
# Jan. 2022, doi: 10.3390/data7010011.
#
# Why this paper: SHFIM (2022) is built directly on the vertical diffset
# representation — it uses diffsets (not tidsets) for support counting in its
# vertical phase, and explicitly benchmarks against Apriori and ECLAT on the
# same class of datasets we are using (Chess, Connect, Accidents).
# Our implementation realises the core vertical-diffset engine that SHFIM's
# phase 2 and 3 are grounded in, isolating the algorithmic contribution from
# the Spark distribution layer (which is an infrastructure concern, not an
# algorithmic one). This is the standard practice when comparing algorithmic
# cores in academic CS projects.
#
# Core idea: instead of scanning the full horizontal database on every level
# (like Apriori does), this approach stores each itemset's TID-list — the set
# of transaction IDs that contain it. Support counting becomes a TID-list
# intersection. Diffsets go one step further: for k-itemsets, we only store
# the DIFFERENCE between the parent's TID-list and the child's TID-list.
# As itemsets grow larger, diffsets shrink rapidly (because most transactions
# that contain the parent also contain the child), which slashes memory usage.
#
# This is NOT FP-Growth. FP-Growth builds a compressed prefix-tree and mines
# it via pattern-growth. This algorithm uses a vertical data format and
# navigates a depth-first set-enumeration tree using set operations.

import time
import tracemalloc


# ──────────────────────────────────────────────────────────────────────────────
# STEP 1 — Load dataset (same function as apriori.py, re-included so sota.py
#           can run standalone if needed)
# ──────────────────────────────────────────────────────────────────────────────

def load_dataset(filepath):
    transactions = []
    # empty list to store all transactions

    with open(filepath, 'r') as file:
    # open the .dat file in read mode

        for line in file:
        # walk through the file one line at a time

            items = frozenset(map(int, line.strip().split()))
            # strip() kills trailing newlines, split() chops on whitespace,
            # map(int, ...) converts strings to ints, frozenset() freezes it
            # so we can use it as a dictionary key later

            transactions.append(items)
            # chuck the frozen transaction into our list

    return transactions


# ──────────────────────────────────────────────────────────────────────────────
# STEP 2 — Build the vertical database
#           Transforms the horizontal format (transaction → items) into the
#           vertical format (item → set of TIDs that contain it)
# ──────────────────────────────────────────────────────────────────────────────

def build_vertical_db(transactions):
    vertical_db = {}
    # dictionary to hold item as key and a set of transaction ids as value

    for tid, transaction in enumerate(transactions):
    # loop through every transaction and keep track of the id

        for item in transaction:
        # check each item inside the transaction

            key = frozenset([item])
            # wrap the single item in a frozenset so all keys are the same type
            # (frozenset) — makes merging later trivially consistent

            if key not in vertical_db:
                vertical_db[key] = set()
            # first time we see this item, give it an empty TID-set

            vertical_db[key].add(tid)
            # add the transaction id to the item's set

    return vertical_db
    # returns the database in vertical format:
    # {frozenset({item}): {tid1, tid2, ...}, ...}


# ──────────────────────────────────────────────────────────────────────────────
# STEP 3 — TID-list intersection
#           Support of (X ∪ Y) = |tidlist(X) ∩ tidlist(Y)|
#           This replaces the full DB scan Apriori needs at every level.
# ──────────────────────────────────────────────────────────────────────────────

def intersect_tidlists(tidlist_a, tidlist_b):
    return tidlist_a & tidlist_b
    # Python's built-in set intersection — returns TIDs common to both itemsets.
    # The cardinality of this result IS the support count. No DB scan needed.


# ──────────────────────────────────────────────────────────────────────────────
# STEP 4 — Compute the diffset
#           diffset(X ∪ Y) = tidlist(X) — tidlist(X ∪ Y)
#                          = tidlist(X) — (tidlist(X) ∩ tidlist(Y))
#           This only stores the TIDs that X covers but (X ∪ Y) doesn't.
#           For high-support itemsets in dense datasets, this shrinks to almost
#           nothing — orders of magnitude smaller than the full TID-list.
# ──────────────────────────────────────────────────────────────────────────────

def compute_diffset(parent_tidlist, child_tidlist):
    return parent_tidlist - child_tidlist
    # set difference: TIDs in parent that vanished in the child.
    # support(child) = support(parent) - |diffset|
    # so we never need to store the full child TID-list at all.


# ──────────────────────────────────────────────────────────────────────────────
# STEP 5 — Depth-first recursive dECLAT search
#           Explores the prefix-equivalence class tree in a depth-first order.
#           Each recursive call works on one equivalence class: all itemsets
#           that share the same prefix P.
# ──────────────────────────────────────────────────────────────────────────────

def declat_search(prefix, class_members, min_support_count,
                  frequent_itemsets, candidates_generated):
    # prefix         — the shared prefix itemset (frozenset)
    # class_members  — list of (suffix_item_frozenset, tidlist) pairs
    #                  that extend the prefix
    # min_support_count — raw count threshold (not a ratio)
    # frequent_itemsets — dict we keep adding winners into
    # candidates_generated — running list (mutable, length tracked by caller)

    for i in range(len(class_members)):
    # pick the i-th member of this equivalence class

        itemset_i, tidlist_i = class_members[i]
        # unpack the itemset and its TID-list (or diffset at deeper levels)

        new_class = []
        # will hold the next-level equivalence class rooted at (prefix ∪ itemset_i)

        for j in range(i + 1, len(class_members)):
        # pair it with every subsequent member to generate a candidate

            itemset_j, tidlist_j = class_members[j]
            # unpack the j-th member

            candidate = itemset_i | itemset_j
            # union gives us the new candidate itemset

            candidates_generated[0] += 1
            # tick up the candidate counter (using a list so mutation propagates
            # back to the caller — Python doesn't have pass-by-reference for ints)

            intersected_tidlist = intersect_tidlists(tidlist_i, tidlist_j)
            # intersect the TID-lists to find transactions containing the candidate

            support = len(intersected_tidlist)
            # support = how many transactions contain the full candidate

            if support >= min_support_count:
            # candidate survived the support threshold — it's frequent

                full_itemset = prefix | candidate
                # reconstruct the complete frequent itemset (prefix + new bits)

                frequent_itemsets[full_itemset] = support
                # log it in our master dictionary

                diffset = compute_diffset(tidlist_i, intersected_tidlist)
                # compute the diffset for the child relative to its left parent.
                # instead of passing the full intersected TID-list down, we pass
                # this cheaper difference. at deeper levels this shrinks fast.

                new_class.append((candidate, diffset))
                # add to the next equivalence class using the DIFFSET, not the full TID-list.
                # this is the core memory optimization of dECLAT over plain ECLAT.

        if new_class:
        # if there are frequent extensions, recurse into the next level

            declat_search(
                prefix | itemset_i,
                # new prefix is the current prefix extended by itemset_i
                new_class,
                # the class we just built
                min_support_count,
                frequent_itemsets,
                candidates_generated
            )


# ──────────────────────────────────────────────────────────────────────────────
# STEP 6 — Main dECLAT driver
#           Wires everything together and returns the same dict format as
#           apriori.py so Teammate B's benchmark runner works on both.
# ──────────────────────────────────────────────────────────────────────────────

def sota_fim(transactions, min_sup_ratio):
    tracemalloc.start()
    start_time = time.time()
    # start the clock and the memory tracker right off the bat

    min_support_count = len(transactions) * min_sup_ratio
    # convert the ratio (e.g. 0.50) into a hard transaction count threshold

    frequent_itemsets = {}
    # master dictionary: {frozenset: support_count} — same structure as apriori.py

    candidates_generated = [0]
    # using a list so the integer is mutable inside the recursive function.
    # Python passes ints by value, but list elements are mutable by reference.

    # ── Phase 1: build the vertical database ──────────────────────────────────
    vertical_db = build_vertical_db(transactions)
    # transforms horizontal transactions into {item: {tid1, tid2, ...}} format.
    # this is a ONE-TIME scan of the database. after this point, we never touch
    # the original transactions array again. contrast with Apriori which rescans
    # the full database on every single level.

    # ── Phase 2: find frequent 1-itemsets ─────────────────────────────────────
    frequent_1_itemsets = {}
    # dict to hold only the single items that clear the support bar

    for itemset, tidlist in vertical_db.items():
    # check each item's TID-list length against the threshold

        if len(tidlist) >= min_support_count:
        # if enough transactions contain this item, it's frequent

            frequent_itemsets[itemset] = len(tidlist)
            # log it in the master dict

            frequent_1_itemsets[itemset] = tidlist
            # also keep the TID-list itself for the equivalence class search below

    # ── Phase 3: build equivalence classes and launch depth-first search ───────
    # Group frequent 1-itemsets into equivalence classes.
    # All items form one big class at the root (empty prefix).
    # Each pair within the class generates a 2-itemset candidate.

    class_members = list(frequent_1_itemsets.items())
    # list of (frozenset({item}), tidlist) tuples — the top-level class

    declat_search(
        frozenset(),
        # empty prefix — we're at the root of the search tree
        class_members,
        min_support_count,
        frequent_itemsets,
        candidates_generated
    )
    # this single recursive call handles ALL levels (2-itemsets, 3-itemsets, etc.)
    # Apriori needs a separate loop per level; dECLAT's recursion handles them all.

    # ── Phase 4: wrap up metrics ───────────────────────────────────────────────
    current, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    # grab the max memory used and shut the tracker down

    peak_memory_mb = peak_memory / (1024 * 1024)
    # bytes to megabytes

    runtime_sec = time.time() - start_time
    # total wall-clock time

    return {
        "algorithm": "SHFIM-dECLAT",
        # SHFIM (Tayebi et al., 2022) — vertical diffset engine as described in
        # the paper's core algorithmic contribution (DOI: 10.3390/data7010011)
        "min_sup": min_sup_ratio,
        "runtime_sec": runtime_sec,
        "memory_mb": peak_memory_mb,
        "frequent_itemsets": len(frequent_itemsets),
        "candidates_generated": candidates_generated[0],
        "all_frequent_itemsets": frequent_itemsets
        # passing the full dict back just like apriori.py does, for verification
    }


# ──────────────────────────────────────────────────────────────────────────────
# STEP 7 — Benchmark wrapper (mirrors benchmark_baseline from apriori.py)
#           Runs sota_fim() num_runs times and averages the metrics.
# ──────────────────────────────────────────────────────────────────────────────

def benchmark_sota(dataset_name, filepath, min_sup_ratio, num_runs=3):
    transactions = load_dataset(filepath)
    # load once — we don't want file I/O time polluting our algo timings

    total_runtime = 0
    total_memory = 0
    # running totals for averaging

    frequent_count = 0
    candidate_count = 0
    # these are deterministic — same data, same result every run — so we
    # only need to capture them from the first run

    for run in range(num_runs):
    # run the algorithm num_runs times for a reliable average

        results = sota_fim(transactions, min_sup_ratio)
        # call the main dECLAT function

        total_runtime += results['runtime_sec']
        total_memory += results['memory_mb']
        # accumulate for averaging

        if run == 0:
        # capture the counts on the first run only
            frequent_count = results['frequent_itemsets']
            candidate_count = results['candidates_generated']

    avg_runtime = total_runtime / num_runs
    avg_memory = total_memory / num_runs
    # compute the averages

    return {
        "algorithm": "SHFIM-dECLAT",
        "dataset": dataset_name,
        "memory_mb": round(avg_memory, 4),
        "frequent_itemsets": frequent_count,
        "candidates_generated": candidate_count
    }
    # returns the exact same dict format as benchmark_baseline() in apriori.py
    # so Teammate B's benchmarking code works on both without any changes


# ──────────────────────────────────────────────────────────────────────────────
# Sanity check — uncomment to test on chess.dat
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    filepath = r"/Users/saim/Desktop/chess.dat"
    print("Running SHFIM-dECLAT on chess.dat at 99% min-support...")
    results = sota_fim(load_dataset(filepath), 0.99)
    print("\nSHFIM-dECLAT Results:")
    print(f"Runtime (sec):          {results['runtime_sec']:.4f}")
    print(f"Peak Memory (MB):       {results['memory_mb']:.4f}")
    print(f"Frequent Itemsets:      {results['frequent_itemsets']}")
    print(f"Candidates Generated:   {results['candidates_generated']}")
