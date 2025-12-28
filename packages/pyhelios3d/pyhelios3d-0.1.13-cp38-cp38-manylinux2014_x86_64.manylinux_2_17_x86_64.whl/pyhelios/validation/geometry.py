"""
Validation for Context geometry operations.

Provides comprehensive validation for all geometry creation methods,
ensuring parameters are valid before reaching C++ code.
"""

from typing import List, Union, Any, Optional
from .core import validate_input, coerce_to_vec3, coerce_to_vec2, validate_positive_value
from .datatypes import (validate_rgb_color, validate_vec3, validate_vec2, 
                       validate_spherical_coord)
from .exceptions import ValidationError, create_validation_error


def validate_geometry_center(center: Any, param_name: str = "center", function_name: str = None):
    """Validate geometry center is a valid vec3."""
    validate_vec3(center, param_name, function_name)


def validate_geometry_size2d(size: Any, param_name: str = "size", function_name: str = None):
    """Validate 2D size is a valid vec2 with positive values."""
    validate_vec2(size, param_name, function_name)
    
    if hasattr(size, 'x') and hasattr(size, 'y'):
        if size.x <= 0:
            raise create_validation_error(
                f"Size x-component must be positive, got {size.x}",
                param_name=f"{param_name}.x",
                function_name=function_name,
                expected_type="positive number",
                actual_value=size.x,
                suggestion="Size dimensions must be greater than 0."
            )
            
        if size.y <= 0:
            raise create_validation_error(
                f"Size y-component must be positive, got {size.y}",
                param_name=f"{param_name}.y",
                function_name=function_name,
                expected_type="positive number",
                actual_value=size.y,
                suggestion="Size dimensions must be greater than 0."
            )


def validate_geometry_size3d(size: Any, param_name: str = "size", function_name: str = None):
    """Validate 3D size is a valid vec3 with positive values."""
    validate_vec3(size, param_name, function_name)
    
    if hasattr(size, 'x') and hasattr(size, 'y') and hasattr(size, 'z'):
        if size.x <= 0:
            raise create_validation_error(
                f"Size x-component must be positive, got {size.x}",
                param_name=f"{param_name}.x",
                function_name=function_name,
                expected_type="positive number",
                actual_value=size.x,
                suggestion="Size dimensions must be greater than 0."
            )
            
        if size.y <= 0:
            raise create_validation_error(
                f"Size y-component must be positive, got {size.y}",
                param_name=f"{param_name}.y",
                function_name=function_name,
                expected_type="positive number",
                actual_value=size.y,
                suggestion="Size dimensions must be greater than 0."
            )
            
        if size.z <= 0:
            raise create_validation_error(
                f"Size z-component must be positive, got {size.z}",
                param_name=f"{param_name}.z",
                function_name=function_name,
                expected_type="positive number",
                actual_value=size.z,
                suggestion="Size dimensions must be greater than 0."
            )


def validate_tube_nodes(nodes: List[Any], param_name: str = "nodes", function_name: str = None):
    """Validate tube nodes list."""
    if not isinstance(nodes, list):
        raise create_validation_error(
            f"Parameter must be a list of vec3 positions",
            param_name=param_name,
            function_name=function_name,
            expected_type="list of vec3",
            actual_value=nodes,
            suggestion="Provide a list of vec3 objects representing tube node positions."
        )
    
    if len(nodes) < 2:
        raise create_validation_error(
            f"Parameter must contain at least 2 nodes for tube creation, got {len(nodes)}",
            param_name=param_name,
            function_name=function_name,
            expected_type="list with >= 2 elements",
            actual_value=nodes,
            suggestion="Tubes require at least 2 nodes to define a path."
        )
    
    for i, node in enumerate(nodes):
        validate_vec3(node, f"{param_name}[{i}]", function_name)


def validate_tube_radii(radii: Union[float, List[float]], nodes_count: int, 
                       param_name: str = "radii", function_name: str = None):
    """Validate tube radii specification."""
    if isinstance(radii, (int, float)):
        validate_positive_value(radii, param_name, function_name)
    elif isinstance(radii, list):
        if len(radii) != nodes_count:
            raise create_validation_error(
                f"Radii list must have same length as nodes ({nodes_count}), got {len(radii)} radii",
                param_name=param_name,
                function_name=function_name,
                expected_type=f"list with {nodes_count} elements",
                actual_value=radii,
                suggestion="Provide one radius value per node, or use a single radius for all nodes."
            )
        
        for i, radius in enumerate(radii):
            validate_positive_value(radius, f"{param_name}[{i}]", function_name)
    else:
        raise create_validation_error(
            f"Parameter must be a positive number or list of positive numbers",
            param_name=param_name,
            function_name=function_name,
            expected_type="positive number or list of positive numbers",
            actual_value=radii,
            suggestion="Use a single positive radius or a list of positive radii (one per node)."
        )


