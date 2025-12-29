import numpy as np


def generate_sliding_windows(im_shape, ws=(800, 800), s=None):
    im_h, im_w = im_shape[:2]

    window_h, window_w = np.array(ws).astype(int)[:2]
    s = ws if s is None else s
    stride_h, stride_w = np.array(s).astype(int)[:2]

    ys = np.arange(0, im_h - window_h + 1, stride_h)
    xs = np.arange(0, im_w - window_w + 1, stride_w)

    thresh_h = int(im_h * 0.001)
    thresh_w = int(im_w * 0.001)

    if xs[-1] + window_w < im_w - thresh_w:
        xs = np.append(xs, im_w - window_w)

    if ys[-1] + window_h < im_h - thresh_h:
        ys = np.append(ys, im_h - window_h)

    xx, yy = np.meshgrid(xs, ys)
    x1 = xx.ravel()
    y1 = yy.ravel()
    x2 = x1 + window_w
    y2 = y1 + window_h

    windows = np.stack([x1, y1, x2, y2], axis=1)

    return windows


def sliding_crop(image, ws=(800, 800), s=None):
    coords = generate_sliding_windows(image.shape, ws=ws, s=s)

    crops = [image[y1:y2, x1:x2] for (x1, y1, x2, y2) in coords]
    return crops, coords


def box_iou(boxes1, boxes2):
    """
    计算两个 box 集合的 IoU（交并比），完全用 numpy 实现。
    Args:
        boxes1 (np.ndarray): [N, 4]，格式为 (x1, y1, x2, y2)
        boxes2 (np.ndarray): [M, 4]，格式为 (x1, y1, x2, y2)
    Returns:
        iou (np.ndarray): [N, M]，每个 box1 和每个 box2 的 IoU
    """
    boxes1 = np.asarray(boxes1)
    boxes2 = np.asarray(boxes2)
    N = boxes1.shape[0]
    M = boxes2.shape[0]

    # 计算交集左上和右下坐标
    lt = np.maximum(boxes1[:, None, :2], boxes2[None, :, :2])  # [N, M, 2]
    rb = np.minimum(boxes1[:, None, 2:], boxes2[None, :, 2:])  # [N, M, 2]

    wh = np.clip(rb - lt, a_min=0, a_max=None)  # [N, M, 2]
    inter = wh[..., 0] * wh[..., 1]  # [N, M]

    area1 = (boxes1[:, 2] - boxes1[:, 0]) * (boxes1[:, 3] - boxes1[:, 1])  # [N]
    area2 = (boxes2[:, 2] - boxes2[:, 0]) * (boxes2[:, 3] - boxes2[:, 1])  # [M]

    union = area1[:, None] + area2[None, :] - inter
    iou = inter / (union + 1e-7)
    return iou


def xyxy2xywhn(x, w: int = 640, h: int = 640, safe: bool = True):
    """
    Convert bounding boxes from (x1, y1, x2, y2) format to
    normalized (x_center, y_center, width, height) format.
    """
    y = np.empty_like(x, dtype=float)
    x1, y1, x2, y2 = x[..., 0], x[..., 1], x[..., 2], x[..., 3]
    y[..., 0] = ((x1 + x2) / 2) / w  # x center
    y[..., 1] = ((y1 + y2) / 2) / h  # y center
    y[..., 2] = (x2 - x1) / w  # width
    y[..., 3] = (y2 - y1) / h  # height
    if safe:
        y = np.clip(y, 0.0, 1.0)
    return y


def xywhn2xyxy(x, w: int = 640, h: int = 640, safe: bool = True):
    """
    Convert bounding boxes from normalized (x_center, y_center, width, height) format
    to (x1, y1, x2, y2) format.
    """
    y = np.empty_like(x, dtype=float)
    x_c, y_c, bw, bh = x[..., 0], x[..., 1], x[..., 2], x[..., 3]
    y[..., 0] = (x_c - bw / 2) * w  # x1
    y[..., 1] = (y_c - bh / 2) * h  # y1
    y[..., 2] = (x_c + bw / 2) * w  # x2
    y[..., 3] = (y_c + bh / 2) * h  # y2
    if safe:
        y[..., 0] = np.clip(y[..., 0], 0, w)
        y[..., 1] = np.clip(y[..., 1], 0, h)
        y[..., 2] = np.clip(y[..., 2], 0, w)
        y[..., 3] = np.clip(y[..., 3], 0, h)
    return y


