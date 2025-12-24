from _typeshed import Incomplete
from tlc.core.builtins.constants.column_names import BOUNDING_BOXES as BOUNDING_BOXES, BOUNDING_BOX_LIST as BOUNDING_BOX_LIST, HEIGHT as HEIGHT, IMAGE as IMAGE, IMAGE_HEIGHT as IMAGE_HEIGHT, IMAGE_WIDTH as IMAGE_WIDTH, LABEL as LABEL, SAMPLE_WEIGHT as SAMPLE_WEIGHT, SEGMENTATION as SEGMENTATION, SEGMENTATIONS as SEGMENTATIONS, WIDTH as WIDTH, X0 as X0, X1 as X1, Y0 as Y0, Y1 as Y1
from tlc.core.data_formats.segmentation import CocoRle as CocoRle
from tlc.core.helpers.segmentation_helper import SegmentationHelper as SegmentationHelper
from tlc.core.objects.table import Table as Table
from tlc.core.objects.tables.from_url.utils import resolve_coco_table_url as resolve_coco_table_url
from tlc.core.url import Url as Url
from typing import Literal

msg: str
logger: Incomplete

def register_coco_instances(name: str, metadata: dict, json_file: str, image_root: str | None, revision_url: str = '', project_name: str = '', keep_crowd_annotations: bool = True, task: Literal['detect', 'segment'] = 'detect', mask_format: Literal['bitmask', 'polygon'] = 'polygon') -> None:
    '''Register a COCO dataset in Detectron2\'s standard format.

    This method works as a drop-in replacement for detectron2.data.datasets.register_coco_instances.

    :References:

    + [COCO data format](https://cocodataset.org/#format-data)
    + [Detectron2 datasets](https://detectron2.readthedocs.io/en/latest/tutorials/datasets.html)

    The original function reads the json file and uses `pycocoapi` to construct a list of dicts
    which are then registered under the key `name` in detectron\'s `DatasetCatalog`.

    These dicts have the following format:

    ```
    {
        "file_name": "COCO_train2014_000000000009.jpg",
        "height": 480,
        "width": 640,
        "image_id": 9,
        "annotations": [
            {
                "bbox": [97.84, 12.43, 424.93, 407.73],
                "bbox_mode": 1,
                "category_id": 16,
                "iscrowd": 0,
                "segmentation": [[...]]
            },
            ...
        ]
    }
    ```

    This function also registers a list of dicts under the key `name` in detectron\'s `DatasetCatalog`, but before the
    data is generated, a `Table` is resolved. The first time the function is called with a given signature, a 3LC
    `Table` is created. On subsequent calls, the Table is replaced with the most recent descendant of the
    root table. If the resolved table contains a `weight` column, this value will be sent along in the list of dicts.

    :param name: the name that identifies a dataset, e.g. "coco_2014_train".
    :param metadata: extra metadata associated with this dataset.
    :param json_file: path to the json instance annotation file.
    :param image_root: directory which contains all the images. `None` if the file_name contains a complete path.
    :param revision_url: url to a specific revision of the table. If not provided, the latest revision will be used.
        If the revision is not a descendant of the initial table, an error will be raised.
    :param project_name: the name of the project.
    :param task: the task to register the dataset for.
    :param mask_format: the format to use for the masks (only used when task is "segment"). Corresponds to the
        detectron2 config `INPUT.MASK_FORMAT`.

    :returns: None
    '''
