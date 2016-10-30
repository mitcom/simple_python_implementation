import operator
from collections import namedtuple
from functools import reduce
from pprint import pprint
from typing import Sequence, Iterator, Tuple, Any, Callable, List

from PIL import Image


CROP_SIZE = (60, 60)
CROP_X, CROP_Y = CROP_SIZE
THRESHOLD = 25  # max value difference between closest part per one channel (RGB)
STEP = 1


XY = namedtuple('XY', ['x', 'y'])
TileData = namedtuple('TileData', ['frames', 'tile_image'])
ScoredTile = namedtuple('ScoredTile', ['scores', 'data'])


STRANGE_MAPPING = {
    (0, 0, False): (0, Image.FLIP_LEFT_RIGHT),
    (0, 1, False): (1, Image.FLIP_TOP_BOTTOM),
    (0, 2, False): (0, Image.FLIP_TOP_BOTTOM),
    (0, 3, False): (1, Image.FLIP_LEFT_RIGHT),
    (1, 0, False): (1, Image.FLIP_TOP_BOTTOM),
    (1, 1, False): (0, Image.FLIP_TOP_BOTTOM),
    (1, 2, False): (1, Image.FLIP_LEFT_RIGHT),
    (1, 3, False): (0, Image.FLIP_LEFT_RIGHT),
    (2, 0, False): (0, Image.FLIP_TOP_BOTTOM),
    (2, 1, False): (1, Image.FLIP_LEFT_RIGHT),
    (2, 2, False): (0, Image.FLIP_LEFT_RIGHT),
    (2, 3, False): (1, Image.FLIP_TOP_BOTTOM),
    (3, 0, False): (1, Image.FLIP_LEFT_RIGHT),
    (3, 1, False): (0, Image.FLIP_LEFT_RIGHT),
    (3, 2, False): (1, Image.FLIP_TOP_BOTTOM),
    (3, 3, False): (0, Image.FLIP_TOP_BOTTOM),
    (0, 0, True): (2, None),
    (0, 1, True): (1, None),
    (0, 2, True): (0, None),
    (0, 3, True): (3, None),
    (1, 0, True): (3, None),
    (1, 1, True): (2, None),
    (1, 2, True): (1, None),
    (1, 3, True): (0, None),
    (2, 0, True): (0, None),
    (2, 1, True): (3, None),
    (2, 2, True): (2, None),
    (2, 3, True): (1, None),
    (3, 0, True): (1, None),
    (3, 1, True): (0, None),
    (3, 2, True): (3, None),
    (3, 3, True): (2, None),
}


def apply_transform(pattern_side, side, reverse, image):
    rotate, flip = STRANGE_MAPPING[pattern_side, side, reverse]
    if rotate:
        image = image.rotate(-rotate * 90)
    if flip:
        image = image.transpose(flip)
    return image


def split_images(source: Image, crop_size: Tuple[int, int]) -> Iterator:
    source_width, source_height = source.size
    crop_width, crop_height = crop_size
    for row in range(0, source_height, crop_height):
        for cell in range(0, source_width, crop_width):
            crop_window = (cell, row, cell+crop_width, row+crop_height)
            yield source.crop(crop_window).rotate(90)


def pixels_slice(
    image: Image, ranges: Tuple[Tuple[int, int], Tuple[int, int]]
) -> List[Tuple[int, int, int]]:

    begin, end = ranges
    b_x, b_y = begin
    e_x, e_y = end
    slice = tuple(
        image.getpixel((column, row))
        for column in range(b_x, e_x, STEP if b_x < e_x else -STEP)
        for row in range(b_y, e_y, STEP if b_y < e_y else -STEP)
    )
    if len(slice) != 60:
        raise ValueError('Wrong length')
    return slice


def compare(side_a, side_b):
    r_a, g_a, b_a = zip(*side_a)
    r_b, g_b, b_b = zip(*side_b)
    r_difference = []
    for a, b in zip(r_a, r_b):
        r_difference.append(abs(a-b))
    # r_difference = sum(r_difference)
    g_difference = []
    for a, b in zip(g_a, g_b):
        g_difference.append(abs(a - b))
    # g_difference = sum(g_difference)
    b_difference = []
    for a, b in zip(b_a, b_b):
        b_difference.append(abs(a - b))
    # b_difference = sum(b_difference)
    difference = []
    difference.extend(r_difference)
    difference.extend(g_difference)
    difference.extend(b_difference)
    return reduce(operator.add, (d for d in difference if d), 1)


def get_sides(tile):
    left = pixels_slice(tile, ((0, 0), (1, CROP_Y)))
    top = pixels_slice(tile, ((CROP_X - 1, 0), (-1, 1)))
    right = pixels_slice(tile, ((CROP_X - 1, CROP_Y - 1), (CROP_X - 2, -1)))
    bottom = pixels_slice(tile, ((0, CROP_Y - 1), (CROP_X, CROP_Y - 2)))
    return left, top, right, bottom

image = Image.open('./HWSYU5_H.png')
# image.show()

tiles = list(split_images(image, CROP_SIZE))
pattern_tile = tiles.pop(0)
# pattern_tile = tiles[0]
pattern_tile.show()
pattern_side_num = 3
pattern_side = get_sides(pattern_tile)[pattern_side_num]
min_difference = len(pattern_side) * THRESHOLD ** 10000

d = {}
for tile_num, tile in enumerate(tiles):
    reverse = False
    for tile_side_num, side in enumerate(get_sides(tile)):
        # print('.', end='')
        difference = compare(pattern_side, side)
        if difference < min_difference:
            min_difference = difference
            similar_side_num = tile_side_num
            similar_reverse = reverse
            similar_tile_num = tile_num
            similar_tile = tile
        d[difference] = tile

    reverse = True
    for tile_side_num, side in enumerate(get_sides(tile)):
        # print(',', end='')
        side = side[::-1]
        difference = compare(pattern_side, side)
        if difference < min_difference:
            min_difference = difference
            similar_side_num = tile_side_num
            similar_reverse = reverse
            similar_tile_num = tile_num
            similar_tile = tile
        d[difference] = tile


print('similar_tile_num', similar_tile_num)
print('min_difference', min_difference)
print('similar_side_num', similar_side_num)
print('similar_reverse', similar_reverse)
# similar_tile.show()
#
fixed_tile = apply_transform(pattern_side_num, similar_side_num, similar_reverse, similar_tile)
fixed_tile.show()

# l = [d[D] for D in sorted(d)]
# for x in l[:10]:
#     x.show()




