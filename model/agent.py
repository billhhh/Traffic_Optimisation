"""
This Agent class is specifically modified for gcnn_dqn
"""

import numpy as np
from model.dqn import DQN as Learner
from scripts.utils import act, act_Y_cnt, lane_waiting, get_loop_state,\
    get_lane_state, get_tls_state_by_TLIDs, get_tls_state_withDet_by_TLIDs, \
    get_len_by_tls
from scripts.logger import Logger
import scipy.sparse as sp
from model.adj import env1_edges
import time


"""
Y_cnt: Yellow phase count down for lengthening Yellow phase
"""
class Agent:
    def __init__(self, traci, use_detector=False, exploration=0.5, Y_cnt=0,
                 change_phase_R=0, dropout=0.5, tls_state=False, env=env1_edges):
        self.controlTLIds = traci.trafficlights.getIDList()  # Control all tls
        self.phaseDefs, action_mask = self.makeActMap(traci, self.controlTLIds)
        self.Y_CNT = Y_cnt
        self.change_phase_R = change_phase_R
        self.useDetector = use_detector
        adj = self._get_adjacency_matrix(self.controlTLIds, env)
        self.tls_state = tls_state

        # Use detector, include loops
        if use_detector:
            self.detectorIDs = self._getDetectorIDs(traci)

        self.reset()
        state_size = self.state.shape[1]
        self.learner = Learner(state_size, action_mask, adj, exploration, dropout)

        # self.logger = Logger(log_name="gcnn_dqn_agent.log")
        # self.log_flag = False
        return

    # reset before each epoch
    def reset(self):
        self.waitTimePrev = 0
        self.totalReward = 0
        self.totalCost = 0
        self.isStable = len(self.controlTLIds) * [True]
        self.Y_cnt_vec = len(self.controlTLIds) * [self.Y_CNT]

        self.previousPhases = [0] * len(self.controlTLIds)
        self.bufferRYGs = len(self.previousPhases) * [0]  # next phase
        self.controlStates = len(self.previousPhases) * [0]  # current phase
        self.action = len(self.controlTLIds) * [0]
        self.state = np.array(self._normalize(self._getStateGCNN()).todense())

    def agentAct(self):
        if all(self.isStable):
            time_start = time.time()
            self.action = self.learner.act(self.state)
            time_end = time.time()
            print()
            print('ACTION_TIME:', time_end-time_start, 's')
            print()

            self.Y_cnt_vec = len(self.controlTLIds) * [self.Y_CNT]

        # isStable array would be modified inside this func, no worries
        act_Y_cnt(self.action, self.bufferRYGs, self.controlStates,
                  self.previousPhases, self.controlTLIds, self.phaseDefs,
                  self.isStable, self.Y_cnt_vec)

        # act(self.action, self.bufferRYGs, self.controlStates, self.previousPhases,
        #     self.controlTLIds, self.phaseDefs, self.isStable)

    def agentCulCost(self):
        self.totalCost += lane_waiting(self.controlTLIds)

    def agentCulReward(self, is_sim=False):
        if all(self.isStable):
            next_state = np.array(self._normalize(self._getStateGCNN()).todense())
            wait_time = lane_waiting(self.controlTLIds)
            reward = self.waitTimePrev - wait_time
            self.waitTimePrev = wait_time

            # print("reward: ", reward)
            if self.change_phase_R != 0:
                reward += self.changePhaseReward()

            if not is_sim:
                self.learner.remember(self.state.flatten(), self.action, reward,
                                      next_state.flatten())
                self.learner.replay()

            self.totalReward += reward
            self.state = next_state

    def _getStateGCNN(self):
        if self.useDetector:
            state = get_tls_state_withDet_by_TLIDs(self.controlTLIds)
        else:
            state = get_tls_state_by_TLIDs(self.controlTLIds)

        if self.tls_state:
            state_list = state.A.tolist()
            for row in range(state.shape[0]):
                state_list[row].append(self.action[row])
            state = sp.csr_matrix(state_list, dtype=np.float32)
        return state

    def _getDetectorIDs(self, traci):
        return traci.inductionloop.getIDList()

    def printLog(self, outfile, simulation):
        outfile.write("Simulation {} group {}: cost {}, reward {}, exploration {:.5}\n"
                      .format(simulation, self.controlTLIds, self.totalCost, self.totalReward,
                              self.learner.exploration))
        outfile.flush()

    def printScreen(self):
        print("agentGroup {}: cost {}, reward {}".format(self.controlTLIds, self.totalCost, self.totalReward))

    def makeActMap(self, traci, tls):
        phase_defs = []
        max_phase_len = 0
        # get phases
        for tl in tls:
            phases = []
            for e in traci.trafficlights.getCompleteRedYellowGreenDefinition(tl):
                for i, p in enumerate(e._phases):
                    # only add none YR states
                    if i % 3 == 0:
                        phases.append(p._phaseDef)
            phase_defs.append(phases)
            max_phase_len = max(max_phase_len, len(phases))

        # create mask
        mask = np.zeros((len(tls), max_phase_len), dtype=np.float32)
        for i, p in enumerate(phase_defs):
            mask[i, len(p):] = float('-inf')
        return phase_defs, mask

    """
    Punish phase change of tls
    or reward those unchanged ones
    """
    def changePhaseReward(self):
        reward = 0
        for ind in range(len(self.controlTLIds)):
            if self.action[ind] == self.previousPhases[ind]:
                reward += self.change_phase_R
        return reward

    def _get_adjacency_matrix(self, tls, env):
        # convert edge to inds
        idx_map = {tl: i for i, tl in enumerate(tls)}
        edges_unordered = np.array(env['edges'])
        edges = np.array(list(map(idx_map.get, edges_unordered.flatten())),
                         dtype=np.int32).reshape(edges_unordered.shape)
        try:
            edges_len = []
            for edge in edges_unordered:
                # find edge length
                edges_len.append(get_len_by_tls(edge[0], edge[1]))
            edges_len_weights = max(edges_len) / np.array(edges_len)
            adj = sp.coo_matrix((edges_len_weights, (edges[:, 0], edges[:, 1])),
                                shape=(len(tls), len(tls)),
                                dtype=np.float32)
        except BaseException:
            adj = sp.coo_matrix((np.ones(edges.shape[0]), (edges[:, 0], edges[:, 1])),
                                shape=(len(tls), len(tls)),
                                dtype=np.float32)
        # build symmetric adjacency matrix
        adj = adj + adj.T.multiply(adj.T > adj) - adj.multiply(adj.T > adj)
        adj = self._normalize(adj
                              + sp.eye(adj.shape[0])  # diagonal mat
                              )
        return np.array(adj.todense())

    def _normalize(self, mx):
        """Row-normalize sparse matrix"""
        rowsum = np.array(mx.sum(1))
        r_inv = np.power(rowsum, -1).flatten()
        r_inv[np.isinf(r_inv)] = 0.
        r_mat_inv = sp.diags(r_inv)
        mx = r_mat_inv.dot(mx)
        return mx
