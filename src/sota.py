# PLEASE USE COMMENTS AT ALMOST EACH STEP AND FORMAT THEM JUST AS I DID!!! ;(
import time
import tracemalloc

def build_vertical_db(transactions):
    vertical_db = {}
    # dictionary to hold item as key and a set of transaction ids as value

    for tid, transaction in enumerate(transactions):
    # loop through every transaction and keep track of the id

        for item in transaction:
        # check each item inside the transaction

            key = frozenset([item])
            if key not in vertical_db:
                vertical_db[key] = set()
            
            vertical_db[key].add(tid)
            # add the transaction id to the item's set

    return vertical_db
    # returns the database in vertical format

def intersect_tidlists(list1, list2):
    # write the logic here to intersect or diffset the lists
    pass

def sota_fim(transactions, min_sup_ratio):
    tracemalloc.start()
    start_time = time.time()
    
    # implement the chosen 2022+ algorithm here
    # PLEASE MUST USE THE 'vertical_db' AND 'intersect' LOGIC

    current, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_memory_mb = peak_memory / (1024 * 1024)
    runtime_sec = time.time() - start_time

    return {
        "algorithm": "Name_of_SOTA_Algorithm",
        "dataset": "dataset_name",
        "min_sup": min_sup_ratio,
        "runtime_sec": runtime_sec,
        "memory_mb": peak_memory_mb,
        "frequent_itemsets": 0, 
        # replace 0 with the actual count
        "candidates_generated": 0
        # replace 0 with tje actual count
    }
    # returns the exact same dictionary format as apriori so the benchmark works
