from multiprocessing import Queue
import random
from functools import lru_cache

from distinctipy.distinctipy import get_colors, get_rgb256


_preset_colors = [
    (r / 255.0, g / 255.0, b / 255.0)
    for r, g, b in [
        (255, 0, 0),  # red
        (0, 255, 0),  # green
        (0, 0, 255),  # blue
        (255, 255, 0),  # yellow
        (0, 255, 255),  # cyan
        (255, 0, 255),  # magenta
        (255, 255, 255),  # white
        (0, 0, 0),  # black
        (128, 128, 128),  # gray
    ]
]

_preset_queue=Queue()
for color in _preset_colors:
    _preset_queue.put(color)

_colors_map = {}
_rng = random.Random("default")


def get_color(key="default", rng=_rng, use_preset=True):
    if key in _colors_map:
        color = _colors_map[key]
    else:
        if use_preset:
            if _preset_queue.qsize() > 0:
                color = _preset_queue.get()
                _colors_map[key] = color
            else:
                exclude_colors = list(
                    set(list(_preset_colors) + [c for c in _colors_map.values()])
                )
                new_colors = get_colors(1, exclude_colors=exclude_colors, rng=rng)
                color = new_colors[0]
        else:
            exclude_colors = list(
                set(list(_preset_colors) + [c for c in _colors_map.values()])
            )
            new_colors = get_colors(1, exclude_colors=exclude_colors, rng=rng)
            color = new_colors[0]

        _colors_map[key] = color
    return get_rgb256(color)


def getcolor(*args, **kwargs):
    import warnings
    warnings.warn(
        "'getcolor' is deprecated, use 'get_color' instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return get_color(*args, **kwargs)



if __name__ == "__main__":
    # 测试代码
    keys = ["apple", "banana", "cherry", "date", "elderberry", "fig", "grape"]       
    import matplotlib.pyplot as plt
    
    # 测试 use_preset=True
    fig, ax = plt.subplots(figsize=(10, 3))
    for i, key in enumerate(keys):
        color = getcolor(key, use_preset=True)
        ax.add_patch(plt.Rectangle((i, 1), 1, 1, color=[c / 255.0 for c in color]))
        ax.text(i + 0.5, 1.5, key, ha='center', va='center', fontsize=8)
    
    _colors_map = {}
    # 测试 use_preset=False
    for i, key in enumerate(keys):
        color = getcolor(key, use_preset=False)
        ax.add_patch(plt.Rectangle((i, 0), 1, 1, color=[c / 255.0 for c in color]))
        ax.text(i + 0.5, 0.5, key, ha='center', va='center', fontsize=8, color='black' if sum(color) > 382 else 'white')
    
    ax.set_xlim(0, len(keys))
    ax.set_ylim(0, 2)
    ax.text(-0.5, 1.5, "use_preset=True", ha='right', va='center', fontsize=10, weight='bold')
    ax.text(-0.5, 0.5, "use_preset=False", ha='right', va='center', fontsize=10, weight='bold')
    
    bg_color = getcolor("background")
    fig.patch.set_facecolor([c / 255.0 for c in bg_color])
    plt.axis('off')
    plt.show()