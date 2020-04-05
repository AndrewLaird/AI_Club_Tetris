# Imports
import sys
import random
import pygame
from datetime import datetime

# Configurations (USER)
SIZE_SCALE = 1
SPEED_DEFAULT = 750  # 750 MS
SPEED_SCALE_ENABLED = True  # game gets faster with more points?
SPEED_SCALE = 1.5  # speed = max(50, 750 - SCORE * SPEED_SCALE)
DISPLAY_PREDICTION = True

COLORS = {
    # Display
    "BACKGROUND_BLACK": "000000",
    "BACKGROUND_DARK": "021c2d",
    "BACKGROUND_LIGHT": "00263f",
    "TRIANGLE_GRAY": "efe6ff",
    "WHITE": "ffffff",
    # Tetris pieces
    "TILE_LINE": "ffb900",
    "TILE_L": "2753f1",
    "TILE_L_REVERSED": "f7ff00",
    "TILE_S": "ff6728",
    "TILE_S_REVERSED": "11c5bf",
    "TILE_T": "ae81ff",
    "TILE_CUBE": "e94659"
}

# Configurations (SYSTEM)
GRID_ROW_COUNT = 20
GRID_COL_COUNT = 10

SCREEN_WIDTH = int(360 / 0.6 * SIZE_SCALE) 
SCREEN_HEIGHT = int(720 * SIZE_SCALE)

MAX_FPS = 60

MULTI_SCORE_ALGORITHM = lambda a: 2 ** a;

TILES = ["LINE", "L", "L_REVERSED", "S", "S_REVERSED", "T", "CUBE"]
TILE_SHAPES = {
    "LINE": [[1, 1, 1, 1]],
    "L": [[0, 0, 2],
          [2, 2, 2]],
    "L_REVERSED": [[3, 0, 0],
                   [3, 3, 3]],
    "S": [[0, 4, 4],
          [4, 4, 0]],
    "S_REVERSED": [[5, 5, 0],
                   [0, 5, 5]],
    "T": [[6, 6, 6],
          [0, 6, 0]],
    "CUBE": [[7, 7],
             [7, 7]]
}


def getColorTuple(colorHex):
    colorHex = colorHex.replace("#", "")
    return tuple(int(colorHex[i:i + 2], 16) for i in (0, 2, 4))


