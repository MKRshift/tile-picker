import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

import torch

spec = importlib.util.spec_from_file_location("collage_nodes", Path(__file__).parents[1] / "nodes.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
Picker = module.CollageTilePicker


class PickerTests(unittest.TestCase):
    def setUp(self):
        Picker._states.clear()
        self.node = Picker()
        self.image = torch.arange(2 * 5 * 7 * 3).reshape(2, 5, 7, 3).float()

    def pick(self, **changes):
        args = dict(image=self.image, columns=2, rows=2, mode="sequential",
                    order="across rows", start_tile=1, reset_counter=0, unique_id="a")
        args.update(changes)
        return self.node.pick(**args)

    def test_sequence_wrap_and_exact_crops(self):
        regions = [(0, 2, 0, 3), (0, 2, 3, 7), (2, 5, 0, 3), (2, 5, 3, 7)]
        for i, (top, bottom, left, right) in enumerate(regions):
            tile, number, col, row = self.pick()
            self.assertEqual((number, col, row), (i + 1, i % 2 + 1, i // 2 + 1))
            self.assertTrue(torch.equal(tile, self.image[:, top:bottom, left:right, :]))
            self.assertTrue(tile.is_contiguous())
        self.assertEqual(self.pick()[1], 1)

    def test_column_order(self):
        coords = [self.pick(order="down columns")[2:] for _ in range(4)]
        self.assertEqual(coords, [(1, 1), (1, 2), (2, 1), (2, 2)])

    def test_reset_start_and_instance_recreation(self):
        self.assertEqual(self.pick(start_tile=3)[1], 3)
        self.node = Picker()
        self.assertEqual(self.pick(start_tile=3)[1], 4)
        self.assertEqual(self.pick(start_tile=3, reset_counter=1)[1], 3)
        self.assertEqual(self.pick(start_tile=3, reset_counter=1)[1], 4)

    def test_nodes_are_independent(self):
        self.assertEqual(self.pick()[1], 1)
        self.assertEqual(self.pick(unique_id="b")[1], 1)
        self.assertEqual(self.pick()[1], 2)

    def test_random_uses_full_grid(self):
        with patch.object(Picker._random, "randrange", side_effect=[0, 3, 3]) as rng:
            self.assertEqual([self.pick(mode="random")[1] for _ in range(3)], [1, 4, 4])
            self.assertEqual(rng.call_args.args, (4,))

    def test_changed_image_continues_and_grid_resets(self):
        self.pick()
        self.assertEqual(self.pick(image=self.image + 1)[1], 2)
        self.assertEqual(self.pick(columns=1)[1], 1)

    def test_invalid_grid_and_start(self):
        for changes in ({"columns": 8}, {"rows": 0}, {"start_tile": 5},
                        {"image": torch.zeros(5, 7, 3)}):
            with self.subTest(changes=list(changes)):
                with self.assertRaises(ValueError):
                    self.pick(**changes)

    def test_single_cell_and_four_by_four(self):
        self.assertTrue(torch.equal(self.pick(columns=1, rows=1)[0], self.image))
        numbers = [self.pick(columns=4, rows=4)[1] for _ in range(17)]
        self.assertEqual(numbers, list(range(1, 17)) + [1])

    def test_forces_execution(self):
        self.assertNotEqual(Picker.IS_CHANGED(), Picker.IS_CHANGED())


if __name__ == "__main__":
    unittest.main()
