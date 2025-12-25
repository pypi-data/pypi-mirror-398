# Quick Grid Search

This directory contains tools for performing grid searches to find optimal force scale vectors for different system configurations.

## Overview

The grid search explores:
- **Systems**: Different physical systems (cart_pole, cart_pole_double, double_pendulum_pm)
- **Damping coefficients**: Various damping configurations
- **Force patterns**: Which coordinates receive external forces
- **Force scales**: Different magnitudes of force application

## Files

- `generate_gridsearch.py`: Generates experiment configurations and execution script
- `analyze_results.py`: Analyzes results and creates visualizations
- `run_gridsearch.sh`: Auto-generated script to run all experiments
- `configs/`: Directory containing individual experiment configurations (auto-generated)
- `analysis/`: Directory containing analysis results and plots (auto-generated)

## Usage

### 1. Generate Grid Search Configurations

```bash
python example/quick_gridsearch/generate_gridsearch.py
```

This will:
- Create experiment configurations in `example/quick_gridsearch/configs/`
- Generate `run_gridsearch.sh` script
- Print summary of experiments to be run

### 2. Run Grid Search

**Sequential execution (one at a time):**
```bash
python example/quick_gridsearch/run_gridsearch.py
```

**Parallel execution (multiple experiments at once):**
```bash
# Run with 4 parallel workers
python example/quick_gridsearch/run_gridsearch.py --parallel 4

# Use all CPU cores
python example/quick_gridsearch/run_gridsearch.py --parallel 8
```

No external dependencies required - pure Python!

### 3. Analyze Results

After experiments complete:

```bash
python example/quick_gridsearch/analyze_results.py
```

This will generate:
- **Individual plots**: Error vs force scale for each configuration
- **Histogram**: Distribution of optimal force scales by system and pattern
- **Heatmaps**: Optimal force scales by damping and force pattern
- **Summary report**: Text file with detailed results
- **JSON output**: Machine-readable optimal configurations

## Output Files

### Analysis Directory (`example/quick_gridsearch/analysis/`)

- `error_vs_scale_*.png`: Individual plots showing error vs force scale magnitude
- `optimal_scales_histogram.png`: Histogram of optimal force scales grouped by system
- `optimal_scales_heatmap_*.png`: Heatmaps for each system showing optimal scales
- `summary_report.txt`: Text summary of all results
- `optimal_configurations.json`: JSON file with optimal configurations for each setup

### Test Directory (`test/`)

- `results_*.json`: Individual experiment results
- `trajectory_comparison_*.png`: Trajectory comparison plots

## Customization

Edit `generate_gridsearch.py` to customize:

- `SYSTEMS`: List of systems to test
- `DAMPING_CONFIGS`: Damping coefficient combinations
- `FORCE_PATTERNS_*`: Which coordinates receive forces
- `FORCE_SCALES`: Magnitude values to test
- `FIXED_PARAMS`: Common parameters for all experiments

## Example Results Interpretation

After running the analysis, look for:

1. **Optimal force scales**: What force magnitude works best for each configuration?
2. **Pattern effects**: Do certain force patterns (e.g., all coordinates vs single coordinate) require different scales?
3. **Damping effects**: How does damping affect the optimal force scale?
4. **Model validity**: Which configurations produce valid models?

## Performance Tips

- Adjust parallel jobs in `run_gridsearch.sh` (default: `-j 4`)
- Run experiments on a powerful machine or cluster
- Monitor disk space (each experiment produces ~2-3 MB of data)
- Expected total experiments: ~100-300 depending on configuration

## Troubleshooting

**Issue**: Experiments are slow
- Solution: Use `--parallel N` to run multiple experiments simultaneously
- Or reduce `validation_time` in the config

**Issue**: Out of memory with parallel execution
- Solution: Reduce the `--parallel` parameter

**Issue**: No results found when analyzing
- Solution: Ensure experiments have completed and results are in `test/` directory

**Issue**: Import errors when running experiments
- Solution: Make sure you're in the project root directory and have activated the environment
