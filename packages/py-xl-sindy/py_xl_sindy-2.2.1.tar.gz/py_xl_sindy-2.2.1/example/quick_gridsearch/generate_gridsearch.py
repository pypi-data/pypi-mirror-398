"""
Generate grid search configurations for optimal force scale vector search.

This script creates a comprehensive grid search over:
- Different systems
- Different damping coefficients
- Different force localizations (which coordinates receive forces)
- Different force scale vectors

Outputs a bash script to run all experiments in parallel.
"""

import json
import os
import itertools
import hashlib
from typing import List, Dict, Any
import numpy as np

# Configuration for grid search
SYSTEMS = ["cart_pole", "cart_pole_double", "double_pendulum_pm"]

# Damping configurations to test
DAMPING_CONFIGS = [
    [-1.0],
    [-0.0],
]

# Force localization patterns (which coordinates receive forces)
# For 2-coordinate systems
FORCE_PATTERNS_2D = [
    [1.0, 0.0],  # Only first coordinate
    [0.0, 1.0],  # Only second coordinate
    [1.0, 1.0],  # Both coordinates equally
]

# For 4-coordinate systems (cart_pole, cart_pole_double)
FORCE_PATTERNS_3D = [
    [1.0, 0.0, 0.0],  # Only first
    [0.0, 1.0, 0.0],  # Only second
    [0.0, 0.0, 1.0],  # Only third
    [1.0, 1.0, 0.0],  # First two
    [0.0, 1.0, 1.0],  # Last two
    [1.0, 0.0, 1.0],  # Last two
    [1.0, 1.0, 1.0],  # All coordinates
]

# Force scale magnitudes to test (will be multiplied by force pattern)
FORCE_SCALES = [1.0]

# Fixed parameters
FIXED_PARAMS = {
    "random_seed": 42,
    "batch_number": 1,
    "max_time": 10.0,
    "initial_position": [0.0, 0.0, 0.0, 0.0],
    "initial_condition_randomness": [0.1],
    "data_ratio": 2.0,
    "validation_time": 30.0,
    "noise_level": 0.0,
    "simulation_mode": "mixed",
}

# System-specific configurations
SYSTEM_CONFIG = {
    "cart_pole": {
        "num_coords": 2,
        "force_patterns": FORCE_PATTERNS_2D,
    },
    "cart_pole_double": {
        "num_coords": 3,
        "force_patterns": FORCE_PATTERNS_3D,
    },
    "double_pendulum_pm": {
        "num_coords": 2,
        "force_patterns": FORCE_PATTERNS_2D,
    },
}


def generate_force_scale_vector(pattern: List[float], scale: float) -> List[float]:
    """Generate force scale vector by multiplying pattern by scale."""
    return [p * scale for p in pattern]


def adjust_damping_for_system(damping: List[float], num_coords: int) -> List[float]:
    """Adjust damping coefficients to match system dimensions."""
    if len(damping) == num_coords:
        return damping
    elif len(damping) < num_coords:
        # Repeat pattern to match size
        return (damping * (num_coords // len(damping) + 1))[:num_coords]
    else:
        # Truncate to match size
        return damping[:num_coords]


def create_experiment_config(
    system: str,
    damping: List[float],
    force_pattern: List[float],
    force_scale: float,
) -> Dict[str, Any]:
    """Create a single experiment configuration."""
    config = FIXED_PARAMS.copy()
    
    system_info = SYSTEM_CONFIG[system]
    num_coords = system_info["num_coords"]
    
    # Adjust parameters for system
    config["experiment_system"] = system
    config["damping_coefficients"] = adjust_damping_for_system(damping, num_coords)
    config["initial_position"] = [0.0] * num_coords*2
    config["forces_scale_vector"] = generate_force_scale_vector(force_pattern, force_scale)
    
    return config


def get_experiment_uid(config: Dict[str, Any]) -> str:
    """Generate unique identifier for experiment."""
    config_str = json.dumps(config, sort_keys=True)
    return hashlib.md5(config_str.encode()).hexdigest()[:8]


def main():
    """Generate grid search configurations and execution script."""
    
    # Create output directory
    output_dir = "example/quick_gridsearch/configs"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate all experiment configurations
    all_configs = []
    
    for system in SYSTEMS:
        system_info = SYSTEM_CONFIG[system]
        force_patterns = system_info["force_patterns"]
        
        for damping in DAMPING_CONFIGS:
            for force_pattern in force_patterns:
                for force_scale in FORCE_SCALES:
                    config = create_experiment_config(
                        system, damping, force_pattern, force_scale
                    )
                    
                    exp_uid = get_experiment_uid(config)
                    config["exp_uid"] = exp_uid
                    
                    all_configs.append(config)
                    
                    # Save individual config file
                    config_file = os.path.join(output_dir, f"config_{exp_uid}.json")
                    with open(config_file, 'w') as f:
                        json.dump(config, f, indent=2)
    
    print(f"Generated {len(all_configs)} experiment configurations")
    
    # Create summary file
    summary = {
        "total_experiments": len(all_configs),
        "systems": SYSTEMS,
        "num_damping_configs": len(DAMPING_CONFIGS),
        "num_force_scales": len(FORCE_SCALES),
        "experiments": all_configs,
    }
    
    summary_file = os.path.join(output_dir, "summary.json")
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Summary saved to {summary_file}")
    
    print(f"\nTo run the grid search:")
    print(f"  python example/quick_gridsearch/run_gridsearch.py")
    print(f"  Or: python example/quick_gridsearch/run_gridsearch.py --parallel 4")


if __name__ == "__main__":
    main()
