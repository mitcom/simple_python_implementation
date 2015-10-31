__author__ = 'matbur'


class Snake(object):
    directions = {
        'right': {
            (0, 1): (-1, 0),
            (1, 0): (0, 1),
            (0, -1): (1, 0),
            (-1, 0): (0, -1)
        },
        'left': {
            (0, 1): (1, 0),
            (1, 0): (0, -1),
            (0, -1): (-1, 0),
            (-1, 0): (0, 1)
        }
    }

    def __init__(self, xy, dir_, n=4, max_=(18, 8), sign='*'):
        self.dir = dir_
        self.max_ = max_
        self.sign = sign

        self.segments = [self.mul_dir(xy, dir_, -n_ - 1) for n_ in xrange(n)]

    def mul_dir(self, a, b, n=1):
        return tuple((a[i] + b[i] * n) % v for i, v in enumerate(self.max_))

    def step(self, new_dir=''):
        first = self.segments[0]
        if new_dir:
            self.dir = self.directions[new_dir][self.dir]
        self.segments.insert(0, self.mul_dir(first, self.dir))
        return self.segments.pop()

    def __str__(self):
        return self.sign