def xyxy2xywh(x):
    """
    Convert bounding boxes from (x1, y1, x2, y2) format to
    (x_center, y_center, width, height) format.
    """
    y = np.empty_like(x, dtype=float)
    x1, y1, x2, y2 = x[..., 0], x[..., 1], x[..., 2], x[..., 3]
    y[..., 0] = (x1 + x2) / 2  # x center
    y[..., 1] = (y1 + y2) / 2  # y center
    y[..., 2] = x2 - x1  # width
    y[..., 3] = y2 - y1  # height
    return y


def xywh2xyxy(x):
    """
    Convert bounding boxes from (x_center, y_center, width, height) format
    to (x1, y1, x2, y2) format.
    """
    y = np.empty_like(x, dtype=float)
    x_c, y_c, bw, bh = x[..., 0], x[..., 1], x[..., 2], x[..., 3]
    y[..., 0] = x_c - bw / 2  # x1
    y[..., 1] = y_c - bh / 2  # y1
    y[..., 2] = x_c + bw / 2  # x2
    y[..., 3] = y_c + bh / 2  # y2
    return y


def crop_with_bbox(
    image, windows, xyxy, cls, save_empty_crop=False, min_area_ratio=0.001
):
    """Crop image regions defined by windows and adjust bounding boxes accordingly.

    Args:
        image (_type_): _description_
        windows (_type_): _description_
        xyxy (_type_): _description_
        save_empty_crop (bool, optional): _description_. Defaults to False.
        min_area_ratio (float, optional): _description_. Defaults to 0.001.
        
    Yields:
        _type_: _description_
    Args:
        image (np.ndarray): The original image from which to crop.
        windows (np.ndarray): An array of shape (M, 4) defining the cropping windows
                              in (x1, y1, x2, y2) format.
        xyxy (np.ndarray): An array of shape (N, 4) containing bounding boxes in (x1, y1, x2, y2) format.
        cls (np.ndarray): An array of shape (N,) containing class labels for each bounding box.
        save_empty_crop (bool, optional): Whether to yield crops with no bounding boxes. Defaults to False. 
        min_area_ratio (float, optional): Minimum area ratio of the bounding box to be kept after cropping. Defaults to 0.001.
    Yields:
        tuple: A tuple containing the cropped image and an array of adjusted bounding boxes in the format
               (class, x1, y1, x2, y2).
    """

    def return_empty_crop(sub_im):
        return sub_im, np.zeros((0, 5), dtype=np.float32)

    ious = box_iou(xyxy, windows)
    crop_imgs = [image[y1:y2, x1:x2] for (x1, y1, x2, y2) in windows]
    original_areas = (xyxy[:, 2] - xyxy[:, 0]) * (xyxy[:, 3] - xyxy[:, 1])
    for idx, window in enumerate(windows):
        mask = ious[:, idx] > 0.0
        x1, y1, x2, y2 = window
        sub_im = crop_imgs[idx]
        keep_xyxy = xyxy[mask].copy()

        if len(keep_xyxy) == 0:
            if save_empty_crop:
                yield return_empty_crop(sub_im)
            continue

        keep_xyxy = np.clip(keep_xyxy, [x1, y1, x1, y1], [x2, y2, x2, y2])
        keep_xyxy -= np.array([x1, y1, x1, y1])
        sub_box_areas = (keep_xyxy[:, 2] - keep_xyxy[:, 0]) * (
            keep_xyxy[:, 3] - keep_xyxy[:, 1]
        )
        keep_original_areas = original_areas[mask]
        keep_area_ratios = sub_box_areas / keep_original_areas
        area_mask = keep_area_ratios >= min_area_ratio
        if not np.any(area_mask):
            if save_empty_crop:
                yield return_empty_crop(sub_im)
            continue
        keep_xyxy = keep_xyxy[area_mask]
        keep_cls = cls[mask][area_mask]
        yield sub_im, np.hstack([keep_cls.reshape(-1, 1), keep_xyxy]).astype(np.float32)
