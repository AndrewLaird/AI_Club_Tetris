# using DQN to play tetris
# This coursera course was a great example that I used to 
# implement this agent: https://github.com/udacity/deep-reinforcement-learning/blob/master/dqn/solution/dqn_agent.py
# state = board given by
from copy import copy , deepcopy
import torch

import numpy as np
import random

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(device)

import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F

class DQN_Model(nn.Module):
    def __init__(self,input_size):
        super(DQN_Model, self).__init__()
        print("INPUT SIZE:", input_size)
        self.dense1 = nn.Linear(input_size,1024)
        self.dense2 = nn.Linear(1024,1024)
        self.dense3 = nn.Linear(1024,2048)
        self.dense4 = nn.Linear(2048,1024)
        self.dense5 = nn.Linear(1024,1024)
        self.dense6 = nn.Linear(1024,6)

    def forward(self, x):
        x = F.relu(self.dense1(x))
        x = F.relu(self.dense2(x))
        x = F.relu(self.dense3(x))
        x = F.relu(self.dense4(x))
        x = F.relu(self.dense5(x))
        output = F.relu(self.dense6(x))
        return output

# possible outputs 
# move left, move right, rotate, do nothing
# maybe add the shoot down option
class DQN_Agent():

    def __init__(self,input_size):
        # gamma is the decay rate
        # or the amount that we don't want reward to propigate
        self.gamma = .9
        self.prob_random = .1
        self.epochs = 50
        # define the layers
        # will come in as flattend rep of the board game
        self.model = DQN_Model(input_size)
        self.target_model = DQN_Model(input_size).to(device)

        #self.model.load_state_dict(torch.load("Pytorch_DQN1.torch"))

        self.update_target_model()


        self.optimizer = optim.Adam(self.model.parameters(),lr=1e-4)

        self.data = []

        self.data_max = 20000

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
        #obs = torch.tensor(obs).flatten(1)
        #new_obs = torch.tensor(new_obs).flatten(1)
        #reward = torch.tensor(reward)
        #done = torch.tensor(done)

        self.add_to_data(zip(obs,action,new_obs,reward,done))


    def train(self):
        print("Training on this many samples",len(self.data))
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
        data = list(np.random.permutation(self.data))
        obs,actions,next_obs,rewards,dones = zip(*data)
        # TODO Figure out why this can't be done in the take in data step
        obs = torch.tensor(obs).flatten(1).float().to(device)
        next_obs = torch.tensor(next_obs).flatten(1).float().to(device)
        rewards = torch.tensor(rewards).unsqueeze(1).float().to(device)
        running = torch.tensor([not x for x in dones]).unsqueeze(1).float().to(device)
        actions = torch.tensor(actions).unsqueeze(1).to(device)


        # all of these are numpy arrays
        # if something looks weird it could be because
        # we are vectorizing this calculation

        for i in range(self.epochs):
            self.model.to(device)

            model_value_of_next_state = self.target_model.forward(next_obs).detach().max(1)[0].unsqueeze(1)

            target_for_this_state = rewards + (self.gamma * model_value_of_next_state * running)

            # TODO Explain Gather
            model_current_estimate = self.model.forward(obs).gather(1,actions)
            
            loss = F.mse_loss(model_current_estimate,target_for_this_state)
            print("\tloss",loss)

            self.optimizer.zero_grad()
            # back up those gradients
            loss.backward()
            self.optimizer.step()
        self.model.to('cpu')
        torch.save(self.model.state_dict(),"Pytorch_DQN1.torch")

        # cleanup memory
        del obs
        del next_obs
        del rewards
        del running
        del actions

        self.update_target_model()

    def update_target_model(self):
        self.target_model.load_state_dict(deepcopy(self.model.state_dict()))


    def predict(self,obs):
        if(random.random() < self.prob_random):
            return random.randint(0,5)
        
        obs = torch.tensor(obs).flatten().float()

        answer = self.model.forward(obs).detach()
        return np.argmax(answer)





        


