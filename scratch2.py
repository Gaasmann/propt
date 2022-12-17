import pickle
from pprint import pprint

import networkx.algorithms.traversal
from networkx import DiGraph, simple_cycles, find_cycle


class ConstructionOrder:
    def __init__(self, g: DiGraph):
        self.g = g

    def head_items(self) -> list[str]:
        """Return the name of item nodes that don't have predecessor."""
        return [
            node
            for node, succ in self.g.pred.items()
            if not succ and g.nodes[node]["node_type"] == "pu"
        ]


def nodes_ready(g: DiGraph) -> list[str]:
    """Return the nodes without unchecked preds (or no preds)."""
    return [
        node
        for node in g.nodes
        if not g.nodes[node]["checked"]
        and (not g.pred[node] or all(g.nodes[n]["checked"] for n in g.pred[node]))
    ]


def circular_item_node(g: DiGraph) -> set[str]:
    h = g.copy()
    checked_nodes = [node for node in h.nodes if h.nodes[node]["checked"]]
    h.remove_nodes_from(checked_nodes)
    cycle = find_cycle(h)
    res = set()
    if not cycle:
        return res
    for edge in cycle:
        res.update(node for node in edge if h.nodes[node]["node_type"] == "item")
    return res

    # res = []
    # for node in g.nodes:
    #     if g.nodes[node]["node_type"] != "item":
    #         continue
    #     print(f"{node} => {set(g.succ[node])} == {set(g.pred[node])}")
    #     if set(g.succ[node]) == set(g.pred[node]):
    #         res.append(node)
    # return res


if __name__ == "__main__":
    with open("graphou", "rb") as f:
        g: DiGraph = pickle.load(f)

    for node in g.nodes:
        g.nodes[node]["checked"] = False
    plop = find_cycle(g)
    res = []
    while any(not g.nodes[n]["checked"] for n in g.nodes):
        next_nodes = nodes_ready(g)
        if not next_nodes:
            items = circular_item_node(g)
            if not items:
                print("FUCK")
                break
            for item in items:
                g.nodes[item]["checked"] = True
            continue
        # print(next_nodes)
        for pu_node in next_nodes:
            g.nodes[pu_node]["checked"] = True
            res.append(pu_node)
            for succ_node in g.succ[pu_node]:
                print(succ_node)
                g.nodes[succ_node]["checked"] = True
        print("HOLOL")
        print([node for node in g.nodes if not g.nodes[node]["checked"]])
        # print(len(res))
        # print([node for node in g.nodes if g.nodes[node]["checked"]])

    # co = ConstructionOrder(g)
    # nodes = co.head_items()
    # g.add_node("begin")
    # for node in nodes:
    #     g.add_edges_from(("begin", n) for n in nodes)
    # n = nodes[0]
    # res = [
    #     " ".join(node.split("\n")[1:]) + "\n"
    #     for node, succ in networkx.algorithms.traversal.bfs_edges(g, "begin")
    #     if g.nodes[node].get("node_type", "") == "pu"
    # ]

    with open("orders", "w") as f:
        f.writelines([" ".join(node.split("\n")[1:]) + "\n" for node in res])
