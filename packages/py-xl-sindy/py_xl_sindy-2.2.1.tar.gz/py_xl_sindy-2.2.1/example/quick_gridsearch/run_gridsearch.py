"""
Pure Python script to run grid search experiments.

No external dependencies on jq or parallel - uses Python's subprocess and multiprocessing.
"""

import json
import os
import glob
import subprocess
import sys
from multiprocessing import Pool, cpu_count
from typing import Dict, Any
import argparse


def load_config(config_file: str) -> Dict[str, Any]:
    """Load a configuration file."""
    with open(config_file, 'r') as f:
        return json.load(f)


def config_to_args(config: Dict[str, Any]) -> list:
    """Convert config dictionary to command line arguments."""
    args = []
    
    # Map config keys to command line arguments
    arg_mapping = {
        "random_seed": "--random-seed",
        "batch_number": "--batch-number",
        "max_time": "--max-time",
        "forces_period": "--forces-period",
        "forces_period_shift": "--forces-period-shift",
        "data_ratio": "--data-ratio",
        "validation_time": "--validation-time",
        "noise_level": "--noise-level",
        "experiment_system": "--experiment-system",
        "catalog_lenght": "--catalog-lenght",
        "simulation_mode": "--simulation-mode",
    }
    
    # List arguments (need to be space-separated)
    list_args = {
        "initial_position": "--initial-position",
        "initial_condition_randomness": "--initial-condition-randomness",
        "forces_scale_vector": "--forces-scale-vector",
        "damping_coefficients": "--damping-coefficients",
    }
    
    # Add simple arguments
    for key, flag in arg_mapping.items():
        if key in config:
            args.extend([flag, str(config[key])])
    
    # Add list arguments
    for key, flag in list_args.items():
        if key in config:
            values = config[key]
            args.append(flag)
            args.extend([str(v) for v in values])
    
    return args


def run_single_experiment(config_file: str) -> tuple:
    """Run a single experiment and return results."""
    try:
        config = load_config(config_file)
        exp_uid = config.get("exp_uid", os.path.basename(config_file))
        
        print(f"Starting experiment: {exp_uid}")
        
        # Build command
        cmd = ["python", "example/minimal_example_modular.py"]
        cmd.extend(config_to_args(config))
        
        # Run experiment
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        if result.returncode == 0:
            print(f"✓ Completed: {exp_uid}")
            return (config_file, True, None)
        else:
            print(f"✗ Failed: {exp_uid}")
            print(f"  Error: {result.stderr[:1000]}")
            return (config_file, False, result.stderr)
            
    except Exception as e:
        print(f"✗ Exception in {config_file}: {str(e)}")
        return (config_file, False, str(e))


def run_experiments_sequential(config_files: list) -> list:
    """Run experiments sequentially."""
    results = []
    total = len(config_files)
    
    for i, config_file in enumerate(config_files, 1):
        print(f"\n[{i}/{total}] Running {os.path.basename(config_file)}")
        result = run_single_experiment(config_file)
        results.append(result)
    
    return results


def run_experiments_parallel(config_files: list, num_workers: int) -> list:
    """Run experiments in parallel using multiprocessing."""
    total = len(config_files)
    print(f"Running {total} experiments with {num_workers} parallel workers...")
    
    with Pool(num_workers) as pool:
        results = pool.map(run_single_experiment, config_files)
    
    return results


def print_summary(results: list):
    """Print summary of results."""
    successful = sum(1 for _, success, _ in results if success)
    failed = len(results) - successful
    
    print("\n" + "=" * 80)
    print("GRID SEARCH SUMMARY")
    print("=" * 80)
    print(f"Total experiments: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    
    if failed > 0:
        print("\nFailed experiments:")
        for config_file, success, error in results:
            if not success:
                print(f"  - {os.path.basename(config_file)}")
                if error:
                    print(f"    {error[:100]}")
    
    print("\nNext steps:")
    print("  python example/quick_gridsearch/analyze_results.py")


def main():
    parser = argparse.ArgumentParser(
        description="Run grid search experiments without jq/parallel dependencies"
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=1,
        help="Number of parallel workers (default: 1 for sequential)"
    )
    parser.add_argument(
        "--configs-dir",
        type=str,
        default="example/quick_gridsearch/configs",
        help="Directory containing config files"
    )
    
    args = parser.parse_args()
    
    # Create test directory
    os.makedirs("test", exist_ok=True)
    
    # Find all config files
    config_pattern = os.path.join(args.configs_dir, "config_*.json")
    config_files = sorted(glob.glob(config_pattern))
    
    if not config_files:
        print(f"No config files found in {args.configs_dir}")
        print("Run: python example/quick_gridsearch/generate_gridsearch.py first")
        sys.exit(1)
    
    print(f"Found {len(config_files)} experiments to run")
    
    # Run experiments
    if args.parallel > 1:
        # Use specified number of workers
        results = run_experiments_parallel(config_files, args.parallel)
    else:
        # Sequential execution
        results = run_experiments_sequential(config_files)
    
    # Print summary
    print_summary(results)


if __name__ == "__main__":
    main()
