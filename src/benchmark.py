# PLEASE USE COMMENTS AT ALMOST EACH STEP AND FORMAT THEM JUST AS I DID!!! ;( 
import csv
import os
import time
# importing basic libraries for saving files and tracking time

from apriori import load_dataset, benchmark_baseline
# importing baseline functions

# from sota import sota_fim
# from optimizations import apriori_optimization_1, apriori_optimization_2
# imports go here once you finish you files

def run_benchmarks():
    datasets = {
        "chess": r"data\chess.dat",
        "connect": r"data\connect.dat", 
        "accidents": r"data\accidents.dat"
    }
    # dictionary holding the paths to the three datasets

    thresholds = [0.50, 0.40, 0.30, 0.20]
    # the four minimum support thresholds that need to test

    results_dir = "results"
    
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    # create the results folder if it doesn't exist already

    csv_file = os.path.join(results_dir, "benchmark_results.csv")
    headers = ["algorithm", "dataset", "min_sup", "runtime_sec", "memory_mb", "frequent_itemsets", "candidates_generated"]
    # setting up the file path and the exact columns required for the charts

    print("Starting the benchmark orchestrator...")

    with open(csv_file, mode='w', newline='') as file:
    # open the csv file in write mode

        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        # set up the csv writer and write the column names at the top

        for dataset_name, filepath in datasets.items():
        # loop through each of the three datasets

            print(f"\nLoading {dataset_name}...")

            if not os.path.exists(filepath):
                print(f"File {filepath} not found. Skipping.")
                continue
            # skip to the next dataset if haven't downloaded yet

            for min_sup in thresholds:
            # loop through all four thresholds for this specific dataset

                print(f"Testing at {min_sup * 100}% support...")

                try:
                    baseline_stats = benchmark_baseline(dataset_name, filepath, min_sup, num_runs=3)
                    writer.writerow(baseline_stats)
                    print("Apriori Baseline finished.")
                except Exception as e:
                    print(f"Baseline crashed: {e}")
                # run baseline, write the results to csv, and catch any errors

                # try:
                #     transactions = load_dataset(filepath)
                #     sota_stats = sota_fim(transactions, min_sup) 
                #     sota_stats['dataset'] = dataset_name
                #     writer.writerow(sota_stats)
                #     print("SOTA finished.")
                # except Exception as e:
                #     print(f"SOTA crashed: {e}")
                # teammate A's block. they need to uncomment this when ready... to whom it may concern lol

                # try:
                #     transactions = load_dataset(filepath)
                #     opt1_stats = apriori_optimization_1(transactions, min_sup)
                #     opt1_stats['dataset'] = dataset_name
                #     writer.writerow(opt1_stats)
                #     print("Optimization 1 finished.")
                # except Exception as e:
                #     print(f"Optimization 1 crashed: {e}")
                # teammate B's first optimization block.. again, to whom it may concern :)

                # try:
                #     transactions = load_dataset(filepath)
                #     opt2_stats = apriori_optimization_2(transactions, min_sup)
                #     opt2_stats['dataset'] = dataset_name
                #     writer.writerow(opt2_stats)
                #     print("Optimization 2 finished.")
                # except Exception as e:
                #     print(f"Optimization 2 crashed: {e}")
                # teammate B's second optimization block... ye bhi!

    print(f"\nAll done! Results saved to {csv_file}.")

if __name__ == "__main__":
    run_benchmarks()
