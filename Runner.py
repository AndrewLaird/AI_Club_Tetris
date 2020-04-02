import tetris_game
import random
import time


def run_game(game,agent):
    done = False
    obs = game.start_game()
    total_reward = 0
    experience = []
    last_obs = obs
    
    while(not done):
        action = agent.predict(obs)
        obs,reward,done = game.step(action,render=True)
        total_reward += reward
        experience.append([last_obs,action,reward])
        last_obs = obs
    print("total reward",total_reward)
    return experience


class RandomAgent():
    def __init__(self):
        pass

    def predict(self,obs):
        return random.randint(0,3)

if __name__ == "__main__":
    game = tetris_game.TetrisApp()
    agent = RandomAgent()
    for i in range(100):
        run_game(game,agent)



    """
    for i in range(1000):
        action = random.randint(0,3)
        # random agent
        obs,reward,done = game.step(action,render=True)
        if(done):
            obs = game.start_game()
        time.sleep(.01)
        """