def validate_ndivs_parameter(ndivs: Any, param_name: str = "ndivs", function_name: str = None, min_value: int = 3):
    """Validate ndivs parameter for geometry subdivision."""
    if not isinstance(ndivs, int):
        raise create_validation_error(
            f"Parameter must be an integer",
            param_name=param_name,
            function_name=function_name,
            expected_type="integer",
            actual_value=ndivs,
            suggestion="Use an integer value for subdivision count."
        )
    
    if ndivs < min_value:
        raise create_validation_error(
            f"Parameter must be >= {min_value}, got {ndivs}",
            param_name=param_name,
            function_name=function_name,
            expected_type=f"integer >= {min_value}",
            actual_value=ndivs,
            suggestion=f"Use at least {min_value} subdivisions for valid geometry."
        )
    
    if ndivs > 1000:  # Reasonable upper limit to prevent performance issues
        raise create_validation_error(
            f"Parameter {ndivs} is very large and may cause performance issues",
            param_name=param_name,
            function_name=function_name,
            expected_type="integer <= 1000",
            actual_value=ndivs,
            suggestion="Consider using fewer subdivisions (typically < 100) for better performance."
        )


# Geometry validation decorators

def validate_patch_params(func):
    """Decorator for addPatch method validation."""
    return validate_input(
        param_validators={
            'center': validate_geometry_center,
            'size': validate_geometry_size2d,
            'rotation': validate_spherical_coord,
            'color': validate_rgb_color
        },
        type_coercions={
            'center': coerce_to_vec3,
            'size': coerce_to_vec2
        }
    )(func)


def validate_triangle_params(func):
    """Decorator for addTriangle method validation.""" 
    return validate_input(
        param_validators={
            'vertex0': lambda v, **kw: validate_geometry_center(v, 'vertex0', kw.get('function_name')),
            'vertex1': lambda v, **kw: validate_geometry_center(v, 'vertex1', kw.get('function_name')),
            'vertex2': lambda v, **kw: validate_geometry_center(v, 'vertex2', kw.get('function_name')),
            'color': validate_rgb_color
        },
        type_coercions={
            'vertex0': lambda v, **kw: coerce_to_vec3(v, 'vertex0'),
            'vertex1': lambda v, **kw: coerce_to_vec3(v, 'vertex1'),
            'vertex2': lambda v, **kw: coerce_to_vec3(v, 'vertex2')
        }
    )(func)


def validate_sphere_params(func):
    """Decorator for addSphere method validation."""
    def validate_sphere_specific(radius, param_name="radius", function_name=None):
        validate_positive_value(radius, param_name, function_name)
        
    return validate_input(
        param_validators={
            'center': validate_geometry_center,
            'radius': validate_sphere_specific,
            'color': validate_rgb_color,
            'ndivs': validate_ndivs_parameter
        },
        type_coercions={
            'center': coerce_to_vec3
        }
    )(func)


def validate_tube_params(func):
    """Decorator for addTube method validation."""
    def validate_tube_wrapper(self, nodes=None, radii=None, ndivs=6, colors=None, **kwargs):
        # Custom validation that can access nodes to validate radii
        if nodes is not None:
            validate_tube_nodes(nodes, "nodes", func.__name__)
            
        if radii is not None and nodes is not None:
            validate_tube_radii(radii, len(nodes), "radii", func.__name__)
        elif radii is not None:
            # Single radius value
            if isinstance(radii, (int, float)):
                validate_positive_value(radii, "radii", func.__name__)
            else:
                validate_tube_radii(radii, 2, "radii", func.__name__)  # Default minimum
                
        if colors is not None:
            if isinstance(colors, list):
                for i, color in enumerate(colors):
                    validate_rgb_color(color, f"colors[{i}]", func.__name__)
            else:
                validate_rgb_color(colors, "colors", func.__name__)
            
        return func(self, nodes, radii, ndivs, colors, **kwargs)
    
    return validate_tube_wrapper


def validate_box_params(func):
    """Decorator for addBox method validation."""
    return validate_input(
        param_validators={
            'center': validate_geometry_center,
            'size': validate_geometry_size3d,
            'rotation': validate_spherical_coord,
            'color': validate_rgb_color
        },
        type_coercions={
            'center': coerce_to_vec3
        }
    )(func)


def validate_disk_params(func):
    """Decorator for addDisk method validation."""
    def validate_disk_specific(radius, param_name="radius", function_name=None):
        validate_positive_value(radius, param_name, function_name)
        
    return validate_input(
        param_validators={
            'center': validate_geometry_center,
            'size': validate_disk_specific,
            'rotation': validate_spherical_coord,
            'color': validate_rgb_color,
            'ndivs': validate_ndivs_parameter
        },
        type_coercions={
            'center': coerce_to_vec3
        }
    )(func)


def validate_cone_params(func):
    """Decorator for addCone method validation."""
    def validate_cone_specific(radius, param_name="radius", function_name=None):
        validate_positive_value(radius, param_name, function_name)
        
    def validate_height(height, param_name="height", function_name=None):
        validate_positive_value(height, param_name, function_name)
        
    return validate_input(
        param_validators={
            'center': validate_geometry_center,
            'radius': validate_cone_specific,
            'height': validate_height,
            'rotation': validate_spherical_coord,
            'color': validate_rgb_color,
            'ndivs': validate_ndivs_parameter
        },
        type_coercions={
            'center': coerce_to_vec3
        }
    )(func)