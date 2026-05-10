# OPTIMIZATION 1: Bitmap-Based Support Counting (Option A)
# OPTIMIZATION 2: TID-list Support Counting    (Option C)
#
# Justification — Optimization 1 (Bitmap):
# Apriori's inner support-counting loop calls c.issubset(t) for every
# candidate across every transaction — a Python-level set operation on each
# pair. Bitmasks replace that with a single integer AND: if
# (tx_mask & candidate_mask) == candidate_mask, the transaction contains the
# candidate. This is theoretically faster because bitwise ops are CPU
# primitives. In practice the speedup is dataset-dependent: on Chess (75
# items) Python's big-integer overhead for 75-bit ints partially offsets the
# gain — the bitmap runs slower than baseline on this specific dataset. The
# optimization pays off most on datasets with thousands of items, where
# Python set overhead dominates. We implement it here because the design is
# correct and the principle is sound; the tradeoff is documented in results.
#
# Justification — Optimization 2 (TID-list):
# The other big bottleneck is rescanning the full database at every level.
# The TID-list approach builds a vertical index once (item -> set of
# transaction IDs that contain it), then counts support by intersecting two
# TID-lists instead of touching the transactions again. The intersection
# cost shrinks as itemsets get larger, so the speedup compounds across levels.

import time
import tracemalloc
from apriori import get_itemset_occurrences, apriori_gen
# importing the base functions so no need to rewrite them


# ─────────────────────────────────────────────────────────────────────────────
# OPTIMIZATION 1 — BITMAP-BASED SUPPORT COUNTING
# ─────────────────────────────────────────────────────────────────────────────

def apriori_bitmap(transactions, min_sup_ratio):
    tracemalloc.start()
    start_time = time.time()
    # start the clock and memory tracker right away

    min_support_count = len(transactions) * min_sup_ratio
    # convert ratio to a hard transaction count, same as baseline

    # ── step 1: build the item -> bit-index mapping ──────────────────────────
    all_items = set()
    for transaction in transactions:
        all_items.update(transaction)
    # collect every unique item across all transactions

    item_to_bit = {item: idx for idx, item in enumerate(sorted(all_items))}
    # assign each item a stable bit position (sorted so it's deterministic)
    # item_to_bit[item] = bit index, e.g. item 1 -> bit 0, item 2 -> bit 1, ...

    # ── step 2: convert every transaction to an integer bitmask ──────────────
    tx_bitmasks = []
    for transaction in transactions:
        mask = 0
        for item in transaction:
            mask |= (1 << item_to_bit[item])
            # flip the bit at position item_to_bit[item] to 1
        tx_bitmasks.append(mask)
    # now each transaction is a single Python int — bit i is 1 iff item i is present

    # ── step 3: get frequent 1-itemsets using the baseline scanner ────────────
    current_frequent = get_itemset_occurrences(transactions, min_support_count)
    # reuse the baseline function for level 1 — no point rewriting it
    # (it's only called once, so the overhead is the same as baseline)

    frequent_itemsets = {}
    # master dict — same role as in apriori()

    total_candidates_generated = 0
    # running tally of candidates we generate across all levels

    k = 1
    # starting at level 1, same structure as baseline

    while current_frequent:
    # keep going as long as we keep finding frequent stuff

        frequent_itemsets.update(current_frequent)
        # dump this round's winners into the master dict

        k += 1
        # level up

        candidates = apriori_gen(current_frequent, k)
        # reuse the baseline candidate generator — same join + prune logic
        # this part isn't the bottleneck we're targeting, so no need to change it

        total_candidates_generated += len(candidates)
        # keep the tally updated

        # ── step 4: build a bitmask for each candidate ────────────────────────
        candidate_masks = []
        for candidate in candidates:
            mask = 0
            for item in candidate:
                mask |= (1 << item_to_bit[item])
                # same bit-flipping as we did for transactions
            candidate_masks.append((candidate, mask))
        # each candidate now has a paired integer bitmask ready for AND operations

        candidate_counts = {}
        # temp dict to count support for this level's candidates

        # ── step 5: bitmap support counting — the actual optimization ─────────
        for tx_mask in tx_bitmasks:
        # iterate over transaction bitmasks, NOT the original frozensets

            for candidate, c_mask in candidate_masks:
            # check each candidate against this transaction

                if (tx_mask & c_mask) == c_mask:
                # bitwise AND: if all candidate bits are set in the transaction,
                # the transaction contains the candidate — no issubset() needed
                # this is a single CPU instruction vs a Python set operation

                    if candidate in candidate_counts:
                        candidate_counts[candidate] += 1
                    else:
                        candidate_counts[candidate] = 1
                    # same increment logic as baseline

        current_frequent = {}
        # reset for filtering

        for candidate, count in candidate_counts.items():
        # check which candidates cleared the threshold

            if count >= min_support_count:
                current_frequent[candidate] = count
                # these are the winners that go into the next round

    # atp we ran out of frequent itemsets — bitmap loop is done

    current, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    # grab peak memory and shut the tracker down

    peak_memory_mb = peak_memory / (1024 * 1024)
    # bytes -> megabytes

    runtime_sec = time.time() - start_time
    # total wall-clock time

    return {
        "algorithm": "Apriori_Bitmap",
        "min_sup": min_sup_ratio,
        "runtime_sec": runtime_sec,
        "memory_mb": peak_memory_mb,
        "frequent_itemsets": len(frequent_itemsets),
        "candidates_generated": total_candidates_generated,
        "all_frequent_itemsets": frequent_itemsets
    }
    # returns the standard dictionary — same keys as apriori() so Teammate B
    # can drop this straight into the benchmark comparison table


