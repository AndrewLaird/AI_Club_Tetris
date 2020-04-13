#t using DQN to play tetris
# This coursera course was a great example that I used to 
# implement this agent: https://github.com/udacity/deep-reinforcement-learning/blob/master/dqn/solution/dqn_agent.py
# state = board given by
from copy import copy , deepcopy
import tensorflow as tf
from tensorflow.keras import layers
from tensorflow.keras import Sequential
import numpy as np
import random device = "CPU" if tf.test.gpu_device_name() == "" else "GPU" print(device)


# possible outputs 
# move left, move right, rotate, do nothing
# maybe add the shoot down option
class DQN_Agent():

    def __init__(self):
        # gamma is the decay rate
        # or the amount that we don't want reward to propigate
        self.gamma = .9
        self.prob_random = .1
        # define the layers
        # will come in as flattend rep of the board game
        self.model = Sequential()
        self.model.add(layers.Dense(512))
        self.model.add(layers.Dense(1024))
        self.model.add(layers.Dense(2048))
        self.model.add(layers.Dense(1024))
        self.model.add(layers.Dense(512))
            # 4 ouputs nothing ,left, right, rotate
        self.model.add(layers.Dense(4))
            
        self.model.compile(optimizer='adam', loss='mean_squared_error')

        self.data = []

        self.data_max = 1000000

    def add_to_data(self,zipped_info):
        # check to make sure that data has room
        zipped_info = list(zipped_info)
        room_left = self.data_max - len(self.data) - len(list(zipped_info))
        if(room_left < 0):
            # remove from the front
            del self.data[0:abs(room_left)]

        # add the info in
        self.data.extend(zipped_info)
        

    def take_in_data(self,data):

        # take in the data
        # flatten the observations
        # put everything into numpy arrays
        obs,action,new_obs,reward,done = zip(*data)
        obs =np.array([np.array(x).flatten() for x  in obs])
        next_obs = np.array([np.array(x).flatten() for x in new_obs])
        reward = np.array(reward)
        done = np.array(done)

        self.data.extend(zip(obs,action,new_obs,reward,done))


    def train(self):
        # this should be fun
        # we want our network to predict the rewards given that input

        # loss we want to maximize is 
        # reward + gamma*max_a'Q(s',a',parameters) - Q(s,a,parameters) 
        # the Q(s,a,parameters) is just the current value
        # so we are going to say that 
        # max_a'Q(s',a',parameters) is just how much reward we expect to get in this state, taking this action
        # Luckily our model takes in a state and produces the amount of reward we expect if we took each action

        # idea written in a formula
        # Update q values
        # Q[state, action] = Q[state, action] + lr * (reward + gamma * np.max(Q[new_state, :]) — Q[state, action])

        # how do we formulate that as a deep learning question
        # we want 
        obs,action,next_obs,rewards,dones = zip(*self.data)
        # all of these are numpy arrays
        # if something looks weird it could be because
        # we are vectorizing this calculation


        model_value_of_next_state = self.model.predict(next_obs).max(1)
        model_value_of_next_state = np.expand_dims(model_value_of_next_state,1) # turn it from [[1],[2],[3]] to [1,2,3]

        target_for_this_state = rewards + self.gamma*model_value_of_next_state*(1-dones)







        for i in range(len(backed_up_reward)):
            if(len(obs[i]) != 0 and not done[i]):
                backed_up_reward[i] += self.gamma*best_next_actions[i] + backed_up_reward[i+1]
            else:
                # no observation that makes any sense
                backed_up_reward[i] = reward[i]

        

    def training_predict(self,obs):
        # no randomness
        # and we return the magnitude of the value not just which one was max
        obs = np.array([np.array(obs).flatten()])
        answer = self.model.predict(obs)
        largest_index = np.argmax(answer)
        return answer[largest_index]


    def predict(self,obs):
        if(random.random() < self.prob_random):
            return random.randint(0,3)
        obs = np.array([np.array(obs).flatten()])
        answer = self.model.predict(obs)[0]
        return np.argmax(answer)





        


