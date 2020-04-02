#!/usr/bin/env python
#-*- coding: utf-8 -*-

# Very simple tetris implementation
# 
# Control keys:
# Down - Drop stone faster
# Left/Right - Move stone
# Up - Rotate Stone clockwise
# Escape - Quit game
# P - Pause game
#
# Have fun!

# Copyright (c) 2010 "Kevin Chabowski"<kevin@kch42.de>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from random import randrange as rand
from itertools import permutations
import pygame, sys
import Agent
from copy import copy,deepcopy

# The configuration
config = {
    'cell_size':    20,
    'cols':        8,
    'rows':        16,
    'delay':    750,
    'maxfps':    30
}

colors = [
(0,   0,   0  ),
(255, 0,   0  ),
(0,   150, 0  ),
(0,   0,   255),
(255, 120, 0  ),
(255, 255, 0  ),
(180, 0,   255),
(0,   220, 220)
]

# Define the shapes of the single parts
tetris_shapes = [
    [[1, 1, 1],
     [0, 1, 0]],
    
    [[0, 2, 2],
     [2, 2, 0]],
    
    [[3, 3, 0],
     [0, 3, 3]],
    
    [[4, 0, 0],
     [4, 4, 4]],
    
    [[0, 0, 5],
     [5, 5, 5]],
    
    [[6, 6, 6, 6]],
    
    [[7, 7],
     [7, 7]]
]

def rotate_clockwise(shape):
    return [ [ shape[y][x]
            for y in range(len(shape)) ]
        for x in range(len(shape[0]) - 1, -1, -1) ]

def check_collision(board, shape, offset):
    off_x, off_y = offset
    for cy, row in enumerate(shape):
        for cx, cell in enumerate(row):
            try:
                if cell and board[ cy + off_y ][ cx + off_x ]:
                    return True
            except IndexError:
                return True
    return False

def remove_row(board, row):
    del board[row]
    return [[0 for i in range(config['cols'])]] + board
    
def join_matrixes(mat1, mat2, mat2_off):
    off_x, off_y = mat2_off
    for cy, row in enumerate(mat2):
        for cx, val in enumerate(row):
            mat1[cy+off_y-1    ][cx+off_x] += val
    return mat1

def new_board():
    board = [ [ 0 for x in range(config['cols']) ]
            for y in range(config['rows']) ]
    board += [[ 1 for x in range(config['cols'])]]
    return board

