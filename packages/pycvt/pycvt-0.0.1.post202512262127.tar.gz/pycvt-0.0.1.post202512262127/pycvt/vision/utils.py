from pathlib import Path
import numpy as np


def render_text_image(text, font_path, font_size, text_color=(255, 255, 255), bg_color=None):
    from PIL import Image
    from PIL import ImageDraw
    from PIL import ImageFont

    if bg_color is None:
        bg_color = (0, 0, 0, 0)
    else:
        bg_color = (*bg_color, 255)[:4]  # 确保背景颜色是 RGBA 格式

    font = ImageFont.truetype(Path(font_path).as_posix(), font_size)
    bbox = font.getbbox(text)
    bbox = np.asarray(bbox, dtype=int).tolist()
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    img = Image.new("RGBA", (text_width, text_height), bg_color)
    draw = ImageDraw.Draw(img)
    draw.text((-bbox[0], -bbox[1]), text, font=font, fill=text_color)
    return np.array(img)


def iou(gtboxes, dtboxes):
    '''numpy version of calculating IoU between two set of 2D bboxes.

    Args:
        gtboxes (np.ndarray): Shape (B,4) of ..,  4 present [x1,y1,x2,y2]
        dtboxes,np.ndarray,shape:(N,4), 4 present [x1,y1,x2,y2].

    Returns:
        np.ndarray: Shape (B,N)  .
    '''


    gtboxes = gtboxes[:, np.
                      newaxis, :]  #converse gtboxes:(B,4) to gtboxes:(B,1,4)
    ixmin = np.maximum(gtboxes[:, :, 0], dtboxes[:, 0])
    iymin = np.maximum(gtboxes[:, :, 1], dtboxes[:, 1])
    ixmax = np.minimum(gtboxes[:, :, 2], dtboxes[:, 2])
    iymax = np.minimum(gtboxes[:, :, 3], dtboxes[:, 3])
    intersection = (ixmax - ixmin + 1) * (iymax - iymin + 1)
    union = (gtboxes[:,:,2]-gtboxes[:,:,0]+1)*(gtboxes[:,:,3]-gtboxes[:,:,1]+1)\
            +(dtboxes[:,2]-dtboxes[:,0]+1)*(dtboxes[:,3]-dtboxes[:,1]+1)-intersection
    return intersection / union