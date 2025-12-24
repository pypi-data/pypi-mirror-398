import numpy as np
from tlc.core.data_formats.geometries import Geometry3DInstances as Geometry3DInstances

class GeometryHelper:
    """Helper class for geometry."""
    @staticmethod
    def create_isotropic_bounds_2d(x_min: float, x_max: float, y_min: float, y_max: float) -> tuple[float, float, float, float]:
        """Create isotropic bounds for a set of 2D points."""
    @staticmethod
    def create_isotropic_bounds_3d(x_min: float, x_max: float, y_min: float, y_max: float, z_min: float, z_max: float, force_z_min: bool = False) -> tuple[float, float, float, float, float, float]:
        """Create isotropic bounds for a set of 3D points."""
    @staticmethod
    def load_obj_geometry(obj_path: str, scale: float = 1.0, transform: np.ndarray | None = None, bounds_3d: tuple[float, float, float, float, float, float] | None = None) -> Geometry3DInstances:
        """Load vertices and triangles from a obj file.

        The obj file should contain vertices and faces. The faces will be fan-triangulated if they are not triangles.
        The triangles will be assigned the material color of the face.

        :param obj_path: The path to the obj file.
        :param scale: The scale factor to apply to the vertices.
        :param transform: The transformation matrix to apply to the vertices (shape (3,3) or (4,4)).
        :param bounds_3d: The 3D bounds of the geometry. If None, the bounds will be computed from the vertices.
        :return: A Geometry3DInstances object.
        """