class TetrisGame:
    
    def __init__(self):
        self.log("Initializing system...")
        pygame.init()
        
        self.screen = pygame.display.set_mode(size=(SCREEN_WIDTH, SCREEN_HEIGHT))
        self.log("Screen size set to: (" + str(SCREEN_WIDTH) + ", " + str(SCREEN_HEIGHT) + ")")

        # PyGame configurations
        pygame.event.set_blocked(pygame.MOUSEMOTION)
        
        # Initialize game-related attributes
        self.init_game()
        
        # Setup callback functions
        self.on_score_changed_callbacks = []
        
        # Start the game
        self.start()
        
    def init_game(self):
        self.log("Initializing game...")
        self.active = True
        self.paused = False
        
        # Board is an 2D array of integers
        self.reset_board()
        
        # Calculate grid size
        self.grid_size = int(SCREEN_HEIGHT / GRID_ROW_COUNT)
        self.log("Tetris grid size calculated to: " + str(self.grid_size))
        
        # Keyboard integration
        self.key_actions = {
            "ESCAPE": self.toggle_pause,
            "LEFT": lambda: self.move_tile(-1),
            "RIGHT": lambda: self.move_tile(1),
            "DOWN": lambda: self.drop(False),
            "SPACE": lambda: self.drop(True),
            "UP": self.rotate_tile
        }
        
        # Tile generation
        self.generate_tile_bank()
        self.spawn_tile()
        
        # Score
        self.score = 0
    
    # Start the UI loop
    def start(self):
        self.active = True
        self.paused = False
        self.tick = 0
        
        pygame.time.set_timer(pygame.USEREVENT + 1, SPEED_DEFAULT if not SPEED_SCALE_ENABLED else int(max(50, SPEED_DEFAULT - self.score * SPEED_SCALE)))
        clock = pygame.time.Clock()
        
        while True:
            self.update(clock)
            self.draw()
            self.tick += 1

    # Called every tick
    def update(self, clock):
        for event in pygame.event.get():
            if event.type == pygame.USEREVENT + 1:
                self.drop()
            elif event.type == pygame.QUIT:
                self.quit()
            elif event.type == pygame.KEYDOWN:
                for key in self.key_actions:
                    if event.key == eval("pygame.K_" + key):
                        self.key_actions[key]()
            
        clock.tick(MAX_FPS)
    
    # Called every tick after update
    def draw(self):
        # Background layer
        self.screen.fill(getColorTuple(COLORS.get("BACKGROUND_BLACK")))
        # Layered background layer
        for a in range(GRID_COL_COUNT):
            color = getColorTuple(COLORS.get("BACKGROUND_DARK" if a % 2 == 0 else "BACKGROUND_LIGHT"))
            pygame.draw.rect(self.screen, color, (a * self.grid_size, 0, self.grid_size, SCREEN_HEIGHT))  # x, y, width, height
        
        # Tetris (tile) layer
        # Draw board first
        self.draw_tiles(self.board)
        # Draw hypothesized tile
        if DISPLAY_PREDICTION:
            self.draw_tiles(self.tile_shape, (self.tile_x, self.get_current_collision_offset()), True)
        # Draw current tile
        self.draw_tiles(self.tile_shape, (self.tile_x, self.tile_y))

