# Tile Picker for ComfyUI

Take one tile from a regular collage grid on each workflow execution. Select tiles randomly, or advance from first to last and repeat. No extra packages are required beyond ComfyUI.

## Install

1. Clone this repository into your ComfyUI `custom_nodes` folder, or download it and copy the extracted `tile-picker` folder there:

   ```sh
   git clone https://github.com/MKRshift/tile-picker.git
   ```

   Run that command from inside `ComfyUI/custom_nodes`. Private repositories require GitHub access.
2. Restart ComfyUI and refresh the browser.
3. Search for **Collage Tile Picker**, under **image → collage**.

## Connect

`Load Image → Collage Tile Picker → Preview Image / Save Image`

Connect the IMAGE output of Load Image to the node's image input. Connect this node's image output to Preview Image, Save Image, or any node that accepts an IMAGE. A connected output node is needed for ComfyUI to execute the branch.

## Controls

| Control | Meaning |
| --- | --- |
| columns | Number of tiles horizontally (X). |
| rows | Number of tiles vertically (Y). |
| mode | `sequential`: next tile each execution, looping forever. `random`: independently choose any tile each execution; repeats are possible. |
| order | `across rows`: left to right, then next row. `down columns`: top to bottom, then next column. |
| start_tile | First tile for a new sequence, numbered from 1 in the selected reading order. Must fit the grid. |
| reset_counter | Change to a different number to restart at start_tile. Leave it unchanged to keep advancing. |

For a 2 × 2 grid in **across rows** order:

```text
1  2
3  4
```

With **down columns**:

```text
1  3
2  4
```

For a 4 × 4 collage, set columns = 4 and rows = 4. Sequential mode returns 1, 2, …, 16, 1, 2, … as you run the workflow repeatedly. Queueing multiple runs advances once for each execution of this node.

The extra outputs give the selected tile number, column, and row (all numbered from 1).

## Behavior and limits

- Crops the existing pixels without resizing. Use an evenly spaced grid with no gutters or outer borders. Borders in the source remain part of the crops.
- If image dimensions do not divide evenly, neighboring tile sizes can differ by one pixel. All pixels belong to exactly one tile.
- A batched IMAGE input returns the same selected region from every image in the batch, preserving the batch.
- Sequence state stays in server memory, separately for each node ID. Restarting ComfyUI resets it. It is not saved with the workflow. Workflows sharing the same node ID on the same server can share sequence state.
- Changing grid, order, mode, starting tile, reset counter, or image dimensions starts a new sequence. Loading another image of the same size continues the current sequence; change reset_counter to restart.
- The node always runs when its connected output branch executes. A later downstream failure does not undo a selected tile.

## Development checks

From this folder, with ComfyUI's Python environment (which includes PyTorch):

```sh
python -m unittest discover -s tests -v
```

Implemented against the supported [ComfyUI custom node interface](https://docs.comfy.org/custom-nodes/backend/server_overview) and [IMAGE tensor format](https://docs.comfy.org/custom-nodes/backend/images_and_masks).
