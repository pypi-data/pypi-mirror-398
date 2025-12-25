"""
Analyze grid search results and generate visualizations.

This script:
1. Loads all experimental results from the test directory
2. Groups results by system, damping, and force pattern
3. Finds optimal force scales for each configuration
4. Generates histograms and summary plots
"""

import json
import os
import glob
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from typing import Dict, List, Any, Tuple
import seaborn as sns

# Set plotting style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)


def load_all_results(results_dir: str = "test") -> List[Dict[str, Any]]:
    """Load all result JSON files from the test directory."""
    result_files = glob.glob(os.path.join(results_dir, "results_*.json"))
    
    results = []
    for result_file in result_files:
        try:
            with open(result_file, 'r') as f:
                result = json.load(f)
                results.append(result)
        except Exception as e:
            print(f"Error loading {result_file}: {e}")
    
    print(f"Loaded {len(results)} result files")
    return results


def extract_force_pattern_key(forces_scale_vector: List[float]) -> str:
    """Extract force pattern (which coordinates are active) as a string key."""
    pattern = tuple(1 if f != 0 else 0 for f in forces_scale_vector)
    return str(pattern)


def get_force_scale_magnitude(forces_scale_vector: List[float]) -> float:
    """Get the magnitude of the force scale vector (assuming uniform scaling of pattern)."""
    non_zero = [f for f in forces_scale_vector if f != 0]
    if not non_zero:
        return 0.0
    return np.mean(np.abs(non_zero))


