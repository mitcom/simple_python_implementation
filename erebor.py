import operator
from collections import namedtuple
from functools import reduce
from pprint import pprint
from typing import Sequence, Iterator, Tuple, Any, Callable, List

from PIL import Image


CROP_SIZE = (60, 60)
CROP_X, CROP_Y = CROP_SIZE
THRESHOLD = 25  # max value difference between closest part per one channel (RGB)


TileData = namedtuple('TileData', ['side_scores', 'frames', 'tile'])


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


class RotatedKeysDict(dict):
    """
    Like dict, but for keys such: '(x,y,z)' generates also keys '(y,z,x)'
    and '(z,x,y)' then sets the same value. Also while deleting one key,
    the generated keys are deleted too. Please be careful with popping values,
    then it behaves like regular dict.

    >>> rd = RotatedKeysDict()
    >>> rd['x','y'] = 'some_value'
    >>> rd
    {('x', 'y'): 'some_value', ('y', 'x'): 'some_value'}
    >>> del rd['y', 'x']
    >>> rd
    {}
    """

    def __init__(self, *args, **kwargs):
        temporary_dict = dict(*args, *kwargs)
        for key, value in temporary_dict.items():
            self[key] = value

    @staticmethod
    def _rotate_keys(key):
        import collections
        if not isinstance(key, str) and isinstance(key, collections.Iterable):
            head, *tail = key
            for _ in key:
                yield (head, *tail)
                head, *tail = *tail, head
        else:
            yield key

    def __setitem__(self, key, value):
        for rotated_key in self._rotate_keys(key):
            super().__setitem__(rotated_key, value)

    def __delitem__(self, key):
        for rotated_key in self._rotate_keys(key):
            super().__delitem__(rotated_key)


def split_images(source: Image, crop_size: Tuple[int, int]) -> Iterator:
    source_width, source_height = source.size
    crop_width, crop_height = crop_size
    for row in range(0, source_height, crop_height):
        for cell in range(0, source_width, crop_width):
            crop_window = (cell, row, cell+crop_width, row+crop_height)
#             print('({}, {})({}, {})'.format(*crop_window))
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
    return TileData(
        (left_rank, top_rank, right_rank, bottom_rank),
        (left, top, right, bottom),
        image,
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
    return (
        values[0] + values[-1],
        values[9] + values[-10],
        values[10] + values[-11],
        values[29] + values[-30], # comment this
        values[20] + values[-21],
        values[14] + values[-15], # comment this
        values[5] + values[-6], # comment this
        values[25] + values[-26], # comment this
        values[1] + values[-2], # comment this
        values[2] + values[-3], # comment this
        )


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


def retransform(pattern_frame, pattern_side, most_similar_tile_data, most_similar_side):
    for side_number, side in enumerate(most_similar_tile_data.side_scores):
        if side == most_similar_side:
            break
    # print(side_number)
    frame = most_similar_tile_data.frames[side_number]
    forward_difference = sum(
        abs(pp[0] - p[0]) + abs(pp[1] - p[1]) + abs(pp[2] - p[2])  # r, g, b
        for pp, p in zip(pattern_frame[::10], frame[::10])  # skip many pixels
    )
    frame = frame[::-1]
    backward_difference = sum(
        abs(pp[0] - p[0]) + abs(pp[1] - p[1]) + abs(pp[2] - p[2])  # r, g, b
        for pp, p in zip(pattern_frame[::10], frame[::10])  # skip many pixels
    )

    reverse = forward_difference > backward_difference
    image = most_similar_tile_data.tile
    image = apply_transform(pattern_side, side_number, reverse, image)
    return image

image = Image.open('./HWSYU5_H.png')

tiles = (
    rank(tile, score_function) for tile in split_images(image, CROP_SIZE)
)

tiles = RotatedKeysDict({
    ranks: TileData(ranks, frames, tile)
    for ranks, frames, tile in tiles
})

print('tiles: ', len(tiles))


BIG = (THRESHOLD**10)**5
print('BIG: ', BIG)
it = iter(tiles)
first_tile_key = next(it)
first_tile_data = tiles[first_tile_key]
first_tile_data.tile.show()
del tiles[first_tile_key]
sides = {
    first_side: (first_side, *rest_side)
    for first_side, *rest_side in tiles
}
print('sides: ', len(sides))


side_number = 0
pattern_tile_data = first_tile_data
for tile in tiles.copy():
    if tile not in tiles:
        continue
    min_difference = BIG
    pattern_tile_side = pattern_tile_data.side_scores[side_number]
    for side in sides:
        difference = compare(pattern_tile_side, side)
        print(difference, end=', ')
        if difference < min_difference:
            min_difference = difference
            most_similar_side = side

    if min_difference == BIG:
        break

    print('difference:', min_difference)
    most_similar_tile_key = sides[most_similar_side]
    most_similar_tile_data = tiles[most_similar_tile_key]
    nearest_tile = retransform(
        pattern_tile_data.frames[side_number],
        side_number,
        most_similar_tile_data,
        most_similar_side
    )
    nearest_tile.show()

    del tiles[most_similar_tile_key]
    print('tiles: ', len(tiles))
    for side in most_similar_tile_key:
        del sides[side]
    print('sides: ', len(sides))

    pattern_tile_data = most_similar_tile_data
