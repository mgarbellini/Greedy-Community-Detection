"""
@author:    M. Garbellini
@email:     matteo.garbellini@studenti.unimi.it
@course-project: Algoritmi e Strutture Dati, Università degli Studi di Milano

Girvan-Newman algorithm for community detection in networks
"""
from collections import deque
import random
import time
import numpy as np
import sys
from tqdm import tqdm

class Graph:
    """Graph class based on adjacency list implemented with dictionaries"""

    def __init__(self):
        self.adj_list = {}
        self.adj_matrix = None
        self.community_structure = {}
        self.num_components = None
        self.num_nodes = None
        self.num_edges = None

    def __iter__(self):
        return iter(self.adj_list.keys())

    def __getitem__(self, n):
        return self.adj_list[n]

    def load_adj_list(self, adj_list):
        self.adj_list = adj_list
        self.community_structure = dict.fromkeys(self.adj_list, 0)
        self.num_nodes = len(self.adj_list)

    def add_edge(self, v, w):
        if v not in self.adj_list:
            self.community_structure.update({v: 0})
            self.adj_list.update({v:[w]})
            if w not in self.adj_list:
                self.adj_list.update({w:[v]})
            else:
                self.adj_list[w].append(v)
        elif w not in self.adj_list:
            self.community_structure.update({w: 0})
            self.adj_list[v].append(w)
            self.adj_list.update({w:[v]})
        else:
            self.adj_list[v].append(w)
            self.adj_list[w].append(v)

    def remove_edge(self, v, w):
        del self.adj_list[v][self.adj_list[v].index(w)]
        del self.adj_list[w][self.adj_list[w].index(v)]

        self.num_edges -= 1

    def connected_components(self):
        seen = set()
        component = 0
        for node in self.adj_list:
            if node not in seen:
                component += 1
                Q = deque([node])
                while Q:
                    v = Q.popleft()
                    self.community_structure[v] = component
                    seen.add(v)
                    for w in self.adj_list[v]:
                        if w not in seen:
                            Q.append(w)

        self.num_components = component

    def get_edges(self):
        edges = []
        for node in self.adj_list:
            for neighbour in self.adj_list[node]:
                edges.append((node, neighbour))

        self.num_edges = len(edges)/2
        return edges

    def update_adj_matrix(self):

        adj_matrix = np.zeros((self.num_nodes, self.num_nodes))
        for node in self.adj_list:
            for neighbour in self.adj_list[node]:
                adj_matrix[node-1][neighbour-1] = 1
                adj_matrix[neighbour-1][node-1] = 1

        self.adj_matrix = adj_matrix

    def read_from_file(self, filename, key = 0):
        with open(filename) as file:
            for line in file:
                edge = line.split()

                if key == 1:
                    self.add_edge(int(edge[0]), int(edge[1]))
                else:
                    self.add_edge(int(edge[0])+1, int(edge[1])+1)

        self.num_nodes = len(self.adj_list)
        self.update_adj_matrix()


def girvan_newman_community_detection(G):


    # assess the graph before running the algorithm
    G.connected_components()
    edges = G.get_edges()
    community_structure = [G.community_structure]
    number_of_communities = [G.num_components]
    max_modularity = compute_modularity(G)
    solution_num_communities = number_of_communities



    # until we get single node community
    while G.num_edges > 0:

        # computes betweenness for the graph
        betweenness = edge_betweenness_centrality(G)

        # find most valuable/between edge
        edge_to_be_removed = most_between_edge(betweenness)

        # remove most between edge
        G.remove_edge(edge_to_be_removed[0], edge_to_be_removed[1])

        # find new modularity
        modularity = compute_modularity(G)

        # add new partition dictionary to communities list
        G.connected_components()
        community_structure.append(G.community_structure)
        number_of_communities.append(G.num_components)

        # save if improvement
        if modularity > max_modularity:
            max_modularity = modularity
            solution_num_communities = G.num_components

        print('Modularity: ', modularity, ' - # Communities: ', G.num_components)

    # printing final solution
    print('FINAL - Modularity: ', max_modularity, ' - # Commuities: ', solution_num_communities)


def edge_betweenness_centrality(G):
    """Computes the edge betweenness centrality by running modified shortest
    path algorithm."""
    betweenness = dict.fromkeys(G.get_edges(), 0.0)

    for node in G:
        # use BFS for shortest path from source s to all other nodes
        S, P, sigma = shortest_path_bfs(G, node)

        # accumulate betweenness for all edges
        betweenness = accumulate_betweenness(betweenness, S, P, sigma, node)

    # normalize betweenness for undirected graphs
    for edge in betweenness:
        betweenness[edge] *= 0.5

    #return betweenness
    return betweenness


def accumulate_betweenness(betweenness, S, P, sigma, s):
    """Accumulates the edge betweenness for all the nodes"""
    delta = dict.fromkeys(S, 0)
    while S:
        w = S.pop()
        coeff = (1 + delta[w]) / sigma[w]
        for v in P[w]:
            c = sigma[v] * coeff
            betweenness[(w, v)] += c
            betweenness[(v, w)] += c
            delta[v] += c
    return betweenness


def shortest_path_bfs(G, s):
    S = []
    P = {}
    for v in G:
        P[v] = []
    sigma = dict.fromkeys(G, 0.0)  # sigma[v]=0 for v in G
    D = {}
    sigma[s] = 1.0
    D[s] = 0
    Q = deque([s])
    while Q:  # use BFS to find shortest paths
        v = Q.popleft()
        S.append(v)
        Dv = D[v]
        sigmav = sigma[v]
        for w in G[v]:
            if w not in D:
                Q.append(w)
                D[w] = Dv + 1
            if D[w] == Dv + 1:  # this is a shortest path, count paths
                sigma[w] += sigmav
                P[w].append(v)  # predecessors
    return S, P, sigma


def most_between_edge(betweenness):

    mx = max(betweenness.values())
    max_keys = [k for k, v in betweenness.items() if v == mx]
    if len(max_keys) > 2:
        between_edge = random.choice(max_keys)
    else:
        between_edge = max_keys[0]

    return between_edge


def compute_modularity(G):

    Q = 0
    m = float(np.sum(G.adj_matrix))/2
    k = np.sum(G.adj_matrix, axis = 0)
    for i in range(len(G.adj_matrix[0])):
        for j in range(len(G.adj_matrix[0])):

            # only if both vertices belong to same community
            if G.community_structure[i+1] == G.community_structure[j+1]:
                Q += G.adj_matrix[i][j] - k[i]*k[j]/m/2

    return np.round(Q/m/2, 7)


if __name__ == '__main__':

    graph = Graph()
    graph.read_from_file(sys.argv[1], 1)
    girvan_newman_community_detection(graph)
