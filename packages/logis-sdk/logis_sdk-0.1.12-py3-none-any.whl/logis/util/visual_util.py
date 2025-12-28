import inspect
from itertools import chain
from math import e
from typing import Iterable

import matplotlib.pyplot as plt
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout


def mro_tree(cls):
    """把 inspect.getclasstree 结果扁平化并返回父->子边"""
    tree = inspect.getclasstree(inspect.getmro(cls))
    edges = []

    def walk(node):
        if not node:
            return
        if not isinstance(node, Iterable):
            return
        if isinstance(node, list):  # 同级列表
            for item in node:
                walk(item)
        elif len(node) == 2:
            # node = (class, (parent_list))
            cls, bases = node
            if not isinstance(bases, Iterable):
                edges.append((cls, None))  # 无父类的类
                return
            for p in bases:
                edges.append((p, cls))  # 父 -> 子
            walk(list(bases))
        else:
            pass

    walk(tree)
    return edges


def draw_mro_tree(*cls_list, use_graphviz=False):
    for cls in cls_list:
        edges = mro_tree(cls)
        G = nx.DiGraph()
        G.add_edges_from(edges)

        plt.figure(figsize=(6, 4))
        if use_graphviz:

            pos = graphviz_layout(G, prog="dot")
        else:
            pos = nx.spring_layout(G, seed=42)

        nx.draw(
            G,
            pos,
            with_labels=True,
            node_size=2000,
            node_color="skyblue",
            font_size=10,
            arrowsize=15,
        )
        plt.axis("off")
        plt.show()
