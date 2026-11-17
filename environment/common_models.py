"""
Common procedural 3D models for optimization.
Reuses cylinder and cone meshes across all scene entities to maximize performance on Intel Iris Xe.
"""
from ursina.models.procedural.cylinder import Cylinder
from ursina.models.procedural.cone import Cone

_cylinder_mesh = None
_cone_mesh = None

def get_cylinder(resolution=12):
    global _cylinder_mesh
    if _cylinder_mesh is None:
        _cylinder_mesh = Cylinder(resolution=resolution)
    return _cylinder_mesh

def get_cone(resolution=12):
    global _cone_mesh
    if _cone_mesh is None:
        _cone_mesh = Cone(resolution=resolution)
    return _cone_mesh