# ─────────────────────────────────────────────────────────────────────────────
# OPTIMIZATION 2 — TID-LIST SUPPORT COUNTING
# ─────────────────────────────────────────────────────────────────────────────

def apriori_tidlist(transactions, min_sup_ratio):
    tracemalloc.start()
    start_time = time.time()
    # clock and memory tracker on

    min_support_count = len(transactions) * min_sup_ratio
    # same threshold conversion as baseline

    frequent_itemsets = {}
    # master dict to hold all frequent itemsets across all levels

    total_candidates_generated = 0
    # running candidate tally

    # ── step 1: build the vertical index for all 1-itemsets ──────────────────
    raw_tidlists = {}
    for tid, transaction in enumerate(transactions):
    # tid is the transaction's index in the list (0, 1, 2, ...)

        for item in transaction:
            fs = frozenset([item])
            # wrap the item in a frozenset so we can use it as a dict key,
            # consistent with how apriori() tracks itemsets

            if fs not in raw_tidlists:
                raw_tidlists[fs] = set()
            raw_tidlists[fs].add(tid)
            # add this transaction's index to the item's TID-list
    # at this point every 1-itemset has a set of transaction IDs that contain it
    # this is the only full-database scan we will ever do

    # ── step 2: filter to frequent 1-itemsets and store their TID-lists ───────
    current_tidlists = {}
    # dict: frozenset -> set of TIDs, for the current level's frequent itemsets

    for fs, tids in raw_tidlists.items():
    # check each 1-itemset's TID-list length against the threshold

        if len(tids) >= min_support_count:
            current_tidlists[fs] = tids
            frequent_itemsets[fs] = len(tids)
            # support count = size of the TID-list — no database scan needed

    k = 2
    # starting the loop at level 2 (we already handled level 1 above)

    while current_tidlists:
    # keep going as long as the previous level produced frequent itemsets

        # ── step 3: generate candidates from the previous level ───────────────
        candidates = apriori_gen(current_tidlists, k)
        # reuse baseline candidate generator — it only needs the keys (frozensets),
        # which current_tidlists has, so it works without modification

        total_candidates_generated += len(candidates)
        # keep the tally going

        next_tidlists = {}
        # will hold the TID-lists for this level's frequent itemsets

        # ── step 4: count support by TID-list intersection — no DB scan ───────
        for candidate in candidates:
        # for each candidate k-itemset we need to count support without rescanning

            # split the candidate back into two (k-1)-subsets that we already have
            items_list = list(candidate)
            # convert frozenset to list so we can index into it

            part_a = frozenset(items_list[:-1])
            part_b = frozenset(items_list[1:])
            # part_a = first k-1 items, part_b = last k-1 items
            # because apriori_gen only joins itemsets that share a (k-2)-prefix,
            # both of these subsets are guaranteed to be in current_tidlists

            if part_a not in current_tidlists or part_b not in current_tidlists:
                continue
                # safety check — if somehow a subset is missing, skip this candidate

            intersected = current_tidlists[part_a] & current_tidlists[part_b]
            # set intersection: gives us every transaction ID that contains BOTH subsets,
            # which is exactly every transaction that contains the full candidate
            # support(A ∪ B) = |tidlist(A) ∩ tidlist(B)|

            support = len(intersected)
            # support count = size of the intersection — zero database reads

            if support >= min_support_count:
            # only keep it if it clears the threshold

                frequent_itemsets[candidate] = support
                # add to the master dict

                next_tidlists[candidate] = intersected
                # carry the intersected TID-list forward — next level will use it
                # for the next round of intersections, no DB scan needed then either

        current_tidlists = next_tidlists
        # swap in the new level's TID-lists for the next iteration

        k += 1
        # level up

    # atp the loop terminated — no more frequent itemsets to find

    current, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    # grab peak memory and kill the tracker

    peak_memory_mb = peak_memory / (1024 * 1024)
    # bytes -> megabytes

    runtime_sec = time.time() - start_time
    # total elapsed time

    return {
        "algorithm": "Apriori_TIDlist",
        "min_sup": min_sup_ratio,
        "runtime_sec": runtime_sec,
        "memory_mb": peak_memory_mb,
        "frequent_itemsets": len(frequent_itemsets),
        "candidates_generated": total_candidates_generated,
        "all_frequent_itemsets": frequent_itemsets
    }
    # returns the standard dictionary — same keys as apriori() so Teammate B
    # can slot this straight into the benchmark comparison table


