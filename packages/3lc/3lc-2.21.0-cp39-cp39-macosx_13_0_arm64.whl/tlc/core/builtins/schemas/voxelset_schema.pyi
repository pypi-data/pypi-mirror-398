from tlc.core.builtins.constants.column_names import SIZE_X as SIZE_X, SIZE_Y as SIZE_Y, SIZE_Z as SIZE_Z, VOXELS as VOXELS
from tlc.core.builtins.constants.number_roles import NUMBER_ROLE_VOXEL_COUNT as NUMBER_ROLE_VOXEL_COUNT
from tlc.core.schema import DimensionNumericValue as DimensionNumericValue, Float32Value as Float32Value, Int32Value as Int32Value, Schema as Schema

def voxelset_schema() -> Schema:
    """
    Returns a standard schema describing a 3D voxel set
    """
