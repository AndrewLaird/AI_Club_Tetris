import TetrisGame, TetrisUtils
from TetrisSettings import *
import time
import json

buffer_count = 0
buffer_curr = 0
buffer_max = 1000
buffer = {}


def json_write(state, action, reward, next_state):
    global buffer, buffer_count, buffer_curr, buffer_max
    if buffer_curr >= buffer_max:
        buffer_curr = 0
        buffer_count += 1
        # Write to file
        with open("models/neo/supervised_data_1.json", "w") as f:
            json.dump(buffer, f, indent=4)
        # Debug
        print(f">> Written {buffer_count * buffer_max}x JSON datasets to file!")
    buffer["data_count"] = buffer.get("data_count", 0) + 1
    obs_arr = buffer.get("observations", [])
    obs_arr.append({
        "state": state,
        "action": action,
        "reward": reward,
        "next": next_state
    })
    buffer["observations"] = obs_arr
    buffer_curr += 1


def run_game(game, agent):
    slp = 0
    while True:
        if game.active:
            actions = agent.predict()
            if not actions:
                if slp > 0:
                    time.sleep(slp)
                game.step()
            else:
                for action in actions:
                    if slp > 0:
                        time.sleep(slp)
                    # Returns: board matrix (state), score change (reward), is-game-over (done), next piece (extras)
                    # Need: state, action, reward, next_state
                    state, reward, _, _ = game.step(action, True)
                    next_state = TetrisUtils.get_board_with_tile(game.board, game.tile_shape, (game.tile_x, game.tile_y), True)
                    json_write(str(state), action, reward, str(next_state))
        else:
            game.reset()


class ActionAgent:
    def __init__(self, tetris):
        self.tetris = tetris

    def predict(self):
        # State, action, next_state, reward, done?
        return TetrisUtils.get_best_actions(self.tetris.board, self.tetris.tile_shape, TILE_SHAPES[self.tetris.get_next_tile()], (self.tetris.tile_x, self.tetris.tile_y))


if __name__ == "__main__":
    game = TetrisGame.TetrisGame()
    agent = ActionAgent(game)
    run_game(game, agent)
