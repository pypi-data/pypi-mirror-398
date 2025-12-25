#!/usr/bin/python3
# -*- coding:utf-8 -*-

"""
author：yannan1
since：2023-08-23
"""
import time
import torch
import numpy as np


class KMeans:

    def __init__(self, n_clusters, seed=None):

        self.n_clusters = n_clusters
        self.seed = seed

    def initialize(self, X):

        num_samples = len(X)
        if self.seed is None:
            indices = np.random.choice(num_samples, self.n_clusters, replace=False)
        else:
            np.random.seed(self.seed)
            indices = np.random.choice(num_samples, self.n_clusters, replace=False)
        initial_state = X[indices]
        return initial_state

    @staticmethod
    def euclidean(data1, data2):
        t0 = time.time()

        # N*1*M
        A = data1.unsqueeze(dim=1)

        # 1*N*M
        B = data2.unsqueeze(dim=0)

        dis = (A - B) ** 2.0
        # return N*N matrix for pairwise distance
        dis = dis.sum(dim=-1).squeeze()

        # print(time.time() - t0)

        # torch.norm(vector1 - vector2)
        return dis

    def fit(self, X):
        X = X.float()
        device = X.device

        initial_state = self.initialize(X).to(device)

        iteration = 0
        iter_limit = 0
        tol = 1e-4

        while True:
            dis = self.euclidean(X, initial_state)
            choice_cluster = torch.argmin(dis, dim=1)
            initial_state_pre = initial_state.clone()

            for index in range(self.n_clusters):
                selected = torch.nonzero(choice_cluster == index).squeeze().to(device)
                selected = torch.index_select(X, 0, selected)
                if selected.shape[0] == 0:
                    selected = X[torch.randint(len(X), (1,))]

                initial_state[index] = selected.mean(dim=0)

            center_shift = torch.sum(
                torch.sqrt(
                    torch.sum((initial_state - initial_state_pre) ** 2, dim=1)
                ))

            # increment iteration
            iteration = iteration + 1

            if center_shift ** 2 < tol:
                break
            if iter_limit != 0 and iteration >= iter_limit:
                break

        return initial_state

    def fit_predict(self, X):

        cluster_centers = self.fit(X)
        dis = self.euclidean(X, cluster_centers)
        out = cluster_centers[torch.argmin(dis, dim=1)]

        return out
