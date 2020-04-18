from AI_Club_Tetris import TetrisGame, TetrisUtils
from AI_Club_Tetris.TetrisSettings import *
import time


def run_game(game, agent):
    slp = 0.01
    while True:
        if game.active:
            actions = agent.predict()
            if not actions:
                time.sleep(slp)
                game.step()
            else:
                for action in actions:
                    time.sleep(slp)
                    game.step(action)
        else:
            game.reset()


class ActionAgent:
    def __init__(self, tetris):
        self.tetris = tetris

    def predict(self):
        return TetrisUtils.get_best_actions(self.tetris.board, self.tetris.tile_shape, TILE_SHAPES[self.tetris.get_next_tile()], (self.tetris.tile_x, self.tetris.tile_y))


if __name__ == "__main__":
    game = TetrisGame.TetrisGame()
    agent = ActionAgent(game)
    run_game(game, agent)
