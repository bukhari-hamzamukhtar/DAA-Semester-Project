import time
import tracemalloc
from apriori import get_itemset_occurrences, apriori_gen
# importing the base functions so no need to rewrite them

def apriori_optimization_1(transactions, min_sup_ratio):
    tracemalloc.start()
    start_time = time.time()
    
    # implement first optimization here
    # example: bitmap counting or partitioning

    current, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_memory_mb = peak_memory / (1024 * 1024)
    runtime_sec = time.time() - start_time

    return {
        "algorithm": "Apriori_Opt_1",
        "dataset": "dataset_name",
        "min_sup": min_sup_ratio,
        "runtime_sec": runtime_sec,
        "memory_mb": peak_memory_mb,
        "frequent_itemsets": 0,
        "candidates_generated": 0
    }
    # returns the standard dictionary

def apriori_optimization_2(transactions, min_sup_ratio):
    tracemalloc.start()
    start_time = time.time()
    
    # implement second optimization here
    # example: multithreading or tid-list pruning

    current, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_memory_mb = peak_memory / (1024 * 1024)
    runtime_sec = time.time() - start_time

    return {
        "algorithm": "Apriori_Opt_2",
        "dataset": "dataset_name",
        "min_sup": min_sup_ratio,
        "runtime_sec": runtime_sec,
        "memory_mb": peak_memory_mb,
        "frequent_itemsets": 0,
        "candidates_generated": 0
    }
    # returns the standard dictionary
