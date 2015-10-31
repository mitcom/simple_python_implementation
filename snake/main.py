#!/usr/bin/python

from apple import Apple
from area import Area
from game import Game
from snake import Snake

__author__ = 'matbur'


def main():
    game = Game((18, 10))
    # game = Game((30, 20))
    map_ = {
        'w': '',
        'a': 'left',
        'd': 'right'
    }
    try:
        while not game.end:
            print game
            print game.dict()
            dir_ = raw_input() or 'w'
            if dir_ in map_:
                game.step(map_[dir_])
        else:
            print game.reason
    except (KeyboardInterrupt, EOFError):
        pass


if __name__ == '__main__':
    main()
