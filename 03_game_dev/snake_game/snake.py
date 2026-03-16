import random

UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)


class Snake:
    def __init__(self, pos):
        self.positions = [pos]
        self.direction = RIGHT
        self.grow_pending = 0

    def head(self):
        return self.positions[0]

    def turn(self, dir):
        # prevent reversing
        if (dir[0] * -1, dir[1] * -1) == self.direction:
            return
        self.direction = dir

    def move(self, grid_w=None, grid_h=None):
        x, y = self.head()
        dx, dy = self.direction
        new_x = x + dx
        new_y = y + dy
        if grid_w is not None and grid_h is not None:
            new_x %= grid_w
            new_y %= grid_h
        new = (new_x, new_y)
        self.positions.insert(0, new)
        if self.grow_pending > 0:
            self.grow_pending -= 1
        else:
            self.positions.pop()

    def grow(self, amount=1):
        self.grow_pending += amount

    def collided_with_self(self):
        return self.head() in self.positions[1:]


class Food:
    def __init__(self, grid_w, grid_h, snake_positions):
        self.grid_w = grid_w
        self.grid_h = grid_h
        self.position = self.spawn(snake_positions)

    def spawn(self, snake_positions):
        choices = [
            (x, y)
            for x in range(self.grid_w)
            for y in range(self.grid_h)
            if (x, y) not in snake_positions
        ]
        if not choices:
            return None
        return random.choice(choices)
