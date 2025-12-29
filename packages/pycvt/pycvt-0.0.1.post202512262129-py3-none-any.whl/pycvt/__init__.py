from importlib.resources import files
from pathlib import Path

_pycvt_basepath_ = files("pycvt")

example_file = Path(_pycvt_basepath_) / "static/example_file.jpg"

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
    crop_with_bbox,
    sliding_crop,
    scale_boxes,
)


from .clolors.colors import (
    getcolor, # deprecated, use get_color instead
    get_color
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
    "crop_with_bbox",
    "scale_boxes",
    "getcolor",
    "get_color",
    "example_file",
]