def group_results(results: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group results by (system, damping_coefficients, force_pattern).
    
    Returns dict with keys: (system, damping_tuple, force_pattern_key)
    """
    grouped = defaultdict(list)
    
    for result in results:
        system = result.get("experiment_system", "unknown")
        damping = tuple(result.get("damping_coefficients", []))
        force_pattern = extract_force_pattern_key(result.get("forces_scale_vector", []))
        
        key = (system, damping, force_pattern)
        grouped[key].append(result)
    
    print(f"Grouped results into {len(grouped)} unique configurations")
    return dict(grouped)


def find_optimal_force_scale(group_results: List[Dict[str, Any]]) -> Tuple[float, float, Dict[str, Any]]:
    """
    Find the optimal force scale for a group of experiments.
    
    Returns: (optimal_scale, minimum_error, best_config)
    """
    valid_results = [r for r in group_results if r.get("valid_model", False)]
    
    if not valid_results:
        return (float('nan'), float('inf'), {})
    
    # Find result with minimum error
    best_result = min(valid_results, key=lambda r: r.get("error", float('inf')))
    
    optimal_scale = get_force_scale_magnitude(best_result.get("forces_scale_vector", []))
    min_error = best_result.get("error", float('inf'))
    
    return (optimal_scale, min_error, best_result)


def create_force_pattern_label(pattern_key: str, num_coords: int) -> str:
    """Create human-readable label for force pattern."""
    pattern = eval(pattern_key)  # Convert string back to tuple
    
    if num_coords == 2:
        coord_names = ["q1", "q2"]
    elif num_coords == 4:
        coord_names = ["x", "θ1", "θ2", "θ3"][:num_coords]
    else:
        coord_names = [f"q{i+1}" for i in range(num_coords)]
    
    active = [coord_names[i] for i, p in enumerate(pattern) if p == 1]
    
    if not active:
        return "No forces"
    elif len(active) == len(coord_names):
        return "All coords"
    else:
        return ", ".join(active)


def plot_error_vs_force_scale(
    group_results: List[Dict[str, Any]], 
    group_key: Tuple[str, Tuple, str],
    output_dir: str
):
    """Plot error vs force scale magnitude for a specific configuration."""
    system, damping, force_pattern = group_key
    
    # Extract data
    force_scales = []
    errors = []
    valid_models = []
    
    for result in group_results:
        scale = get_force_scale_magnitude(result.get("forces_scale_vector", []))
        error = result.get("error", float('inf'))
        valid = result.get("valid_model", False)
        
        force_scales.append(scale)
        errors.append(error if valid and not np.isinf(error) else np.nan)
        valid_models.append(valid)
    
    # Sort by force scale
    sorted_indices = np.argsort(force_scales)
    force_scales = np.array(force_scales)[sorted_indices]
    errors = np.array(errors)[sorted_indices]
    valid_models = np.array(valid_models)[sorted_indices]
    
    # Create plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot valid results
    valid_mask = ~np.isnan(errors)
    if valid_mask.any():
        ax.plot(force_scales[valid_mask], errors[valid_mask], 'o-', 
                markersize=8, linewidth=2, label='Valid models')
        
        # Mark optimal point
        if valid_mask.any():
            opt_idx = np.nanargmin(errors)
            ax.plot(force_scales[opt_idx], errors[opt_idx], 'r*', 
                    markersize=20, label=f'Optimal (scale={force_scales[opt_idx]:.2f})')
    
    # Mark invalid models
    invalid_mask = ~valid_models
    if invalid_mask.any():
        ax.plot(force_scales[invalid_mask], 
                np.ones(invalid_mask.sum()) * np.nanmax(errors) * 1.2, 
                'x', markersize=10, color='red', label='Invalid models')
    
    ax.set_xlabel('Force Scale Magnitude', fontsize=12)
    ax.set_ylabel('RMSE Error', fontsize=12)
    ax.set_title(f'System: {system}\nDamping: {damping}\nPattern: {create_force_pattern_label(force_pattern, len(damping))}',
                 fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Save plot
    safe_key = f"{system}_{'_'.join(map(str, damping))}_{force_pattern.replace(' ', '')}"
    filename = os.path.join(output_dir, f"error_vs_scale_{safe_key}.png")
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close()


def plot_optimal_scales_histogram(
    optimal_results: Dict[Tuple, Tuple[float, float, Dict]],
    output_dir: str
):
    """Create histograms of optimal force scales grouped by system and force pattern."""
    
    # Group by system
    systems_data = defaultdict(lambda: defaultdict(list))
    
    for (system, damping, force_pattern), (opt_scale, min_error, config) in optimal_results.items():
        if not np.isnan(opt_scale) and not np.isinf(min_error):
            pattern_label = create_force_pattern_label(force_pattern, len(damping))
            systems_data[system][pattern_label].append(opt_scale)
    
    # Create subplots for each system
    num_systems = len(systems_data)
    fig, axes = plt.subplots(num_systems, 1, figsize=(12, 6 * num_systems))
    
    if num_systems == 1:
        axes = [axes]
    
    for idx, (system, patterns_data) in enumerate(sorted(systems_data.items())):
        ax = axes[idx]
        
        # Prepare data for grouped histogram
        pattern_labels = sorted(patterns_data.keys())
        data_by_pattern = [patterns_data[label] for label in pattern_labels]
        
        # Create histogram
        ax.hist(data_by_pattern, bins=15, alpha=0.7, label=pattern_labels, edgecolor='black')
        
        ax.set_xlabel('Optimal Force Scale', fontsize=12)
        ax.set_ylabel('Count', fontsize=12)
        ax.set_title(f'Optimal Force Scales - System: {system}', fontsize=14)
        ax.legend(title='Force Pattern')
        ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    filename = os.path.join(output_dir, "optimal_scales_histogram.png")
    plt.savefig(filename, dpi=150)
    plt.close()
    print(f"Saved histogram to {filename}")


def plot_optimal_scales_heatmap(
    optimal_results: Dict[Tuple, Tuple[float, float, Dict]],
    output_dir: str
):
    """Create heatmap of optimal force scales by system and damping."""
    
    for system in ["cart_pole", "cart_pole_double", "double_pendulum_pm"]:
        system_results = {k: v for k, v in optimal_results.items() if k[0] == system}
        
        if not system_results:
            continue
        
        # Extract unique dampings and patterns
        dampings = sorted(set(k[1] for k in system_results.keys()))
        patterns = sorted(set(k[2] for k in system_results.keys()))
        
        # Create matrix for heatmap
        opt_scales = np.full((len(patterns), len(dampings)), np.nan)
        
        for i, pattern in enumerate(patterns):
            for j, damping in enumerate(dampings):
                key = (system, damping, pattern)
                if key in system_results:
                    opt_scale, _, _ = system_results[key]
                    opt_scales[i, j] = opt_scale
        
        # Create heatmap
        fig, ax = plt.subplots(figsize=(12, len(patterns) * 0.8 + 2))
        
        im = ax.imshow(opt_scales, cmap='viridis', aspect='auto')
        
        # Set ticks and labels
        ax.set_xticks(np.arange(len(dampings)))
        ax.set_yticks(np.arange(len(patterns)))
        ax.set_xticklabels([str(d) for d in dampings], rotation=45, ha='right')
        ax.set_yticklabels([create_force_pattern_label(p, len(dampings[0])) for p in patterns])
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Optimal Force Scale', rotation=270, labelpad=20)
        
        # Add values to cells
        for i in range(len(patterns)):
            for j in range(len(dampings)):
                if not np.isnan(opt_scales[i, j]):
                    text = ax.text(j, i, f'{opt_scales[i, j]:.2f}',
                                   ha="center", va="center", color="white", fontweight='bold')
        
        ax.set_xlabel('Damping Coefficients', fontsize=12)
        ax.set_ylabel('Force Pattern', fontsize=12)
        ax.set_title(f'Optimal Force Scales - {system}', fontsize=14)
        
        plt.tight_layout()
        filename = os.path.join(output_dir, f"optimal_scales_heatmap_{system}.png")
        plt.savefig(filename, dpi=150)
        plt.close()
        print(f"Saved heatmap to {filename}")


def generate_summary_report(
    optimal_results: Dict[Tuple, Tuple[float, float, Dict]],
    output_dir: str
):
    """Generate a text summary report of the grid search results."""
    
    report_lines = [
        "=" * 80,
        "GRID SEARCH RESULTS SUMMARY",
        "=" * 80,
        "",
    ]
    
    # Group by system
    by_system = defaultdict(list)
    for key, (opt_scale, min_error, config) in optimal_results.items():
        system, damping, force_pattern = key
        by_system[system].append((key, opt_scale, min_error, config))
    
    for system in sorted(by_system.keys()):
        report_lines.append(f"\n{'=' * 80}")
        report_lines.append(f"SYSTEM: {system}")
        report_lines.append('=' * 80)
        
        results = by_system[system]
        results.sort(key=lambda x: x[2])  # Sort by error
        
        for (sys, damping, force_pattern), opt_scale, min_error, config in results:
            pattern_label = create_force_pattern_label(force_pattern, len(damping))
            
            report_lines.append(f"\n  Configuration:")
            report_lines.append(f"    Damping:       {damping}")
            report_lines.append(f"    Force Pattern: {pattern_label} {force_pattern}")
            report_lines.append(f"    Optimal Scale: {opt_scale:.3f}")
            report_lines.append(f"    Min Error:     {min_error:.6f}")
            report_lines.append(f"    Valid Model:   {config.get('valid_model', False)}")
            report_lines.append(f"    Max Time:      {config.get('max_validation_end_time', 0.0):.2f}s")
    
    report_lines.append("\n" + "=" * 80)
    
    # Save report
    report_file = os.path.join(output_dir, "summary_report.txt")
    with open(report_file, 'w') as f:
        f.write('\n'.join(report_lines))
    
    print(f"Saved summary report to {report_file}")
    print("\n" + '\n'.join(report_lines[:20]))  # Print first 20 lines


def main():
    """Main analysis pipeline."""
    
    # Create output directory
    output_dir = "example/quick_gridsearch/analysis"
    os.makedirs(output_dir, exist_ok=True)
    
    # Load all results
    results = load_all_results()
    
    if not results:
        print("No results found. Run experiments first!")
        return
    
    # Group results by configuration
    grouped = group_results(results)
    
    # Find optimal force scales for each configuration
    optimal_results = {}
    for group_key, group_data in grouped.items():
        opt_scale, min_error, best_config = find_optimal_force_scale(group_data)
        optimal_results[group_key] = (opt_scale, min_error, best_config)
        
        # Plot individual configuration
        plot_error_vs_force_scale(group_data, group_key, output_dir)
    
    # Generate summary visualizations
    plot_optimal_scales_histogram(optimal_results, output_dir)
    plot_optimal_scales_heatmap(optimal_results, output_dir)
    
    # Generate text report
    generate_summary_report(optimal_results, output_dir)
    
    # Save optimal configurations to JSON
    optimal_configs_serializable = {}
    for key, (opt_scale, min_error, config) in optimal_results.items():
        system, damping, force_pattern = key
        key_str = f"{system}_{damping}_{force_pattern}"
        optimal_configs_serializable[key_str] = {
            "system": system,
            "damping": damping,
            "force_pattern": force_pattern,
            "optimal_scale": float(opt_scale) if not np.isnan(opt_scale) else None,
            "min_error": float(min_error) if not np.isinf(min_error) else None,
            "forces_scale_vector": config.get("forces_scale_vector", []),
        }
    
    json_file = os.path.join(output_dir, "optimal_configurations.json")
    with open(json_file, 'w') as f:
        json.dump(optimal_configs_serializable, f, indent=2)
    
    print(f"\nOptimal configurations saved to {json_file}")
    print(f"All analysis outputs saved to {output_dir}")


if __name__ == "__main__":
    main()
