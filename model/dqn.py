import torch
import torch.nn as nn
import numpy as np
from scripts.logger import Logger
from model.models import GCN as Net


class DQN(object):
    def __init__(self, state_size, action_mask, adj, exploration, dropout,
                 lr=0.001, batch_size=150, gamma=0.9,
                 save_memo=False):
        buffer_size = 2000
        action_len, action_size = action_mask.shape
        self.eval_net, self.target_net = Net(state_size, action_size, dropout),\
                                         Net(state_size, action_size, dropout)
        self.action_size = action_size
        self.action_len = action_len
        self.exploration = exploration
        self.state_size = state_size
        self.buffer_size = buffer_size
        self.batch_size = batch_size
        self._target_replace_iter = 100
        self.gamma = gamma
        self.mask = torch.FloatTensor(action_mask)
        self.adj = torch.FloatTensor(adj)

        self.learn_step_counter = 0
        self.memory_counter = 0
        self.memory = np.zeros((buffer_size, (action_len*state_size) * 2 + action_len + 1))  # initialize memory
        self.optimizer = torch.optim.Adam(self.eval_net.parameters(), lr=lr)
        # self.optimizer = torch.optim.SGD(self.eval_net.parameters(), lr=lr, momentum=0.9)
        self.loss_func = nn.MSELoss()
        # self.logger = Logger(log_name="dqn.log")
        self.saveMemo = save_memo

    def act(self, x):
        x = torch.unsqueeze(torch.FloatTensor(x), 0)
        # input only one sample
        if np.random.rand() > self.exploration:  # greedy
            out = self.eval_net.forward(x, self.adj)
        else:  # random
            out = np.random.rand(self.action_len, self.action_size)
        out = out + self.mask
        # print(out)
        action = torch.max(out, -1)[1].data.numpy().flatten()
        return action

    def remember(self, s, a, r, s_):
        transition = np.hstack((s, a, r, s_))
        # replace the old memory with new memory
        index = self.memory_counter % self.buffer_size
        self.memory[index, :] = transition
        self.memory_counter += 1

    def replay(self):
        if self.memory_counter < self.buffer_size:
            return
        # target parameter update
        if self.learn_step_counter % self._target_replace_iter == 0:
            self.target_net.load_state_dict(self.eval_net.state_dict())
        self.learn_step_counter += 1

        # sample batch transitions
        sample_index = np.random.choice(self.buffer_size, self.batch_size)
        b_memory = self.memory[sample_index, :]
        state_space = self.action_len*self.state_size
        b_s = torch.FloatTensor(b_memory[:, :state_space]).view(-1, self.action_len, self.state_size)
        b_a = torch.LongTensor(b_memory[:, state_space:state_space + self.action_len].astype(int))
        b_r = torch.FloatTensor(b_memory[:, state_space + self.action_len:state_space + self.action_len + 1])
        b_s_ = torch.FloatTensor(b_memory[:, -state_space:]).view(-1, self.action_len, self.state_size)

        # q_eval w.r.t the action in experience
        q_eval = self.eval_net(b_s, self.adj).gather(2, b_a.unsqueeze(2))  # shape (batch, action_len)
        q_next = self.target_net(b_s_, self.adj).detach()  # detach from graph, don't backpropagate
        q_target = b_r + self.gamma * q_next.max(-1)[0].view(self.batch_size,
                                                             self.action_len)  # shape (batch, action_len)
        loss = self.loss_func(q_eval.squeeze(), q_target)

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        if self.exploration > 0.01:
            self.exploration *= 0.99999

    def load(self, name):
        states = torch.load(name)
        self.eval_net.load_state_dict(states['eval_net'])
        self.target_net.load_state_dict(states['target_net'])
        if 'memory' in states:
            self.memory = states['memory']
            self.memory_counter = states['memory_counter']
            self.exploration = states['exploration']
            self.optimizer = states['optimizer']

    def loadModel(self, dict_to_load):
        self.eval_net.load_state_dict(dict_to_load['eval_net'])
        self.target_net.load_state_dict(dict_to_load['target_net'])
        if 'memory' in dict_to_load:
            self.memory = dict_to_load['memory']
            self.memory_counter = dict_to_load['memory_counter']
            self.exploration = dict_to_load['exploration']
            self.optimizer = dict_to_load['optimizer']

    # used for single agent
    def save(self, name):
        dict_to_save = {
            'eval_net': self.eval_net.state_dict(),
            'target_net': self.target_net.state_dict(),
        }
        if self.saveMemo:
            dict_to_save['memory'] = self.memory
            dict_to_save['memory_counter'] = self.memory_counter % self.buffer_size + self.buffer_size
            dict_to_save['exploration'] = self.exploration
            dict_to_save['optimizer'] = self.optimizer
        torch.save(dict_to_save, name)

    # used for multi agents
    def returnSaveDict(self):
        dict_to_save = {
            'eval_net': self.eval_net.state_dict(),
            'target_net': self.target_net.state_dict(),
        }
        if self.saveMemo:
            dict_to_save['memory'] = self.memory
            dict_to_save['memory_counter'] = self.memory_counter % self.buffer_size + self.buffer_size
            dict_to_save['exploration'] = self.exploration
            dict_to_save['optimizer'] = self.optimizer
        return dict_to_save
