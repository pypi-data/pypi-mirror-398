from importlib.resources import files
from pathlib import Path

basepath = files("pycvt")

test_file = Path(basepath) / "static/pexels-dsengul77-32423632.jpg"

from .annotations.yolo import (
    load_yolo_annotations,
    save_yolo_annotations,
    load_yolo_names,
)


from .vision.plot_boxes import (
    draw_bounding_boxes,
)


from .vision.bbox import (
    xyxy2xywh,
    xywh2xyxy,
    xyxy2xywhn,
    xywhn2xyxy,
    box_iou,
    generate_sliding_windows,
    sliding_crop,
)


from .clolors.colors import (
    getcolor,
)


__all__ = [
    "load_yolo_annotations",
    "save_yolo_annotations",
    "load_yolo_names",
    "draw_bounding_boxes",
    "xyxy2xywh",
    "xywh2xyxy",
    "xyxy2xywhn",
    "xywhn2xyxy",
    "box_iou",
    "generate_sliding_windows",
    "sliding_crop",
    "getcolor",
    "test_file",
]
