import operator
from collections import namedtuple
from functools import reduce
from pprint import pprint
from typing import Sequence, Iterator, Tuple, Any, Callable, List

from PIL import Image


CROP_SIZE = (60, 60)
CROP_X, CROP_Y = CROP_SIZE
THRESHOLD = 25  # max value difference between closest part per one channel (RGB)


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
            yield source.crop(crop_window)


def rank(image: Image, score_function: object) -> Tuple[Tuple, Tuple, 'PIL.Image']:
    #     height, width = source_image.size()
    height, width = CROP_SIZE
    left = pixels_slice(image, ((0, 0), (1, height)))
    left_rank = tuple(score_function(color) for color in zip(*left))
    top = pixels_slice(image, ((width-1, 0), (-1, 1)))
    top_rank = tuple(score_function(color) for color in zip(*top))
    right = pixels_slice(image, ((width-1, height-1), (width-2, -1)))
    right_rank = tuple(score_function(color) for color in zip(*right))
    bottom = pixels_slice(image, ((0, height-1), (width, height-2)))
    bottom_rank = tuple(score_function(color) for color in zip(*bottom))

    scores = (left_rank, top_rank, right_rank, bottom_rank)
    reversed_scores = [score[::-1] for score in scores]
    reversed_scores.extend(scores)

    return ScoredTile(
        reversed_scores,
        TileData((left, top, right, bottom), image),
    )


def pixels_slice(image: Image, ranges: Tuple[Tuple[int, int]]) -> List[Tuple[int, int, int]]:
    begin, end = ranges
    b_x, b_y = begin
    e_x, e_y = end
    return tuple(
        image.getpixel((column, row))
        for column in range(b_x, e_x, 1 if b_x < e_x else -1)
        for row in range(b_y, e_y, 1 if b_y < e_y else -1)
    )


def score_function(values: Sequence[int]):
    # return (
        # values[0] + values[-1],
        # values[9] + values[-10],
        # values[10] + values[-11],
        # values[29] + values[-30], # comment this
        # values[20] + values[-21],
        # values[14] + values[-15], # comment this
        # values[5] + values[-6], # comment this
        # values[25] + values[-26], # comment this
        # values[1] + values[-2], # comment this
        # values[2] + values[-3], # comment this
        # )
    return values[::1]


def compare(side_a, side_b):
    colors_differences = []
    for color_on_a, color_on_b in zip(side_a, side_b):
        color_value_differences = tuple(
            abs(a - b) or 1 for a, b in zip(color_on_a, color_on_b)
        )
        # if max(color_value_differences) > THRESHOLD:
        #     return BIG
        colors_differences.append(reduce(operator.mul, color_value_differences))

    side_difference = reduce(operator.mul, colors_differences)
    return side_difference


def retransform(pattern_side_num, most_similar_tile_data, most_similar_side_num):
    reverse = True
    if most_similar_side_num > 3:
        most_similar_side_num -= 4
        reverse = False

    if pattern_side_num > 3:
        pattern_side_num -= 4
        reverse = not reverse

    image = most_similar_tile_data.tile_image
    image = apply_transform(pattern_side_num, most_similar_side_num, reverse, image)
    return image

image = Image.open('./HWSYU5_H.png')
# image.show()

tiles = list(
    rank(tile, score_function) for tile in split_images(image, CROP_SIZE)
)

print(len(tiles))

BIG = (THRESHOLD**1000)**5
print('BIG: ', BIG)

pattern = tiles.pop(117)
pattern.data.tile_image.show()
pattern_side_number = 7
pattern_side = pattern.scores[pattern_side_number]
min_difference = BIG
for tile_num, tile in enumerate(tiles):
    side_number = 0
    for side_num, side in enumerate(tile.scores):
        difference = compare(pattern_side, side)
        print('.', end='')
        if difference < min_difference:
            # print(difference)
            min_difference = difference
            most_similar_side = side
            most_similar_tile = tile
            most_similar_tile_num = tile_num
            most_similar_side_num = side_number
#
#     if min_difference == BIG:
#         break
#
print()
print('difference:', min_difference)
print('most_similar_num:', most_similar_tile_num)
print('most_similar_side_num:', most_similar_side_num)
# most_similar_tile.data.tile_image.show()
nearest_tile = retransform(
    pattern_side_number,
    most_similar_tile.data,
    most_similar_side_num
)
nearest_tile.show()
#
#     del tiles[most_similar_tile_key]
#     print('tiles: ', len(tiles))
#     for side in most_similar_tile_key:
#         del sides[side]
#     print('sides: ', len(sides))
#
#     pattern_tile_data = most_similar_tile_data
