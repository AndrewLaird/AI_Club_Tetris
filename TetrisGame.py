# Imports
import sys
import random
import pygame
import copy
import threading
from datetime import datetime

# Configurations (USER)
SIZE_SCALE = 1
SPEED_DEFAULT = 750  # 750 MS
SPEED_SCALE_ENABLED = True  # game gets faster with more points?
SPEED_SCALE = 0.05  # speed = max(50, 750 - SCORE * SPEED_SCALE)
DISPLAY_PREDICTION = True
HAS_DISPLAY = True
MIN_DEBUG_LEVEL = 3

FONT_NAME = "Consolas"

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

MESSAGES = {
    # Display
    "TITLE": "Tetris",
    "CONTROLS": "Left/Right - Move tile\nUp - Rotate tile\nDown - Fast drop\nSpace - Insta-drop\nEscape - Play/Pause\nTab - Swap next tile",
    "SCORE": "Score: {score} (x{lines})",
    "HIGH_SCORE": "High Score: {}",
    "SPEED": "Speed: {}ms",
    "NEXT_TILE": "Next tile: {}",
}

# Configurations (SYSTEM)
GRID_ROW_COUNT = 20
GRID_COL_COUNT = 10

SCREEN_WIDTH = int(360 / 0.6 * SIZE_SCALE)
SCREEN_HEIGHT = int(720 * SIZE_SCALE)
MAX_FPS = 30

########################
# Score Configurations #
########################
MULTI_SCORE_ALGORITHM = lambda lines_cleared: 5 ** lines_cleared;
PER_STEP_SCORE_GAIN = 0.5