class TetrisApp(object):
    def __init__(self):
        # we could remove this for speed without visibility
        pygame.init()
        #pygame.key.set_repeat(250,25)
        self.width = config['cell_size']*config['cols']
        self.height = config['cell_size']*config['rows']
        
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.event.set_blocked(pygame.MOUSEMOTION) # We do not need
                                 # mouse movement
                                 # events, so we
                                 # block them.
        self.init_game()


    
    def new_stone(self):
        self.stone = tetris_shapes[rand(len(tetris_shapes))]
        self.stone_x = int(config['cols'] / 2 - len(self.stone[0])/2)
        self.stone_y = 0

        
        if check_collision(self.board,
                            self.stone,
                            (self.stone_x, self.stone_y)):
            self.gameover = True
    
    def init_game(self):
        self.gameover = False
        self.paused = False
        self.board = new_board()
        self.new_stone()
    
    def center_msg(self, msg):
        for i, line in enumerate(msg.splitlines()):
            msg_image =  pygame.font.Font(
                pygame.font.get_default_font(), 12).render(
                    line, False, (255,255,255), (0,0,0))
        
            msgim_center_x, msgim_center_y = msg_image.get_size()
            msgim_center_x //= 2
            msgim_center_y //= 2
        
            self.screen.blit(msg_image, (
              self.width // 2-msgim_center_x,
              self.height // 2-msgim_center_y+i*22))
    
    def draw_matrix(self, matrix, offset):
        off_x, off_y  = offset
        for y, row in enumerate(matrix):
            for x, val in enumerate(row):
                if val:
                    pygame.draw.rect(
                        self.screen,
                        colors[val],
                        pygame.Rect(
                            (off_x+x) *
                              config['cell_size'],
                            (off_y+y) *
                              config['cell_size'], 
                            config['cell_size'],
                            config['cell_size']),0)
    
    def move(self, delta_x):
        if not self.gameover and not self.paused:
            new_x = self.stone_x + delta_x
            if new_x < 0:
                new_x = 0
            if new_x > config['cols'] - len(self.stone[0]):
                new_x = config['cols'] - len(self.stone[0])
            if not check_collision(self.board,
                           self.stone,
                           (new_x, self.stone_y)):
                self.stone_x = new_x
    def quit(self):
        #self.center_msg("Exiting...")
        #pygame.display.update()
        sys.exit()
    
    def drop(self):
        if not self.gameover and not self.paused:
            self.stone_y += 1
            if check_collision(self.board,
                       self.stone,
                       (self.stone_x, self.stone_y)):
                self.board = join_matrixes(
                  self.board,
                  self.stone,
                  (self.stone_x, self.stone_y))
                self.new_stone()
                while True:
                    for i, row in enumerate(self.board[:-1]):
                        if 0 not in row:
                            self.board = remove_row(
                              self.board, i)
                            self.score += 7
                            break
                    else:
                        break
    
    def rotate_stone(self):
        if not self.gameover and not self.paused:
            new_stone = rotate_clockwise(self.stone)
            if not check_collision(self.board,
                           new_stone,
                           (self.stone_x, self.stone_y)):
                self.stone = new_stone
    
    def toggle_pause(self):
        self.paused = not self.paused

    
    def start_game(self):
        self.score = 0
        self.score_last_screen = 0
        if self.gameover:
            self.init_game()
            self.gameover = False
        return self.construct_state()
    
    def run(self):
        key_actions = {
            'ESCAPE':    self.quit,
            'LEFT':     lambda:self.move(-1),
            'RIGHT':    lambda:self.move(+1),
            'DOWN':        self.drop,
            'UP':        self.rotate_stone,
            'p':        self.toggle_pause,
            'SPACE':    self.start_game
        }
        
        self.gameover = False
        self.paused = False
        
        pygame.time.set_timer(pygame.USEREVENT+1, config['delay'])
        dont_burn_my_cpu = pygame.time.Clock()
        while 1:
            for event in pygame.event.get():
                if event.type == pygame.USEREVENT+1:
                    self.drop()
                elif event.type == pygame.QUIT:
                    self.quit()
                elif event.type == pygame.KEYDOWN:
                    for key in key_actions:
                        if event.key == eval("pygame.K_"+key):
                            key_actions[key]()
                
            self.step(action=-1,render=True)
            dont_burn_my_cpu.tick(config['maxfps'])

    def draw_screen(self):
        self.screen.fill((0,0,0))
        if(self.gameover):
            self.center_msg("Game Over")
        else:
            if self.paused:
                self.center_msg("Paused")
            else:
                self.draw_matrix(self.board, (0,0))
                self.draw_matrix(self.stone,
                         (self.stone_x,
                          self.stone_y))
        pygame.display.update()
            
    def construct_state(self):
        board = deepcopy(self.board)
        # put in the tetris piece
        stone_matrix = self.stone
        stone_x = self.stone_x
        stone_y = self.stone_y
        
        # add the stone into the board
        for row in range(len(stone_matrix)):
            for col in range(len(stone_matrix[row])):
                board[stone_y+row][stone_x+col] = stone_matrix[row][col]
        return board
    
    def step(self,action,render=True):
        actions = {
                1:  lambda:self.move(-1), #move left
                2:  lambda:self.move(+1), # move right
                3:  self.rotate_stone # rotate stone
                }
        
        if(render):
            self.draw_screen()
        # don't take any actions for 0
        if(action != 0):
            actions[action]()
        self.drop()
        # check for game over
        if(self.gameover):
            return [[],0,True]
        obs = []
        obs = self.construct_state()
        done = False
        # number of blocks done in the last round
        reward = self.score - self.score_last_screen
        self.score_last_screen = self.score
        

        return [obs,reward,done]

        

if __name__ == '__main__':
    App = TetrisApp()
    App.run()
