# DAA-Semester-Project

# Apriori Baseline Module

Here is the core logic for our baseline Apriori. You don't have to mess with the internal functions. Just import the benchmarking wrapper to get what you need.

## Dataset Setup

Just a heads-up on the data files. The `chess.dat` and `connect.dat` files are already there in the `data/` folder. 

However, `accidents.dat` was way too huge to upload directly. So, in the `data/` folder, I put an `accidents.txt` file instead. You just need to open that text file, grab the Google Drive link inside, download the actual `.dat` file, and drop it into the `data/` folder. Make sure you do this before running your benchmarks.

## How to Call the Code

To run the baseline and get the averaged stats, just drop this into your script:

```python
from src.apriori import benchmark_baseline

# This runs the algo 3 times and spits out the averages
metrics = benchmark_baseline("chess", "data/chess.dat", 0.50)
print(metrics)
```

## Expected Output Format
Your SOTA algorithm needs to return a dictionary with these exact keys so charts, that'll be used in future, don't break.

```python
{
  'algorithm': 'Apriori', 
  'dataset': 'chess', 
  'min_sup': 0.5, 
  'runtime_sec': 14.2341, 
  'memory_mb': 45.12, 
  'frequent_itemsets': 1823, 
  'candidates_generated': 9401
}
```
