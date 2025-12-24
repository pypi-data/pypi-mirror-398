from PIL import Image
from tlc.core.builtins.constants.column_names import X0 as X0, X1 as X1, Y0 as Y0, Y1 as Y1
from tlc.core.data_formats.bounding_boxes import BoundingBox as BoundingBox
from tlc.core.schema import Schema as Schema
from tlc.core.url import Url as Url

class BBCropInterface:
    """Interface for creating bounding box crops."""
    @staticmethod
    def crop(image_path: str | Url | Image.Image, bb_dict: dict[str, float | int], bb_schema: Schema, image_height: int = 0, image_width: int = 0, x_max_offset: float = 0.0, y_max_offset: float = 0.0, y_scale_range: tuple[float, float] = (1.0, 1.0), x_scale_range: tuple[float, float] = (1.0, 1.0)) -> Image.Image:
        """Crops an image according to a bounding box and returns the cropped image.

        The parameters x_max_offset, y_max_offset, y_scale_range, and x_scale_range are used to introduce random
        variations in the crop, which can be useful for data augmentation during training.

        :param image_path: Path to the image to crop.
        :param bb_dict: Dictionary containing bounding box coordinates under the keys X0, Y0, X1, Y1.
        :param bb_schema: Schema for the bounding box.
        :param image_height: Height of the original image (only necessary if box is in relative coordinates).
        :param image_width: Width of the original image (only necessary if box is in relative coordinates).
        :param x_max_offset: Maximum random relative offset of the crop in x direction (both left and right).
        :param y_max_offset: Maximum random relative offset of the crop in y direction (both up and down).
        :param y_scale_range: Range of random relative scaling of the crop in y direction. The first value is the
            minimum scaling factor, the second value is the maximum scaling factor.
        :param x_scale_range: Range of random relative scaling of the crop in x direction. The first value is the
            minimum scaling factor, the second value is the maximum scaling factor.
        :returns: Cropped image.
        """
