import numpy as np
from tlc.core.data_formats.segmentation import CocoRle as CocoRle

class SegmentationHelper:
    """Helper class for segmentation operations."""
    @staticmethod
    def empty_rle(height: int, width: int) -> CocoRle:
        """Create an empty RLE mask with the given dimensions.

        :param height: Height of the mask
        :param width: Width of the mask

        :return: An empty RLE mask dictionary with 'counts' and 'size' fields
        """
    @staticmethod
    def mask_from_rle(rle: dict[str, list[int] | bytes]) -> np.ndarray:
        """Convert an RLE mask to a numpy array.

        :param rle: The RLE mask to convert

        :return: A numpy array of shape (H, W, N) containing N binary masks
        """
    @staticmethod
    def masks_from_rles(rles: list[CocoRle]) -> np.ndarray:
        """Convert multiple RLE masks to a numpy array.

        :param rles: List of RLE dictionaries with 'counts' and 'size' fields

        :return: A numpy array of shape (H, W, N) containing N binary masks
        """
    @staticmethod
    def mask_from_polygons(polygons: list[list[float]], height: int, width: int, relative: bool = False) -> np.ndarray:
        """Convert a list of polygons to a numpy array.

        :param polygons: The list of polygons to convert
        :param height: The height of the image
        :param width: The width of the image
        :param relative: Whether the polygons are relative to the image size

        :return: A numpy array of shape (H, W, N) containing N binary masks
        """
    @staticmethod
    def polygons_from_mask(mask: np.ndarray, relative: bool = False) -> list[float]:
        """Convert a binary mask to a list of polygons using OpenCV contour detection.

        :param mask: The binary mask to convert
        :param relative: Whether to return polygons with coordinates relative to image dimensions

        :return: List of polygons where each polygon is a flattened list of x,y coordinates
        """
    @staticmethod
    def polygons_from_rles(rles: list[CocoRle], relative: bool = False) -> list[list[float]]:
        """Convert a list of RLE encoded masks to polygons.

        :param rles: List of RLE dictionaries with 'counts' and 'size' fields
        :param relative: Whether to return polygons with coordinates relative to image dimensions

        :return: List of polygons where each polygon is a flattened list of x,y coordinates
        """
    @staticmethod
    def rles_from_polygons(polygons: list[list[float]], height: int, width: int, relative: bool = False) -> list[CocoRle]:
        """Convert a list of polygons to RLE format.

        :param polygons: The list of polygons to convert
        :param height: The height of the image
        :param width: The width of the image
        :param relative: Whether the polygons are relative to the image size

        :return: List of RLE dictionaries with 'counts' and 'size' fields
        """
    @staticmethod
    def rles_from_masks(masks: np.ndarray) -> list[CocoRle]:
        """Convert a stack of binary masks to RLE format.

        :param masks: A numpy array of shape (H, W, N) containing N binary masks

        :return: List of RLE dictionaries with 'counts' and 'size' fields
        """
    @staticmethod
    def bbox_from_rle(rle: CocoRle) -> list[float]:
        """Convert an RLE mask to a bounding box.

        :param rle: The RLE mask to convert

        :return: A list of bounding box coordinates [x1, y1, x2, y2]
        """