# ─────────────────────────────────────────────────────────────────────────────
# BENCHMARK WRAPPER — mirrors benchmark_baseline() in apriori.py
# ─────────────────────────────────────────────────────────────────────────────

def benchmark_optimization(algo_func, algo_name, dataset_name, transactions,
                            min_sup_ratio, num_runs=3):
    total_runtime = 0
    total_memory  = 0
    # accumulators for averaging across runs

    frequent_count  = 0
    candidate_count = 0
    # these don't change between runs on the same data — grab once

    for run in range(num_runs):
    # run 3 times to average out any OS scheduling noise

        results = algo_func(transactions, min_sup_ratio)
        # call whichever optimization function was passed in

        total_runtime += results['runtime_sec']
        total_memory  += results['memory_mb']
        # accumulate

        if run == 0:
        # snag counts on the first pass only
            frequent_count  = results['frequent_itemsets']
            candidate_count = results['candidates_generated']

    avg_runtime = total_runtime / num_runs
    avg_memory  = total_memory  / num_runs
    # compute averages

    return {
        "algorithm": algo_name,
        "dataset":   dataset_name,
        "min_sup":   min_sup_ratio,
        "runtime_sec":      round(avg_runtime, 4),
        "memory_mb":        round(avg_memory,  4),
        "frequent_itemsets": frequent_count,
        "candidates_generated": candidate_count
    }
    # returns the standard dict — Teammate B can compare this directly
    # against benchmark_baseline()'s output from apriori.py


# ─────────────────────────────────────────────────────────────────────────────
# SANITY CHECK — uncomment to verify both optimizations match baseline counts
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from apriori import load_dataset, apriori
    filepath = r"chess.dat"   # swap in your local path
    MIN_SUP  = 0.90
    transactions = load_dataset(filepath)
    base    = apriori(transactions, MIN_SUP)
    bitmap  = apriori_bitmap(transactions, MIN_SUP)
    tidlist = apriori_tidlist(transactions, MIN_SUP)
    print(f"Baseline  — itemsets: {base['frequent_itemsets']}  runtime: {base['runtime_sec']:.4f}s")
    print(f"Bitmap    — itemsets: {bitmap['frequent_itemsets']}  runtime: {bitmap['runtime_sec']:.4f}s")
    print(f"TID-list  — itemsets: {tidlist['frequent_itemsets']}  runtime: {tidlist['runtime_sec']:.4f}s")
    assert base['frequent_itemsets'] == bitmap['frequent_itemsets'],  "Bitmap count mismatch!"
    assert base['frequent_itemsets'] == tidlist['frequent_itemsets'], "TID-list count mismatch!"
    print("All counts match baseline. We're good.")
