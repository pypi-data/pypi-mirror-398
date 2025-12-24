from _typeshed import Incomplete
from numpy.typing import NDArray as NDArray
from pathlib import Path
from super_gradients.training.datasets.detection_datasets.detection_dataset import DetectionDataset as SuperGradientsDetectionDataset
from tlc.core.builtins.constants.column_names import IMAGE as IMAGE
from tlc.core.data_formats.bounding_boxes import BoundingBox as BoundingBox, XYXYBoundingBox as XYXYBoundingBox
from tlc.core.objects.table import Table as Table
from tlc.core.url import Url as Url
from typing import Any

logger: Incomplete

class DetectionDataset(SuperGradientsDetectionDataset):
    table: Table
    image_column_name: Incomplete
    label_column_name: Incomplete
    def __init__(self, table: Table | Url | Path | str, image_column_name: str = 'image', label_column_name: str = 'bbs.bb_list.label', **kwargs: Any) -> None:
        """A dataset for training SuperGradients detection models, populated from a 3LC Table.

        :::{note}
        SuperGradients models expect the labels to be contiguous from 0 to num_classes - 1. If the label value map
        keys are not contiguous, a mapping is applied for the `DetectionDataset` and the reverse is applied in the
        {py:class}`DetectionMetricsCollectionCallback<tlc.integration.super_gradients.callbacks.detection_callback.DetectionMetricsCollectionCallback>`.
        In such cases, model predictions outside of 3LC will have contiguous labels, which are not consistent with the
        keys in the 3LC Table.
        :::

        :param table: The table or URL to the table to read image paths and ground truth boxes from.
        :param image_column_name: The name of the column containing the image paths.
        :param label_column_name: The value path to the ground truth labels.
        """
