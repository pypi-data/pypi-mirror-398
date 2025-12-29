from copy import deepcopy

import cv2
import numpy as np

from pycvt.utils.image_utils import convert_rgba


def paste_image(
        bg_img,
        fg_img,
        position=None,
):
    """
    fg_img will be pasted onto bg_img at the specified position with the given alpha blending factor.

    1. If position is None, a random position will be chosen within the bounds of the background image.
    2. IF position + fg_img exceeds the bounds of bg_img, it will be clipped to fit within bg_img.

    :param bg_img: Background image, can be a numpy array or a PIL image.
    :param fg_img: Foreground image, can be a numpy array or a PIL image.
    :param position: Tuple (y, x) indicating where to paste the foreground image on the background image.
    :return: Tuple containing the modified background image and the bounding box of the pasted foreground image.
    """

    bg_img = deepcopy(bg_img)
    fg_img = deepcopy(fg_img)

    bg_img = cv2.cvtColor(bg_img, cv2.COLOR_RGB2BGR)
    fg_img = convert_rgba(fg_img)

    img_h, img_w, = bg_img.shape[:2]
    fg_h, fg_w, = fg_img.shape[:2]

    if position is None:
        position = np.random.randint(0, img_h - fg_h // 2), np.random.randint(0, img_w - fg_w // 2),

    ymin, xmin = position
    ymax, xmax = min(img_h, position[0] + fg_h), min(img_w, position[1] + fg_w)

    fg_img = fg_img[
        0:min(fg_h, ymax - ymin),
        0:min(fg_w, xmax - xmin),
        :
    ]

    blended_bgr = cv2.seamlessClone(
        src=cv2.cvtColor(fg_img, cv2.COLOR_RGBA2BGR),
        dst=bg_img,
        mask=(fg_img[:, :, 3] > 10).astype(np.uint8) * 255,
        p=((xmin + xmax) // 2, (ymin + ymax) // 2),
        flags=cv2.NORMAL_CLONE,
    )
    blended = cv2.cvtColor(blended_bgr, cv2.COLOR_BGR2RGB)
    return blended, (xmin, ymin, xmax, ymax)
