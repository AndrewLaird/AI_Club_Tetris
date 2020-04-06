import tetris_game
import random
import time
from Agent import DQN_Agent


def run_game(game,agent,render):
    done = False
    obs = game.start_game()
    total_reward = 0
    experience = []
    last_obs = obs
    
    while(not done):
        action = agent.predict(obs)
        obs,reward,done = game.step(action,render=render)
        total_reward += reward
        experience.append([last_obs,action,obs,reward,done])
        last_obs = obs
    print("total reward",total_reward)
    if(total_reward == 0):
        return -1
    return experience


class RandomAgent():
    def __init__(self):
        pass

    def predict(self,obs):
        return random.randint(0,3)

if __name__ == "__main__":
    game = tetris_game.TetrisApp()
    agent = RandomAgent()
    better_agent = DQN_Agent()
    while(True):
        for i in range(100):
            experience = run_game(game,better_agent,render=i==99)
            if(experience != -1):
                #something to be gained
                better_agent.take_in_data(experience)
        better_agent.train()



    """
    for i in range(1000):
        action = random.randint(0,3)
        # random agent
        obs,reward,done = game.step(action,render=True)
        if(done):
            obs = game.start_game()
        time.sleep(.01)
        """