######################
# STEP Configuration #
######################
ALWAYS_DRAW = True
STEP_ACTION = True
STEP_DEBUG = False

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
        if HAS_DISPLAY:
            self.log("Initializing system...", 3)
            pygame.init()
            pygame.font.init()

            self.screen = pygame.display.set_mode(size=(SCREEN_WIDTH, SCREEN_HEIGHT))
            self.log("Screen size set to: (" + str(SCREEN_WIDTH) + ", " + str(SCREEN_HEIGHT) + ")", 2)
            self.obs_size = GRID_ROW_COUNT*GRID_COL_COUNT # would be + 1 if you are using the next block

            # PyGame configurations
            pygame.event.set_blocked(pygame.MOUSEMOTION)

            # Initialize game-related attributes
            self.init_game()

            # Setup callback functions
            self.on_score_changed_callbacks = []

        # High-score
        self.high_score = 0
        self.score = 0

        if HAS_DISPLAY:
            # Start the game
            self.start()

    def init_game(self):
        self.log("Initializing game...", 2)
        self.active = True
        self.paused = False

        # Board is an 2D array of integers
        self.reset_board()

        # Calculate grid size
        self.grid_size = int(SCREEN_HEIGHT / GRID_ROW_COUNT)
        self.log("Tetris grid size calculated to: " + str(self.grid_size), 2)

        # Keyboard integration
        # http://thepythongamebook.com/en:glossary:p:pygame:keycodes
        self.key_actions = {
            "ESCAPE": self.toggle_pause,
            "LEFT": lambda: self.move_tile(-1),
            "RIGHT": lambda: self.move_tile(1),
            "DOWN": lambda: self.drop(False),
            "SPACE": lambda: self.drop(True),
            "UP": self.rotate_tile,
            "TAB": self.swap_tile
        }

        # Tile generation
        self.generate_tile_bank()
        self.spawn_tile()

        # Score
        self.score = 0
        self.lines = 0

    # Start the UI loop
    def start(self):
        self.active = True
        self.paused = False

        pygame.time.set_timer(pygame.USEREVENT + 1, SPEED_DEFAULT if not SPEED_SCALE_ENABLED else int(
            max(50, SPEED_DEFAULT - self.score * SPEED_SCALE)))
        clock = pygame.time.Clock()

        def loop():
            while True:
                # Game control: step or auto?
                if (STEP_ACTION):
                    # Command-line debugging
                    if STEP_DEBUG:
                        cmd = input("Command:")
                        if cmd == "q":
                            break
                        elif cmd == "d":
                            self.render()
                        elif cmd == "p":
                            self.print_board()
                        else:
                            try:
                                cmd = int(cmd)
                            except:
                                continue
                            self.step(cmd)
                else:
                    # Auto
                    self.update()
                # Drawing of the UI
                if not STEP_ACTION or ALWAYS_DRAW:
                    self.draw()
                clock.tick(MAX_FPS)

        # Use multi-threading?
        if STEP_ACTION and not STEP_DEBUG:
            th = threading.Thread(target=loop, daemon=False)
            th.start()
        else:
            loop()

    # Called every tick
    def update(self):
        for event in pygame.event.get():
            if event.type == pygame.USEREVENT + 1:
                self.drop()
            elif event.type == pygame.QUIT:
                self.quit()
            elif event.type == pygame.KEYDOWN:
                for key in self.key_actions:
                    if event.key == eval("pygame.K_" + key):
                        self.key_actions[key]()

    # Called every tick after update
    def draw(self):
        # Background layer
        self.screen.fill(getColorTuple(COLORS.get("BACKGROUND_BLACK")))

        ################
        # Tetris Board #
        ################

        # Layered background layer
        for a in range(GRID_COL_COUNT):
            color = getColorTuple(COLORS.get("BACKGROUND_DARK" if a % 2 == 0 else "BACKGROUND_LIGHT"))
            pygame.draw.rect(self.screen, color,
                             (a * self.grid_size, 0, self.grid_size, SCREEN_HEIGHT))  # x, y, width, height

        # Tetris (tile) layer
        # Draw board first
        self.draw_tiles(self.board)
        # Draw hypothesized tile
        if DISPLAY_PREDICTION:
            self.draw_tiles(self.tile_shape, (self.tile_x, self.get_current_collision_offset()), True)
        # Draw current tile
        self.draw_tiles(self.tile_shape, (self.tile_x, self.tile_y))

        #################
        # Message Board #
        #################
        # Coordinates calculations
        margin = 20  # 20 pixels margin
        text_x_start = GRID_COL_COUNT * self.grid_size + margin
        text_y_start = margin

        # Title
        message = MESSAGES.get("TITLE")
        if not self.active:
            message = "Game Over"
        elif self.paused:
            message = "= PAUSED ="
        text_image = pygame.font.SysFont(FONT_NAME, 32).render(message, False, getColorTuple(COLORS.get("WHITE")))
        self.screen.blit(text_image, (text_x_start, text_y_start))
        text_y_start = 60

        # Controls
        for msg in MESSAGES.get("CONTROLS").split("\n"):
            text_image = pygame.font.SysFont(FONT_NAME, 16).render(msg, False, getColorTuple(COLORS.get("WHITE")))
            self.screen.blit(text_image, (text_x_start, text_y_start))
            text_y_start += 20
        text_y_start += 10

        # Score
        text_image = pygame.font.SysFont(FONT_NAME, 16).render(
            MESSAGES.get("SCORE").format(score=self.score, lines=self.lines), False, getColorTuple(COLORS.get("WHITE")))
        self.screen.blit(text_image, (text_x_start, text_y_start))
        text_y_start += 20

        # High Score
        text_image = pygame.font.SysFont(FONT_NAME, 16).render(
            MESSAGES.get("HIGH_SCORE").format(self.score if self.score > self.high_score else self.high_score), False,
            getColorTuple(COLORS.get("WHITE")))
        self.screen.blit(text_image, (text_x_start, text_y_start))
        text_y_start += 20

        # Speed        
        speed = SPEED_DEFAULT if not SPEED_SCALE_ENABLED else int(max(50, SPEED_DEFAULT - self.score * SPEED_SCALE))
        text_image = pygame.font.SysFont(FONT_NAME, 16).render(MESSAGES.get("SPEED").format(speed), False,
                                                               getColorTuple(COLORS.get("WHITE")))
        self.screen.blit(text_image, (text_x_start, text_y_start))
        text_y_start += 20

        # Next tile
        text_image = pygame.font.SysFont(FONT_NAME, 16).render(MESSAGES.get("NEXT_TILE").format(self.get_next_tile()),
                                                               False, getColorTuple(COLORS.get("WHITE")))
        self.screen.blit(text_image, (text_x_start, text_y_start))
        text_y_start += 20

        self.draw_next_tile((text_x_start, text_y_start));
        text_y_start += 60

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
                if (not outline_only):
                    pygame.draw.rect(self.screen,
                                     getColorTuple(COLORS.get("TILE_" + TILES[val - 1])),
                                     (coord_x, coord_y, self.grid_size, self.grid_size))
                    pygame.draw.rect(self.screen,
                                     getColorTuple(COLORS.get("BACKGROUND_BLACK")),
                                     (coord_x, coord_y, self.grid_size, self.grid_size), 1)
                    # Draw highlight triangle
                    offset = int(self.grid_size / 10)
                    pygame.draw.polygon(self.screen, getColorTuple(COLORS.get("TRIANGLE_GRAY")),
                                        ((coord_x + offset, coord_y + offset),
                                         (coord_x + 3 * offset, coord_y + offset),
                                         (coord_x + offset, coord_y + 3 * offset)))
                else:
                    # Outline-only for prediction location
                    pygame.draw.rect(self.screen,
                                     getColorTuple(COLORS.get("TILE_" + TILES[val - 1])),
                                     (coord_x + 1, coord_y + 1, self.grid_size - 2, self.grid_size - 2), 1)

    def draw_next_tile(self, offsets):
        size = int(self.grid_size * 0.75)
        for y, row in enumerate(TILE_SHAPES.get(self.get_next_tile())):
            for x, val in enumerate(row):
                if val == 0:
                    continue
                coord_x = offsets[0] + x * size
                coord_y = offsets[1] + y * size
                # Draw rectangle
                pygame.draw.rect(self.screen, getColorTuple(COLORS.get("TILE_" + TILES[val - 1])),
                                 (coord_x, coord_y, size, size))
                pygame.draw.rect(self.screen, getColorTuple(COLORS.get("BACKGROUND_BLACK")),
                                 (coord_x, coord_y, size, size), 1)
                # Draw highlight triangle
                offset = int(size / 10)
                pygame.draw.polygon(self.screen, getColorTuple(COLORS.get("TRIANGLE_GRAY")),
                                    ((coord_x + offset, coord_y + offset),
                                     (coord_x + 3 * offset, coord_y + offset),
                                     (coord_x + offset, coord_y + 3 * offset)))

    def spawn_tile(self):
        self.tile = self.get_next_tile(pop=True)
        self.tile_shape = TILE_SHAPES.get(self.tile)[:]
        self.tile_x = int(GRID_COL_COUNT / 2 - len(self.tile_shape[0]) / 2)
        self.tile_y = 0

        self.log("Spawning a new " + self.tile + " tile!", 1)
        if self.check_collision(self.tile_shape, (self.tile_x, self.tile_y)):
            self.active = False
            self.paused = True

    def get_next_tile(self, pop=False):
        if not self.tile_bank:
            self.generate_tile_bank()
        return self.tile_bank[0] if not pop else self.tile_bank.pop(0)

    # Drop the current tile by 1 grid
    def drop(self, instant=False):
        if not self.active or self.paused:
            return
        # Drop the tile
        if instant:
            destination = self.get_current_collision_offset()
            self.score += PER_STEP_SCORE_GAIN * (destination - self.tile_y)
            self.tile_y = destination
        else:
            self.tile_y += 1
            self.score += PER_STEP_SCORE_GAIN

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
        self.tile_x = new_x

    def rotate_tile(self):
        if not self.active or self.paused:
            return
        new_shape = list(zip(*reversed(self.tile_shape)))
        temp_x = self.tile_x
        # Out of range detection
        if self.tile_x + len(new_shape[0]) > GRID_COL_COUNT:
            temp_x = GRID_COL_COUNT - len(new_shape[0])
            # If collide, disallow rotation
        if self.check_collision(new_shape, (temp_x, self.tile_y)):
            return
        self.tile_x = temp_x
        self.tile_shape = new_shape

    def swap_tile(self):
        if not self.active or self.paused:
            return
        tile = self.get_next_tile(True)
        self.tile_bank.insert(0, self.tile)

        self.tile = tile
        self.tile_shape = TILE_SHAPES.get(self.tile)[:]

        # Out of range detection
        if self.tile_x + len(self.tile_shape[0]) > GRID_COL_COUNT:
            self.tile_x = GRID_COL_COUNT - len(self.tile_shape[0])

    # Calculate score (called after every collision)
    def calculate_scores(self):
        score_count = 0
        row = 0
        while True:
            if row >= len(self.board):
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
        if score_count == 0:
            return
        # Calculate total score based on algorithm
        total_score = MULTI_SCORE_ALGORITHM(score_count)
        # Callback
        for callback in self.on_score_changed_callbacks:
            callback(self.score, self.score + total_score)

        self.score += total_score
        self.lines += score_count
        self.log("Cleared " + str(score_count) + " rows with score " + str(total_score), 3)
        pygame.time.set_timer(pygame.USEREVENT + 1, SPEED_DEFAULT if not SPEED_SCALE_ENABLED else int(
            max(50, SPEED_DEFAULT - self.score * SPEED_SCALE)))

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
        self.log("Resetting game...", 2)
        # Calculate high score
        if self.high_score < self.score:
            self.high_score = self.score
        # Reset
        self.init_game()
        return self.board[:]

    def reset_board(self):
        self.board = [[0] * GRID_COL_COUNT for _ in range(GRID_ROW_COUNT)]

    def toggle_pause(self):
        if not self.active:
            self.reset()
            self.paused = False
            return
        self.paused = not self.paused
        self.log(("Pausing" if self.paused else "Resuming") + " game...", 2)

    def quit(self):
        sys.exit()

    def generate_tile_bank(self):
        self.tile_bank = list(TILE_SHAPES.keys())
        random.shuffle(self.tile_bank)

    def print_board(self):
        self.log("Printing debug board", 10)
        for i, row in enumerate(self.get_board_with_current_tile()):
            print("{:02d}".format(i), row)

    def log(self, message, level):
        if MIN_DEBUG_LEVEL > level:
            return
        current_time = datetime.now().strftime("%H:%M:%S:%f")[:-3]
        print(f"[{level}] {current_time} >> {message}")

    ################################################
    # Integration with neural networks (Interface) #
    ################################################
    # On-score-changed event handler
    # Template: on_score_changed(original_score, new_score)
    def subscribe_on_score_changed(self, callback):
        self.on_score_changed_callbacks.append(callback)

    def get_board_with_current_tile(self):
        board = copy.deepcopy(self.board)
        for y, row in enumerate(self.tile_shape):
            for x, val in enumerate(row):
                if val == 0:
                    continue
                board[y + self.tile_y][x + self.tile_x] = val
        return board

    def render(self):
        self.draw()

    # Action = index of { NOTHING, L, R, 2L, 2R, ROTATE, SWAP, FAST_FALL }
    def step(self, action=0):
        # Update UI
        if HAS_DISPLAY:
            pygame.event.get()
        # Obtain previous score
        previous_score = self.score
        # Move action
        if action in [1, 2, 3, 4]:
            self.move_tile((-1 if action in [1, 3] else 1) * (1 if action in [1, 2] else 2))
        # Rotate
        elif action == 5:
            self.rotate_tile()
        # Swap
        elif action == 6:
            self.swap_tile()
        # Fast fall
        elif action == 7:
            self.drop()

        # Continue by 1 step
        self.drop()

        # >> Returns: board matrix, score change, is-game-over, next piece
        return self.get_board_with_current_tile(), self.score - previous_score, not self.active, self.get_next_tile()


if __name__ == "__main__":
    HAS_DISPLAY = True
    print("Hello world!")
    game = TetrisGame()
    games = 0
    if STEP_ACTION and not STEP_DEBUG:
        while True:
            # if random.randrange(10000) == 0:
            #    game.draw()
            if game.active:
                game.step()
            else:
                game.reset()
                games += 1
                print(games)
    print("Goodbye world!")
