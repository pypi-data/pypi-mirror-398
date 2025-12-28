"""
Validation module for PyHelios.

This module provides comprehensive parameter validation for all PyHelios operations,
ensuring fail-fast behavior with clear error messages before reaching C++ code.

Public API:
    ValidationError: Exception for validation failures
    
    Core validators:
        validate_vec3, validate_rgb_color, validate_positive_value
    
    Decorators:
        validate_geometry_params
        validate_plugin_params
    
    Coercion functions:
        coerce_to_vec3, coerce_to_vec2

Following PyHelios's fail-fast philosophy, validation provides:
- Clear, actionable error messages
- Type coercion where safe (list to vec3)
- Performance optimization via decorators
- Comprehensive testing coverage
"""

from .exceptions import ValidationError
from .core import (
    validate_input,
    is_finite_numeric,
    coerce_to_vec3,
    coerce_to_vec2,
    validate_positive_value,
    validate_non_negative_value
)
from .datatypes import (
    validate_vec3,
    validate_vec2, 
    validate_rgb_color,
    validate_rgba_color,
    validate_spherical_coord
)
from .geometry import (
    validate_geometry_center,
    validate_geometry_size2d,
    validate_geometry_size3d,
    validate_patch_params,
    validate_triangle_params,
    validate_sphere_params,
    validate_tube_params,
    validate_box_params
)
from .files import (
    validate_file_path,
    validate_directory_path
)
from .plugins import (
    validate_wavelength_range,
    validate_flux_value,
    validate_ray_count,
    validate_direction_vector,
    validate_band_label,
    validate_source_id,
    validate_source_id_list,
    validate_wpt_parameters,
    validate_time_value,
    validate_physical_quantity,
    validate_tree_id,
    validate_segment_resolution,
    validate_angle_degrees,
    validate_scaling_factor,
    validate_filename,
    validate_uuid_list,
    validate_positive_integer_range,
    validate_recursion_level,
    validate_subdivision_count
)
from .plugin_decorators import (
    # RadiationModel decorators
    validate_radiation_band_params,
    validate_collimated_source_params,
    validate_sphere_source_params,
    validate_sun_sphere_params,
    validate_source_flux_multiple_params,
    validate_get_source_flux_params,
    validate_update_geometry_params,
    validate_run_band_params,
    validate_scattering_depth_params,
    validate_min_scatter_energy_params,
    # WeberPennTree decorators
    validate_tree_uuid_params,
    validate_recursion_params,
    validate_trunk_segment_params,
    validate_branch_segment_params,
    validate_leaf_subdivisions_params,
    # EnergyBalance decorators
    validate_energy_run_params,
    validate_energy_band_params,
    validate_air_energy_params,
    validate_evaluate_air_energy_params,
    validate_output_data_params,
    validate_print_report_params,
    # Visualizer decorators
    validate_build_geometry_params,
    validate_print_window_params
)

__all__ = [
    # Exceptions
    'ValidationError',
    
    # Core functions
    'validate_input',
    'is_finite_numeric', 
    'coerce_to_vec3',
    'coerce_to_vec2',
    'validate_positive_value',
    'validate_non_negative_value',
    
    # DataTypes validation
    'validate_vec3',
    'validate_vec2',
    'validate_rgb_color', 
    'validate_rgba_color',
    'validate_spherical_coord',
    
    # Geometry validation
    'validate_geometry_center',
    'validate_geometry_size2d',
    'validate_geometry_size3d',
    'validate_patch_params',
    'validate_triangle_params', 
    'validate_sphere_params',
    'validate_tube_params',
    'validate_box_params',
    
    # File validation
    'validate_file_path',
    'validate_directory_path',
    
    # Plugin validation
    'validate_wavelength_range',
    'validate_flux_value',
    'validate_ray_count', 
    'validate_direction_vector',
    'validate_band_label',
    'validate_source_id',
    'validate_source_id_list',
    'validate_wpt_parameters',
    'validate_time_value',
    'validate_physical_quantity',
    'validate_tree_id',
    'validate_segment_resolution',
    'validate_angle_degrees',
    'validate_scaling_factor',
    'validate_filename',
    'validate_uuid_list',
    'validate_positive_integer_range',
    'validate_recursion_level',
    'validate_subdivision_count',
    
    # Plugin decorators
    'validate_radiation_band_params',
    'validate_collimated_source_params',
    'validate_sphere_source_params',
    'validate_sun_sphere_params',
    'validate_source_flux_multiple_params',
    'validate_get_source_flux_params',
    'validate_update_geometry_params',
    'validate_run_band_params',
    'validate_scattering_depth_params',
    'validate_min_scatter_energy_params',
    'validate_tree_uuid_params',
    'validate_recursion_params',
    'validate_trunk_segment_params',
    'validate_branch_segment_params',
    'validate_leaf_subdivisions_params',
    'validate_energy_run_params',
    'validate_energy_band_params',
    'validate_air_energy_params',
    'validate_evaluate_air_energy_params',
    'validate_output_data_params',
    'validate_print_report_params',
    'validate_build_geometry_params',
    'validate_print_window_params'
]