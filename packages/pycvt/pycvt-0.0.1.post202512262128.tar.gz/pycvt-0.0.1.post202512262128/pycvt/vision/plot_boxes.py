from typing import Union

import cv2
import numpy
import numpy as np
from distinctipy.distinctipy import get_rgb256, get_text_color
from easyfont import getfont

from pycvt.clolors.colors import getcolor
from pycvt.vision.utils import render_text_image

def get_text_positions(xmin, ymin, xmax, ymax, text_w, text_h, w, h, margin=2):
    """
    自动生成若干合理的位置，并保证不会超出边界
    返回按优先级排序的 (x, y) 列表
    """
    positions = []

    # 下方
    y = ymax + margin
    if y + text_h <= h:
        positions.append((xmin, y))
        positions.append((xmax - text_w, y))  # 右对齐
        positions.append((xmin + (xmax - xmin)//2 - text_w//2, y))  # 居中

    # 上方
    y = ymin - text_h - margin
    if y >= 0:
        positions.append((xmin, y))
        positions.append((xmax - text_w, y))
        positions.append((xmin + (xmax - xmin)//2 - text_w//2, y))

    # 左侧
    x = xmin - text_w - margin
    if x >= 0:
        positions.append((x, ymin))
        positions.append((x, ymax - text_h))

    # 右侧
    x = xmax + margin
    if x + text_w <= w:
        positions.append((x, ymin))
        positions.append((x, ymax - text_h))

    # 截断到图像范围
    positions = [(max(0, min(x, w - text_w)), max(0, min(y, h - text_h))) for x, y in positions]
    return positions




def draw_bounding_boxes(
        image: numpy.ndarray,
        boxes: Union[np.ndarray, list],
        labels: list = None,
        colors=None,
        line_width=None,
        font=None,
        font_size=None
):
    h, w = image.shape[:2]
    boxes = np.asarray(boxes, dtype=int)
    n = len(boxes)
    line_width = line_width if line_width else max(int(0.003 * min(w, h)), 2)
    font_size = font_size if font_size else line_width * 6
    font = font if font else getfont()

    if colors is None:
        if labels:
            colors = np.array([getcolor(label) for label in labels])
        else:
            colors = np.array([getcolor()] * n)
    labels = labels if labels else [None] * n
    boxes_colors = np.asarray(colors, dtype=int)

    for box, label, color in zip(boxes, labels, boxes_colors):
        xmin, ymin, xmax, ymax = box
        image = cv2.rectangle(image, (xmin, ymin), (xmax, ymax), color.tolist(), line_width, lineType=cv2.LINE_AA)
        if label:
            text_color = get_rgb256(get_text_color(color / 255))
            text_rendered = render_text_image(label, font, font_size, text_color=text_color, bg_color=color)[..., :3]
            text_h, text_w = text_rendered.shape[:2]
            try_poses =get_text_positions(xmin, ymin, xmax, ymax, text_w, text_h, w, h)
            for xstart, ystart in try_poses:
                if xstart < 0 or ystart < 0 or xstart + text_w > w or ystart + text_h > h:
                    continue
                image[ystart:ystart + text_h, xstart:xstart + text_w] = text_rendered
                break
    return image


