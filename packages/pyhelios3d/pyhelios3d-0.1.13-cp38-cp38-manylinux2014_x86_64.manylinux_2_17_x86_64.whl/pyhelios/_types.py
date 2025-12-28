# Convenience module for direct vector type imports
# Usage: from pyhelios.types import *

from .wrappers.DataTypes import (
    vec2, vec3, vec4, int2, int3, int4,
    RGBcolor, RGBAcolor, SphericalCoord,
    make_vec2, make_vec3, make_vec4, 
    make_int2, make_int3, make_int4,
    make_RGBcolor, make_RGBAcolor, make_SphericalCoord,
    PrimitiveType
)

def import_vector_types():
    """Import all vector types into the calling module's namespace.
    
    Usage:
        from pyhelios.types import import_vector_types
        import_vector_types()
        # Now can use vec3(1, 2, 3) directly
    """
    import inspect
    frame = inspect.currentframe().f_back
    frame.f_globals.update({
        'vec2': vec2, 'vec3': vec3, 'vec4': vec4,
        'int2': int2, 'int3': int3, 'int4': int4,
        'RGBcolor': RGBcolor, 'RGBAcolor': RGBAcolor,
        'SphericalCoord': SphericalCoord,
        'make_vec2': make_vec2, 'make_vec3': make_vec3, 'make_vec4': make_vec4,
        'make_int2': make_int2, 'make_int3': make_int3, 'make_int4': make_int4,
        'make_RGBcolor': make_RGBcolor, 'make_RGBAcolor': make_RGBAcolor,
        'make_SphericalCoord': make_SphericalCoord,
        'PrimitiveType': PrimitiveType
    })

__all__ = [
    'vec2', 'vec3', 'vec4', 'int2', 'int3', 'int4',
    'RGBcolor', 'RGBAcolor', 'SphericalCoord',
    'make_vec2', 'make_vec3', 'make_vec4', 
    'make_int2', 'make_int3', 'make_int4',
    'make_RGBcolor', 'make_RGBAcolor', 'make_SphericalCoord',
    'PrimitiveType'
]