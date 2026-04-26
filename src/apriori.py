def load_dataset(filepath):
    transactions = []
    # an empty list to store transactions      

    with open (filepath, 'r') as file:
    # opens the file in read mode
     
        for line in file:
        # iterates through the file line by line
       
            items = frozenset(map(int, line.strip().split()))
            # strip() deals with the hidden newline characters at the end of the line.
            # split() chops the line into individual string characters based on space.
            # map(int, ) turns those string characters into integers.
            # frozenset(); we are gonna use these itemsets later on as dictionary keys
            # to keep track of their count. if we use regular changeable list, pythons
            # gonna throw an absolute fit, so we freeze the list.

            transactions.append(items)
            # chucks the frozenset into our transaction list

    return transactions

# # Just a sanity check:
# if __name__ == "__main__":

#     dataset = load_dataset(r"c:\Users\Hamza Bukhari\Desktop\DAA\chess.dat\chess.dat")

#     print("\nTotal Transactions: ")
#     print(len(dataset))

#     print("\nPrinting first transaction: ")
#     print(dataset[0])


def get_itemset_occurrences(transactions, min_support_count):
    item_counts = {}
    # dictionary to hold value counts of each item

    for transaction in transactions:
    # pick a transaction from the transactions list

        for item in transaction:
        # iterate through the items in that transaction

            itemset = frozenset([item])
            # take each item as a list, freeze it, store it in
            # itemset, so int becomes frozenset({int})

            if itemset in item_counts:
            # if it already exists in dictionary, increment
                item_counts[itemset] += 1

            else:
            # otherwise start the count with 1
                item_counts[itemset] = 1
        
    # atp we have counted every item up

    itemset_occurrences = {}
    # dictionary to store only the itemsets that meet min_support_count

    for itemset, count in item_counts.items():
    # check each counted itemset against the minimum support threshold

        if count >= min_support_count:
        # keep itemsets that are frequent enough

            itemset_occurrences[itemset] = count

    return itemset_occurrences

# # Just a sanity check:
# if __name__ == "__main__":
#     dataset = load_dataset(r"c:\Users\Hamza Bukhari\Desktop\DAA\chess.dat\chess.dat")
#     frequent = get_itemset_occurrences(dataset, 100)
#     print(f"Found {len(frequent)} frequent itemsets!")


import time
import tracemalloc
# importing these bad boys to track:
# how long it takes, and 
# how much memory it hogs


def apriori_gen(prev_frequent, k):
    candidates = []
    # empty list to store our newly generated candidate itemsets

    prev_items = list(prev_frequent.keys())
    # grab just the itemsets (the keys) from our previous frequent dict, 
    # cast to list so we can index

    for i in range(len(prev_items)):
    # loop through every itemset

        for j in range(i + 1, len(prev_items)):
        # loop through the remaining itemsets to form pairs

            set1 = list(prev_items[i])
            set2 = list(prev_items[j])
            # convert frozensets back to lists so we can sort and compare them

            set1.sort()
            set2.sort()
            # sorting makes sure we only join sets that are identical except for the very last item

            if set1[:k-2] == set2[:k-2]:
            # check if the core prefix (everything but the last item) matches up perfectly

                candidate = prev_items[i] | prev_items[j]
                # union the two sets together to make a new candidate of size k

                # we have a candidate now
                # for the pruning phase:

                is_valid = True
                # assume innocent until proven guilty

                for item in candidate:
                # check every possible subset of size k-1

                    subset = candidate - frozenset([item])
                    # drop one item to create a subset

                    if subset not in prev_frequent:
                    # if this subset wasn't frequent in the last round, this candidate is trash

                        is_valid = False
                        break
                        # no need to check the rest, just bail

                if is_valid:
                # if it survived the pruning gauntlet

                    candidates.append(candidate)
                    # chuck it into our candidate list

    return candidates
    # returns the fully vetted list of size k candidates


def apriori(transactions, min_sup_ratio):
    tracemalloc.start()
    start_time = time.time()
    # start the clock and the memory tracker right off the bat

    min_support_count = len(transactions) * min_sup_ratio
    # convert the percentage (ratio) into a hard number of transactions needed

    frequent_itemsets = {}
    # master dictionary to hold all frequent itemsets of all sizes

    total_candidates_generated = 0
    # keeping a running tally of how many candidates we cook up

    k = 1
    # starting at level 1 (single items)

    current_frequent = get_itemset_occurrences(transactions, min_support_count)
    # kick things off by getting the frequent 1-itemsets

    while current_frequent:
    # keep looping as long as we keep finding frequent stuff

        frequent_itemsets.update(current_frequent)
        # toss the winners from this round into the master dictionary

        k += 1
        # level up to the next size

        candidates = apriori_gen(current_frequent, k)
        # generate new candidates of size k from our previous winners

        total_candidates_generated += len(candidates)
        # add the number of new candidates to our running tally

        candidate_counts = {}
        # temporary dictionary to count up occurrences for these new candidates

        for transaction in transactions:
        # scan the whole database again (apriori's biggest bottleneck id say)

            for candidate in candidates:
            # check each candidate against this specific transaction

                if candidate.issubset(transaction):
                # if the transaction contains the whole candidate set

                    if candidate in candidate_counts:
                        candidate_counts[candidate] += 1
                    else:
                        candidate_counts[candidate] = 1
                    # same as before, increment or start at 1

        current_frequent = {}
        # reset for the filtering phase

        for candidate, count in candidate_counts.items():
        # check which candidates survived the cut

            if count >= min_support_count:
                current_frequent[candidate] = count
                # add them to our current winners list to be used in the next loop

    # atp the loop is dead because we couldn't find any more frequent itemsets

    current, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    # grab the max memory used and shut the tracker down

    peak_memory_mb = peak_memory / (1024 * 1024)
    # convert bytes to megabytes so it's actually readable

    runtime_sec = time.time() - start_time
    # calculate total time elapsed

    return {
        "algorithm": "Apriori",
        "min_sup": min_sup_ratio,
        "runtime_sec": runtime_sec,
        "memory_mb": peak_memory_mb,
        "frequent_itemsets": len(frequent_itemsets),
        "candidates_generated": total_candidates_generated,
        "all_frequent_itemsets": frequent_itemsets
        # passing back the actual itemsets too just in case we need to verify them later
    }