#         self.draw_tiles(TILE_SHAPES.get(self.get_next_tile()), (self.tile_x, 0), True)

        pygame.display.update()
    
    # Draw the tetris tiles
    def draw_tiles(self, matrix, offsets=(0, 0), outline_only=False):
        for y, row in enumerate(matrix):
            for x, val in enumerate(row):
                if val == 0:
                    continue
                coord_x = (offsets[0] + x) * self.grid_size
                coord_y = (offsets[1] + y) * self.grid_size
                # Draw rectangle
                if(not outline_only):
                    pygame.draw.rect(self.screen,
                                     getColorTuple(COLORS.get("TILE_" + TILES[val - 1])),
                                     (coord_x, coord_y, self.grid_size, self.grid_size))
                    pygame.draw.rect(self.screen,
                                     getColorTuple(COLORS.get("BACKGROUND_BLACK")),
                                     (coord_x, coord_y, self.grid_size, self.grid_size), 1)
                    # Draw highlight triangle
                    offset = int(self.grid_size / 10)
                    pygame.draw.polygon(self.screen, getColorTuple(COLORS.get("TRIANGLE_GRAY")), ((coord_x + offset, coord_y + offset),
                                        (coord_x + 3 * offset, coord_y + offset), (coord_x + offset, coord_y + 3 * offset)))
                else:
                    # Outline-only for prediction location
                    pygame.draw.rect(self.screen,
                                     getColorTuple(COLORS.get("TILE_" + TILES[val - 1])),
                                     (coord_x + 1, coord_y + 1, self.grid_size - 2, self.grid_size - 2), 1)
                
    def spawn_tile(self):
        if not self.tile_bank:
            self.generate_tile_bank() 
        self.tile = self.tile_bank.pop(0)
        self.tile_shape = TILE_SHAPES.get(self.tile)[:]
        self.tile_x = int(GRID_COL_COUNT / 2 - len(self.tile_shape[0]) / 2)
        self.tile_y = 0
        
        self.log("Spawning a new " + self.tile + " tile!")
        if self.check_collision(self.tile_shape, (self.tile_x, self.tile_y)):
            self.gameover = True
            self.paused = True
    
    def get_next_tile(self):
        if not self.tile_bank:
            self.generate_tile_bank()
        return self.tile_bank[0]
    
    # Drop the current tile by 1 grid
    def drop(self, instant=False):
        if not self.active or self.paused:
            return
        # Drop the tile
        if instant:
            self.tile_y = self.get_current_collision_offset()
        else:            
            self.tile_y += 1
        # If no collision happen, skip
        if not self.check_collision(self.tile_shape, (self.tile_x, self.tile_y)):
            return
        # Collided! Add tile to board, spawn new tile, and calculate scores
        self.add_tile_to_board()
        self.calculate_scores()
        self.spawn_tile()
    
    def move_tile(self, delta):
        if not self.active or self.paused:
            return
        new_x = self.tile_x + delta
        # Clamping
        new_x = max(0, min(new_x, GRID_COL_COUNT - len(self.tile_shape[0])))
        # Cannot "override" blocks AKA cannot move when it is blocked
        if self.check_collision(self.tile_shape, (new_x, self.tile_y)):
            return
        self.tile_x = new_x;
    
    def rotate_tile(self):
        if not self.active or self.paused:
            return
        new_shape = list(zip(*reversed(self.tile_shape)))
        # If collide, disallow rotation
        if self.check_collision(new_shape, (self.tile_x, self.tile_y)):
            return
        self.tile_shape = new_shape
        
    # Calculate score (called after every collision)
    def calculate_scores(self):
        score_count = 0
        row = 0
        while True:
            if(row >= len(self.board)):
                break
            if 0 in self.board[row]:
                row += 1
                continue
            # Delete the "filled" row
            del self.board[row]
            # Insert empty row at top
            self.board.insert(0, [0] * GRID_COL_COUNT)
            score_count += 1
        # If cleared nothing, do nothing
        if(score_count == 0):
            return
        # Calculate total score based on algorithm
        total_score = MULTI_SCORE_ALGORITHM(score_count)
        # Callback
        for callback in self.on_score_changed_callbacks:
            callback(self.score, self.score + total_score)

        self.log("Cleared " + str(score_count) + " rows with score " + str(total_score), "I")
        self.score += total_score
    
    def get_current_collision_offset(self):
        offset_y = self.tile_y
        while not self.check_collision(self.tile_shape, (self.tile_x, offset_y)):
            offset_y += 1
        return offset_y - 1
    
    def check_collision(self, tile_shape, offsets):
        for cy, row in enumerate(tile_shape):
            for cx, val in enumerate(row):
                if val == 0:
                    continue
                try:
                    if self.board[cy + offsets[1]][cx + offsets[0]]:
                        return True
                except IndexError:
                    return True
        return False
    
    def add_tile_to_board(self):
        for cy, row in enumerate(self.tile_shape):
            for cx, val in enumerate(row):
                if val == 0:
                    continue
                self.board[cy + self.tile_y - 1][cx + self.tile_x] = val
    
    def reset(self):
        self.init_game()
    
    def reset_board(self):
        self.board = [[0] * GRID_COL_COUNT for _ in range(GRID_ROW_COUNT)]
    
    def toggle_pause(self):
        self.paused = not self.paused

    def quit(self):
        sys.exit()
    
    def generate_tile_bank(self):
        self.tile_bank = list(TILE_SHAPES.keys())
        random.shuffle(self.tile_bank)
    
    def print_board(self):
        self.log("Printing debug board")
        for i, row in enumerate(self.board):
            print("{:02d}".format(i), row)
    
    def log(self, message, level="D"):
        current_time = datetime.now().strftime("%H:%M:%S:%f")[:-3]
        print("[" + level + "] " + current_time + " >> " + message)
    
    # Integration with neural networks
    # Template: on_score_changed(original_score, new_score)
    def subscribe_on_score_changed(self, callback):
        self.on_score_changed_callbacks.append(callback)


if __name__ == "__main__":
    print("Hello world!")
    TetrisGame()
