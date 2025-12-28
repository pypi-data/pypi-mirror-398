import matplotlib.pyplot as plt
import networkx as nx

def plot_graph(graph):
    '''С помощью matplotlib и networkx рисует граф'''
    G = nx.Graph()
    for node, neighbors in graph.items():
        for neighbor in neighbors:
            G.add_edge(node, neighbor)
    nx.draw(G, with_labels=True, node_color='lightblue', node_size=500, font_size=12)
    plt.show()
    

if __name__ == '__main__':
    example = {1: [2, 3], 2: [1, 5, 4], 3: [1, 5], 4: [2], 5: [2, 3]}
    plot_graph(example)