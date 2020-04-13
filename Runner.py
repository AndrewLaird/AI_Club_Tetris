import TetrisGame
import random
import time
from Pytorch_Agent import DQN_Agent


def run_game(game,agent,render):
    done = False
    obs = game.reset()
    total_reward = 0
    experience = []
    last_obs = obs
    
    while(not done):
        action = agent.predict(obs)
        obs,reward,done,next_block = game.step(action)
        next_block = TetrisGame.TILES.index(next_block)
        # print(next_block)
        total_reward += reward
        experience.append([last_obs,action,obs,reward,done])
        last_obs = obs
    print("total reward",total_reward)
    return experience


class RandomAgent():
    def __init__(self):
        pass

    def predict(self,obs):
        return random.randint(0,3)

if __name__ == "__main__":
    game = TetrisGame.TetrisGame()
    agent = RandomAgent()
    dqn_agent = DQN_Agent(game.obs_size)
    while(True):
        for i in range(25):
            experience = run_game(game,dqn_agent,render=True)
            #if(experience != -1):
                #something to be gained
            dqn_agent.take_in_data(experience)
        dqn_agent.train()



    """
    for i in range(1000):
        action = random.randint(0,3)
        # random agent
        obs,reward,done = game.step(action,render=True)
        if(done):
            obs = game.start_game()
        time.sleep(.01)
        """
