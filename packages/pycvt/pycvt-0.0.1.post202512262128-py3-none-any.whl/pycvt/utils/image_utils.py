from copy import deepcopy

import cv2
import numpy as np


def blend_rgba(
        bg_crop: np.ndarray,
        fg_crop: np.ndarray,
        alpha_threshold=10,  # 默认透明度阈值
        **kwargs,
) -> np.ndarray:
    """
    只替换 fg_crop 中 alpha > 0 的区域，直接覆盖 bg_crop 对应像素，
    其他部分保留 bg_crop。

    要求 bg_crop 和 fg_crop 形状相同，且均为 RGBA。
    """
    if bg_crop.shape != fg_crop.shape or bg_crop.shape[2] != 4:
        raise ValueError("输入图像需为形状相同的 RGBA 图像")

    out = bg_crop.copy()

    alpha_mask = fg_crop[:, :, 3] > alpha_threshold

    for c in range(4):
        channel_bg = out[:, :, c]
        channel_fg = fg_crop[:, :, c]
        channel_bg[alpha_mask] = channel_fg[alpha_mask]

    return out


def convert_rgba(img: np.ndarray) -> np.ndarray:
    """
    支持灰度图、RGB图和RGBA图，统一输出 RGBA。
    已经是 RGBA 的直接返回。

    参数：
        img (np.ndarray): 输入图像

    返回：
        np.ndarray: RGBA 图像
    """
    if len(img.shape) == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGBA)
    elif img.shape[2] == 3:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2RGBA)
    elif img.shape[2] == 4:
        # 已经是 RGBA，直接返回
        return img
    else:
        raise ValueError(f"只支持灰度图、RGB和RGBA图，当前通道数: {img.shape[2] if len(img.shape) > 2 else 1}")

    return img


def crop_image(img: np.ndarray, x: int, y: int, crop_w: int, crop_h: int) -> np.ndarray:
    """
    从图像中裁剪指定区域，自动限制不会超出图像边界。

    参数：
        img (np.ndarray): 输入图像，shape (H, W, C) 或 (H, W)
        x (int): 裁剪区域左上角的横坐标（列）
        y (int): 裁剪区域左上角的纵坐标（行）
        crop_w (int): 裁剪宽度
        crop_h (int): 裁剪高度

    返回：
        np.ndarray: 裁剪后的图像区域
    """
    img_h, img_w = img.shape[:2]

    # 限制裁剪坐标和尺寸不超过图像范围
    x_end = min(img_w, x + crop_w)
    y_end = min(img_h, y + crop_h)

    # 防止坐标越界（x, y不能小于0）
    x = max(0, x)
    y = max(0, y)

    return img[y:y_end, x:x_end]


def get_opaque_bounding_box(rgba_img: np.ndarray, alpha_threshold: int = 0):
    """
    给定 RGBA 图，返回不透明区域的外接矩形 (top, left, bottom, right)。

    alpha_threshold：不透明的阈值，默认为0，表示alpha>0的像素算不透明。

    如果全透明，则返回 None。
    """
    if rgba_img.shape[2] != 4:
        raise ValueError("输入图像必须是 RGBA 格式")

    alpha = rgba_img[:, :, 3]
    mask = alpha > alpha_threshold

    if not np.any(mask):
        return None  # 全透明无外接矩形

    coords = np.argwhere(mask)  # 找出所有不透明像素的坐标，格式为 (y, x)
    ymin, xmin = coords.min(axis=0)
    ymax, xmax = coords.max(axis=0)

    return (xmin, ymin, xmax, ymax)


def rotate_image_with_bound(image: np.ndarray, angle: float = None) -> np.ndarray:
    """
    旋转图像，自动扩充尺寸以适应整个旋转后的图像。
    RGB 背景填白，RGBA 背景填透明。

    参数:
        image: 输入图像 (H, W, 3) 或 (H, W, 4)
        angle: 逆时针旋转角度，单位度，如果为 None，则随机选择一个角度。

    返回:
        旋转后自动扩充尺寸的图像
    """

    image = deepcopy(image)

    if angle is None:
        angle = np.random.randint(-180, 180)

    (h, w) = image.shape[:2]
    (cx, cy) = (w // 2, h // 2)

    M = cv2.getRotationMatrix2D((cx, cy), -angle, 1.0)

    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])

    new_w = int((h * sin) + (w * cos))
    new_h = int((h * cos) + (w * sin))

    M[0, 2] += (new_w / 2) - cx
    M[1, 2] += (new_h / 2) - cy

    # 判断通道数，设置填充颜色
    if image.shape[2] == 3:
        border_val = (255, 255, 255)  # 白色填充
    elif image.shape[2] == 4:
        border_val = (0, 0, 0, 0)  # 透明填充
    else:
        raise ValueError("只支持 RGB 或 RGBA 图像")

    rotated = cv2.warpAffine(image, M, (new_w, new_h), flags=cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_CONSTANT, borderValue=border_val)
    return rotated
