import subprocess
from pathlib import Path
from PIL import Image
import numpy as np
import sys

import pytest

from src import composite


def make_image(path: Path, size=(4, 4), color=(255, 0, 0)):
    img = Image.new('RGB', size, color)
    img.save(path)
    return path


def test_interlace_rows_same_size(tmp_path):
    a = tmp_path / 'a.png'
    b = tmp_path / 'b.png'
    out = tmp_path / 'out.png'

    # image A: red rows, image B: green rows
    img_a = Image.new('RGB', (3, 2), (255, 0, 0))
    img_b = Image.new('RGB', (3, 2), (0, 255, 0))
    img_a.save(a)
    img_b.save(b)

    composite.interlace_rows(str(a), str(b), str(out))

    out_img = Image.open(out)
    arr = np.array(out_img)

    # same size as inputs
    assert out_img.size == (3, 2)
    # check first row from A (red)
    assert (arr[0, 0] == np.array([255, 0, 0])).all()
    # check second row from B (green)
    assert (arr[1, 0] == np.array([0, 255, 0])).all()


def test_composite_rows_interleave_doubled_height(tmp_path):
    a = tmp_path / 'a2.png'
    b = tmp_path / 'b2.png'
    out = tmp_path / 'out2.png'

    img_a = Image.new('RGB', (2, 2), (10, 10, 10))
    img_b = Image.new('RGB', (2, 2), (200, 200, 200))
    img_a.save(a)
    img_b.save(b)

    composite.composite_rows(str(a), str(b), str(out))
    out_img = Image.open(out)
    arr = np.array(out_img)

    # height should be doubled
    assert out_img.size == (2, 4)
    # check alternating rows with bottom-up consumption + final flip
    # after bottom-up + flip, first row should come from B (200), then A (10)
    assert (arr[0, 0] == np.array([200, 200, 200])).all()
    assert (arr[1, 0] == np.array([10, 10, 10])).all()


def test_tiling_smaller_image(tmp_path):
    # Larger image 4x4, smaller 1x1 should tile
    a = tmp_path / 'large.png'
    b = tmp_path / 'small.png'
    out = tmp_path / 'out_tile.png'

    Image.new('RGB', (4, 4), (50, 60, 70)).save(a)
    Image.new('RGB', (1, 1), (5, 5, 5)).save(b)

    # composite interleave rows (doubled height)
    composite.composite_rows(str(a), str(b), str(out))
    out_img = Image.open(out)
    assert out_img.size == (4, 8)


def test_interlace_with_white_keyword(tmp_path):
    a = tmp_path / 'img.png'
    out = tmp_path / 'out_white.png'
    Image.new('RGB', (3, 3), (123, 45, 67)).save(a)

    # using 'white' keyword should work
    composite.interlace_rows(str(a), 'white', str(out))
    out_img = Image.open(out)
    arr = np.array(out_img)
    # odd rows should be white
    assert (arr[1, 0] == np.array([255, 255, 255])).all()
