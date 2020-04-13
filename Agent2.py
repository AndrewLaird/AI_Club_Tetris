import keras
from tensorflow.keras import layers
from tensorflow.keras import Sequential

import numpy as np
import random


class DQN_Agent():
    def __init__(self):
        # Gamma is the decay rate
        # - the amount that we don't want reward to propagate
        self.gamma = .9
        self.prob_random = .1

        self.model = Sequential()

        # Define the layers
        # Board is 20 (rows) x 10 (cols)
        # self.model.add(layers.Dense(256, input_shape=(200,), activation="relu"))
        # self.model.add(layers.Dense(8, activation="softmax"))  # output actions = 8

        self.model.add(layers.Dense(512))
        self.model.add(layers.Dense(1024))
        self.model.add(layers.Dense(2048))
        self.model.add(layers.Dense(1024))
        self.model.add(layers.Dense(512))
        self.model.add(layers.Dense(8, activation="softmax"))

        self.model.compile(optimizer='adam', loss='mean_squared_error', metrics=["accuracy"])
        self.data = []
        self.data_max = 1_000_000

    # Zipped info format: [(obs, action, backed_up_reward, done), (...)]
    def add_to_data(self, zipped_info):
        # Check to make sure that data has room
        zipped_info = list(zipped_info)
        room_left = self.data_max - len(self.data) - len(zipped_info)
        if room_left < 0:
            del self.data[:abs(room_left)]  # remove earliest data
        self.data.extend(zipped_info)  # append data

    # Data format: [(last_obs, action, obs, reward, done), (...)]
    def take_in_data(self, data):
        # we have to take in this data and backup the rewards correctly
        # assuming we haven't shuffled the data yet
        # so backup the reward between 1's going backward
        # lets do it by backing up any reward with discount

        # oh I think we have a dp problem
        # we want rt + yrt+1 + y^2rt+2 ...
        # which recursively is g(t) = rt + y*g(t+1)
        obs, action, new_obs, reward, done = zip(*data)
        backed_up_reward = [0 for x in range(len(reward))]

        for i in range(len(reward) - 2, 0, -1):
            if not done[i]:
                backed_up_reward[i] = reward[i] + self.gamma * backed_up_reward[i + 1] + .01

        # now add to the backed_up_reward the term for discounted gamma*max_a(Q(s',a))
        for i in range(len(backed_up_reward)):
            if len(obs[i]) != 0 and not done[i]:
                max_action = self.training_predict(obs[i])
                backed_up_reward[i] += self.gamma * max_action

        self.add_to_data(zip(obs, action, backed_up_reward, done))

    def train(self, iteration=0):
        # this should be fun
        # we want our network to predict the rewards given that input
        obs, action, reward, done = zip(*self.data)
        x_train = np.array([np.array(x).flatten() for x in obs])
        print(x_train.shape)
        y_train = np.array(reward)
        self.model.fit(x_train, y_train, epochs=10)
        self.model.save(f"models/neo/model{iteration}.h5")

    def training_predict(self, obs):
        # no randomness
        # and we return the magnitude of the value not just which one was max
        obs = np.array([np.array(obs).flatten()])
        answer = self.model.predict(obs)[0]
        largest_index = np.argmax(answer)
        return answer[largest_index]

    def predict(self, obs):
        if random.random() < self.prob_random:
            return random.randint(0, 8)
        obs = np.array([np.array(obs).flatten()])
        answer = self.model.predict(obs)[0]
        return np.argmax(answer)
