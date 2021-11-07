import torch.nn as nn
import torch.nn.functional as F
from model.layers import GraphConvolution

H_NEURONS_l1 = 128
H_NEURONS_l2 = 64


class GCN(nn.Module):
    def __init__(self, in_c, out_c, dropout):
        super(GCN, self).__init__()

        self.gc1 = GraphConvolution(in_c, H_NEURONS_l1)
        self.gc2 = GraphConvolution(H_NEURONS_l1, H_NEURONS_l2)
        self.gc3 = GraphConvolution(H_NEURONS_l2, out_c)
        self.dropout = dropout

    def forward(self, x, adj):
        x = F.relu(self.gc1(x, adj))
        x = F.dropout(x, self.dropout, training=self.training)
        x = F.relu(self.gc2(x, adj))
        x = F.dropout(x, self.dropout, training=self.training)
        out = self.gc3(x, adj)
        return out