# # Just a sanity check:
# if __name__ == "__main__":
#     dataset = load_dataset(r"c:\Users\Hamza Bukhari\Desktop\DAA\chess.dat\chess.dat")
    
#     results = apriori(dataset, 0.50)
#     # testing with a 50% minimum support ratio (0.50)
    
#     print("\nApriori Results: ")
#     print("\nRuntime in seconds: ")
#     print(f"{results['runtime_sec']:.4f}")
#     print("\nPeak Memory in MBs: ")
#     print(f"{results['memory_mb']:.4f}")
#     print("\nCandidates Generated: ")
#     print(results['candidates_generated'])
#     print("\nTotal Frequent Itemsets: ")
#     print(results['frequent_itemsets'])

def benchmark_baseline(dataset_name, filepath, min_sup_ratio, num_runs=3):
    transactions = load_dataset(filepath)
    # loads data once so we aint factoring file i/o time into our algo stats

    total_runtime = 0
    total_memory = 0
    # variables to keep a running tally of our performance metrics

    frequent_count = 0
    candidate_count = 0
    # these won't change between runs on the exact same data, so we just need to grab them once

    for run in range(num_runs):
    # loop 3 times (or whatever num_runs is) to get a fair average

        results = apriori(transactions, min_sup_ratio)
        # call the apriori function

        total_runtime += results['runtime_sec']
        total_memory += results['memory_mb']
        # add the stats from this specific run to our tallies

        if run == 0:
        # just snag the raw counts on the very first loop
            frequent_count = results['frequent_itemsets']
            candidate_count = results['candidates_generated']

    avg_runtime = total_runtime / num_runs
    avg_memory = total_memory / num_runs
    # do the math to get the averages

    return {
        "algorithm": "Apriori",
        "dataset": dataset_name,
        "min_sup": min_sup_ratio,
        "runtime_sec": round(avg_runtime, 4),
        "memory_mb": round(avg_memory, 4),
        "frequent_itemsets": frequent_count,
        "candidates_generated": candidate_count
    }
    # atp we are returning the perfectly formatted dictionary that Teammate B needs to build their tables


# # Just a sanity check:
# if __name__ == "__main__":
#     # testing the wrapper with the 95% threshold since we know it's fast
#     metrics = benchmark_baseline("chess", r"c:\Users\Hamza Bukhari\Desktop\DAA\chess.dat\chess.dat", 0.95)
    
#     print("\nBaseline Metrics Wrapper Output: ")
#     for key, value in metrics.items():
#         print(f"{key}: {value}")


# # Cross-verifying against mlxtend:

# import pandas as pd
# from mlxtend.preprocessing import TransactionEncoder
# from mlxtend.frequent_patterns import apriori as mlxtend_apriori

# def run_sanity_check(filepath, min_sup_ratio=0.90):
#     print("Loading data and setting up the lie detector (mlxtend)...")
#     transactions = load_dataset(filepath)
    
#     te = TransactionEncoder()
#     te_ary = te.fit(transactions).transform(transactions)
#     df = pd.DataFrame(te_ary, columns=te.columns_)
    
#     print(f"Running mlxtend Apriori at {min_sup_ratio * 100}% support. Hold tight...")
#     verified_results = mlxtend_apriori(df, min_support=min_sup_ratio, use_colnames=True, low_memory=True)
    
#     print(f"\n--- The Moment of Truth at {min_sup_ratio * 100}% ---")
#     print(f"mlxtend official count: {len(verified_results)} frequent itemsets")
    
#     print("Running your homemade Apriori...")
#     your_results = apriori(transactions, min_sup_ratio)
#     print(f"Your official count: {your_results['frequent_itemsets']} frequent itemsets")
    
#     if len(verified_results) == your_results['frequent_itemsets']:
#         print("MATCH! Your code is bulletproof. Send it to the group.")
#     else:
#         print("Uh oh, the counts don't match. Something is sus.")

# if __name__ == "__main__":
#     file_path = r"c:\Users\Hamza Bukhari\Desktop\DAA\chess.dat\chess.dat"
#     run_sanity_check(file_path, 0.90)
