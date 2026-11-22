"""Pick a grid cell from a ComfyUI IMAGE without extra dependencies."""

import random
import threading


class CollageTilePicker:
    # State survives ComfyUI recreating a node instance after widget changes.
    # UNIQUE_ID keeps separate nodes independent during this server session.
    _states = {}
    _lock = threading.Lock()
    _random = random.SystemRandom()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "columns": ("INT", {"default": 2, "min": 1, "max": 4096}),
                "rows": ("INT", {"default": 2, "min": 1, "max": 4096}),
                "mode": (["sequential", "random"],),
                "order": (["across rows", "down columns"],),
                "start_tile": ("INT", {"default": 1, "min": 1, "max": 16777216}),
                "reset_counter": ("INT", {
                    "default": 0, "min": 0, "max": 2147483647,
                    "tooltip": "Change this number to restart the sequence at start_tile.",
                }),
            },
            "hidden": {"unique_id": "UNIQUE_ID"},
        }

    RETURN_TYPES = ("IMAGE", "INT", "INT", "INT")
    RETURN_NAMES = ("image", "tile_number", "column", "row")
    FUNCTION = "pick"
    CATEGORY = "image/collage"
    DESCRIPTION = "Output one collage tile each run, randomly or in a looping sequence."

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Both modes must execute again even when all inputs stay the same.
        return float("nan")

    def pick(self, image, columns, rows, mode, order, start_tile,
             reset_counter, unique_id=None):
        if len(image.shape) != 4 or image.shape[0] < 1 or image.shape[3] < 1:
            raise ValueError("Expected an IMAGE batch with shape [batch, height, width, channels].")
        height, width = image.shape[1:3]
        if not 1 <= columns <= width or not 1 <= rows <= height:
            raise ValueError("Columns and rows must be positive and cannot exceed image width and height.")
        if mode not in ("sequential", "random"):
            raise ValueError("Unknown selection mode.")
        if order not in ("across rows", "down columns"):
            raise ValueError("Unknown reading order.")
        count = columns * rows
        if not 1 <= start_tile <= count:
            raise ValueError(f"start_tile must be between 1 and {count} for this grid.")

        # Image content changes intentionally do not reset the sequence.
        signature = (columns, rows, mode, order, start_tile, reset_counter, height, width)
        key = str(unique_id) if unique_id is not None else self
        with self._lock:
            if mode == "random":
                index = self._random.randrange(count)
                self._states.pop(key, None)
            else:
                previous = self._states.get(key)
                index = previous[1] if previous and previous[0] == signature else start_tile - 1
                self._states[key] = (signature, (index + 1) % count)

        if order == "across rows":
            row, column = divmod(index, columns)
        else:
            column, row = divmod(index, rows)
        # Integer boundaries cover every pixel, including non-divisible sizes.
        left, right = column * width // columns, (column + 1) * width // columns
        top, bottom = row * height // rows, (row + 1) * height // rows
        tile = image[:, top:bottom, left:right, :].contiguous()
        return (tile, index + 1, column + 1, row + 1)
