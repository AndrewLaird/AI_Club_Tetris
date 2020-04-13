import random
from AI_Club_Tetris.Agent2 import DQN_Agent
import AI_Club_Tetris.TetrisGame as TetrisGame


class RandomAgent:
    def predict(self, obs):
        return random.randint(0, 3)


def run_game(game, agent, render):
    done = False
    obs = game.reset()
    total_reward = 0
    experience = []
    last_obs = obs

    while not done:
        action = agent.predict(obs)
        obs, reward, done, next_block = game.step(action)
        next_block = TetrisGame.TILES.index(next_block)
        # print(next_block)
        total_reward += reward
        experience.append((last_obs, action, obs, reward, done))
        last_obs = obs
    # print(f"Total reward: {total_reward}")
    return experience


if __name__ == "__main__":
    game = TetrisGame.TetrisGame()
    agent = RandomAgent()
    better_agent = DQN_Agent()
    exp_list = []

    iteration = 0
    while True:
        exp_list.clear()
        print(f"[{iteration}] Running simulations...")
        for i in range(100):
            exp_list.append(run_game(game, agent, render=True))
            # if(experience != -1):
            # something to be gained

        print(f"[{iteration}] Gathering data...")
        for i in range(len(exp_list)):
            if i % 5 == 0:
                print(f">> {i * 100 / len(exp_list):.0f}% complete")
            better_agent.take_in_data(exp_list[i])

        print(f"[{iteration}] Training agent...")
        better_agent.train()
        iteration += 1

    """
    for i in range(1000):
        action = random.randint(0,3)
        # random agent
        obs,reward,done = game.step(action,render=True)
        if(done):
            obs = game.start_game()
        time.sleep(.01)
        """
