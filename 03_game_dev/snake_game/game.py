import pygame
import sys
from snake import Snake, Food, UP, DOWN, LEFT, RIGHT


class Game:
    def __init__(self, cell_size=20, grid_w=30, grid_h=20):
        pygame.init()
        self.cell = cell_size
        self.grid_w = grid_w
        self.grid_h = grid_h
        self.width = grid_w * cell_size
        self.height = grid_h * cell_size
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('Snake')
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 24)
        self.reset()

    def reset(self):
        start = (self.grid_w // 2, self.grid_h // 2)
        self.snake = Snake(start)
        self.food = Food(self.grid_w, self.grid_h, self.snake.positions)
        self.score = 0
        self.game_over = False
        self.speed = 10

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                self.snake.turn(UP)
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                self.snake.turn(DOWN)
            elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                self.snake.turn(LEFT)
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                self.snake.turn(RIGHT)
            elif event.key == pygame.K_r:
                self.reset()
            elif event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

    def update(self):
        if self.game_over:
            return
        # move with wrapping at borders
        self.snake.move(self.grid_w, self.grid_h)
        # self collision
        if self.snake.collided_with_self():
            self.game_over = True
            return
        # food
        if self.food.position and self.snake.head() == self.food.position:
            self.snake.grow()
            self.score += 1
            self.food = Food(self.grid_w, self.grid_h, self.snake.positions)

    def draw_grid(self):
        for x in range(self.grid_w):
            for y in range(self.grid_h):
                rect = pygame.Rect(x * self.cell, y * self.cell, self.cell, self.cell)
                pygame.draw.rect(self.screen, (30, 30, 30), rect, 1)

    def draw(self):
        self.screen.fill((0, 0, 0))
        # draw snake
        for i, (x, y) in enumerate(self.snake.positions):
            rect = pygame.Rect(x * self.cell, y * self.cell, self.cell, self.cell)
            color = (0, 200, 0) if i == 0 else (0, 150, 0)
            pygame.draw.rect(self.screen, color, rect)
        # draw food
        if self.food.position:
            fx, fy = self.food.position
            rect = pygame.Rect(fx * self.cell, fy * self.cell, self.cell, self.cell)
            pygame.draw.rect(self.screen, (200, 0, 0), rect)
        # score
        score_surf = self.font.render(f'Score: {self.score}', True, (255, 255, 255))
        self.screen.blit(score_surf, (5, 5))
        if self.game_over:
            go_surf = self.font.render('Game Over - Press R to restart', True, (255, 50, 50))
            self.screen.blit(go_surf, (self.width//2 - go_surf.get_width()//2, self.height//2))
        pygame.display.flip()

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                self.handle_event(event)
            self.update()
            self.draw()
            self.clock.tick(self.speed)
