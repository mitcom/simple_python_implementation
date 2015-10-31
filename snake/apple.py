from random import randrange

__author__ = 'matbur'


class Apple(object):
    pos = 0, 0
    pts = -1

    def __init__(self, max_=(18, 8), sign='@'):
        self.sign = sign
        self.max_ = max_
        self.random()

    def random(self):
        self.pos = tuple(randrange(0, i) for i in self.max_)
        self.pts += 1

    def __str__(self):
        return self.sign
