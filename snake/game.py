from apple import Apple
from area import Area
from snake import Snake

__author__ = 'matbur'


class Game(object):
    def __init__(self, xy=(18, 8), n=4, area_sign=' ', apple_sign='@', snake_sign='*'):
        self.area = Area(xy, area_sign)
        self.apple = Apple(xy, apple_sign)
        self.snake = Snake((n - 1, 0), (1, 0), n, xy, snake_sign)
        self.end = False
        self.reason = ''

        self.step()

    def dict(self):
        return dict(
            pos=self.apple.pos,
            dir=self.snake.dir,
            pts=self.apple.pts,
            len=len(self.snake.segments)
        )

    def step(self, new_dir=''):

        def is_in_snake():
            return self.apple.pos in self.snake.segments

        def eat_self():
            segments = self.snake.segments
            return len(set(segments)) != len(segments)

        last = self.snake.step(new_dir)

        if is_in_snake():
            self.apple.random()
            self.snake.segments.append(last)

        self.area.unset(*last)
        for segment in self.snake.segments:
            self.area.set(sign=self.snake.sign, *segment)
        self.area.set(sign=self.apple.sign, *self.apple.pos)

        if eat_self():
            self.end = True
            self.reason = 'You have been eaten by yourself!'

    def __str__(self):
        return str(self.area)
