
import networkx as nx
import matplotlib.pyplot as plt


def show_lable_weigth(G,plt,attr="weight"):
    """图结构可视化"""
    # 更复杂的可视化
    pos = nx.spring_layout(G)  # 布局算法
    nx.draw_networkx_nodes(G, pos, node_size=500)
    nx.draw_networkx_edges(G, pos, width=1.0)
    nx.draw_networkx_labels(G, pos, font_size=12, font_family="sans-serif")
    
    nx.draw(G, pos, with_labels=True, node_color='lightcoral', edge_color='gray')
    edge_labels = nx.get_edge_attributes(G, attr)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels,font_size=12, font_family="sans-serif")
    
    plt.axis("off")
    plt.show()



    