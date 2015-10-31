__author__ = 'matbur'


class Area(object):
    def __init__(self, xy=(18, 8), sign=' '):
        self.sign = sign
        self.x, self.y = xy
        self.tab = self.create()

    def create(self):
        return [[self.sign] * self.x for _ in xrange(self.y)]

    def set(self, x, y, sign):
        self.tab[y][x] = sign

    def unset(self, x, y):
        self.tab[y][x] = self.sign

    def __call__(self, x, y):
        return self.tab[y][x]

    def __str__(self):
        out = []
        for row in self.tab:
            out.append('.'.join(row))
        return '\n'.join(out)
