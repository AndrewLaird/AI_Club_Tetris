# using DQN to play tetris

# state = board given by
from copy import copy , deepcopy
import tensorflow as tf
from tensorflow.keras import layers
from tensorflow.keras import Sequential
import numpy as np
import random

device = "CPU" if tf.test.gpu_device_name() == "" else "GPU"
print(device)


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
        # we have to take in this data and backup the rewards correctly
        # assuming we haven't shuffled the data yet
        # so backup the reward between 1's going backward
        # lets do it by backing up any reward with discount
        
        # oh I think we have a dp problem
        # we want rt + yrt+1 + y^2rt+2 ...
        # which recursively is g(t) = rt + y*g(t+1)
        obs,action,new_obs,reward,done = zip(*data)
        backed_up_reward = [0 for x in range(len(reward))]
        current_reward = 0
        for i in range(len(reward)-2,0,-1):
            if(done[i]):
                current_reward = 0 
            else:
                backed_up_reward[i] = reward[i] + self.gamma*backed_up_reward[i+1] + .01
        
        # now add to the backed_up_reward the term for discounted gamma*max_a(Q(s',a))
        # definitely vectorize this
        # TODO
        for i in range(len(backed_up_reward)):
            if(len(obs[i]) != 0 and not done[i]):
                max_action = self.training_predict(obs[i])
                backed_up_reward[i] += self.gamma*max_action

        self.add_to_data(zip(obs,action,backed_up_reward,done))

    def train(self):
        # this should be fun
        # we want our network to predict the rewards given that input
        with tf.device(device):
            obs,action,reward,done = zip(*self.data)
            x_train = np.array([np.array(x).flatten() for x  in obs])
            print(x_train.shape)
            y_train = np.array(reward)
            self.model.fit(x_train,y_train,epochs=5)

    def training_predict(self,obs):
        # no randomness
        # and we return the magnitude of the value not just which one was max
        obs = np.array([np.array(obs).flatten()])
        answer = self.model.predict(obs)[0]
        largest_index = np.argmax(answer)
        return answer[largest_index]


    def predict(self,obs):
        if(random.random() < self.prob_random):
            return random.randint(0,3)
        obs = np.array([np.array(obs).flatten()])
        answer = self.model.predict(obs)[0]
        return np.argmax(answer)





        


