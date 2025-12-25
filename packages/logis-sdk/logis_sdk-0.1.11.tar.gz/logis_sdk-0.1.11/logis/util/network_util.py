from typing import Any, Dict, List, Literal, Optional, Union

from logis.data_type import Point

Grid2 = List[List[Point]]
Grid3 = List[Grid2]


def to_grid(
    points: List[Point], include_x=True, include_y=True, include_z=False, **kwargs
) -> Union[Grid3, Grid2, None]:
    """
    将一系列点转换为网格结构
    每个Point代表一个方块的中心点，方块大小一致但不一定是正立方体

    Args:
        points: 一系列Point对象
        **kwargs: 可选参数
            x_step: x方向上的网格步长,如果未指定则自动推测
            y_step: y方向上的网格步长,如果未指定则自动推测
            z_step: z方向上的网格步长,如果未指定则自动推测

    Returns:
        三维网格/二维网格
    """
    if not points:
        return None

    # 定义一个函数来计算步长
    def calculate_step(values):
        """计算一组值的最小步长"""
        if len(values) <= 1:
            return 1

        # 计算相邻值之间的差值
        diffs = [abs(values[i + 1] - values[i]) for i in range(len(values) - 1)]
        return min(diffs)

    x_step = y_step = z_step = None
    x_size = y_size = z_size = None

    # 获取步长参数，如果未指定则自动计算
    if include_x:
        x_step = kwargs.get("x_step", calculate_step(sorted(set(p.x for p in points))))
        min_x = min(p.x for p in points)
        max_x = max(p.x for p in points)
        x_size = int((max_x - min_x) / x_step) + 1

    if include_y:
        y_step = kwargs.get("y_step", calculate_step(sorted(set(p.y for p in points))))
        min_y = min(p.y for p in points)
        max_y = max(p.y for p in points)
        y_size = int((max_y - min_y) / y_step) + 1

    if include_z:
        z_step = kwargs.get("z_step", calculate_step(sorted(set(p.z for p in points))))
        min_z = min(p.z for p in points)
        max_z = max(p.z for p in points)
        z_size = int((max_z - min_z) / z_step) + 1

    valid_indexes = list(filter(lambda v: v is not None, [x_size, y_size, z_size]))
    if len(valid_indexes) < 2:
        return None

    # 初始化网格
    if x_size and y_size and z_size:
        grid = [
            [[None for _ in range(z_size)] for _ in range(y_size)]
            for _ in range(x_size)
        ]
    else:
        x_size, y_size = valid_indexes
        grid = [[None for _ in range(y_size)] for _ in range(x_size)]

    # 将点放入网格中
    for point in points:
        # 计算点在网格中的索引
        x_idx = int((point.x - min_x) / x_step) if x_step else None
        y_idx = int((point.y - min_y) / y_step) if y_step else None
        z_idx = int((point.z - min_z) / z_step) if z_step else None

        tmp = grid
        for _, idx in enumerate([x_idx, y_idx, z_idx]):
            if idx is None:
                continue
            if tmp[idx] is None:
                tmp[idx] = point
            else:
                tmp = tmp[idx]
    return grid


import networkx as nx
from pyecharts import options as opts
from pyecharts.charts import Graph, Sankey, Tree


def nx_digraph_to_graph(
    G: nx.DiGraph,
    title: Optional[str] = None,
    node_size: int = 30,
    node_size_key: str = None,
    layout: Literal["force", "circular"] = "force",
    graph_opts: Dict[str, Any] = {},
    virtual_root_id: Optional[str] = None,
    **kwargs,
) -> Graph:
    """
    将 networkx.DiGraph 转换为 Pyecharts Graph 图表

    参数:
        G: networkx 有向图
        title: 图表标题
        node_size: 默认节点大小
        node_size_key: 从节点属性中读取大小的字段（如节点有 "size" 属性则优先使用）
        edge_width: 默认边宽度
        edge_width_key: 从边属性中读取宽度的字段（如边有 "weight" 属性则优先使用）
        layout: 布局方式

    返回:
        Pyecharts Graph 对象，可直接调用 render() 生成 HTML
    """
    if virtual_root_id and (roots := [n for n, d in G.in_degree() if d == 0]):
        if len(roots) > 1:
            G = G.copy()
            for r in roots:
                G.add_edge(virtual_root_id, r)

    nodes = []
    for node, attrs in G.nodes(data=True):
        size = attrs.get(node_size_key, node_size) if node_size_key else node_size
        nodes.append(opts.GraphNode(name=str(node), symbol_size=size))

    links = []
    for u, v, attrs in G.edges(data=True):
        links.append(opts.GraphLink(source=str(u), target=str(v)))

    graph = (
        Graph()
        .add(
            series_name="",
            nodes=nodes,
            links=links,
            layout=layout,
            is_draggable=True,
            **graph_opts,
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title=title),
            tooltip_opts=opts.TooltipOpts(trigger="item"),  # 鼠标悬停显示信息
        )
    )

    return graph


def nx_digraph_to_tree(
    G: nx.DiGraph,
    title: Optional[str] = None,
    layout: str = "orthogonal",
    orient: str = "LR",
    name_key: str = "name",
    color_key: str = "color",
    default_name: str = "node",
    virtual_root_id: Optional[str] = None,
) -> Tree:
    """
    将树状结构的 networkx.DiGraph 转换为 Pyecharts Tree 图表

    参数:
        G: 有向图（需为无环图且含单根节点）
        title: 图表标题
        layout: 布局方式（"orthogonal" 或 "radial"）
        orient: 树方向（"LR"/"RL"/"TB"/"BT"）
        name_key: 节点属性中用于显示名称的字段
        color_key: 节点属性中用于颜色的字段
        default_name: 无名称属性时的默认名称
        virtual_root_id: 虚拟根节点ID（当节点存在多个根节点时使用）
    """
    # 校验图结构（无环 + 单根节点）
    if not nx.is_directed_acyclic_graph(G):
        raise ValueError("输入图必须是无环有向图（DAG）")
    roots = [n for n, d in G.in_degree() if d == 0]

    if virtual_root_id and len(roots) > 1:
        if virtual_root_id not in G:
            G = G.copy()
            for root in roots:
                G.add_edge(virtual_root_id, root)
        roots = [virtual_root_id]
    elif len(roots) != 1:
        raise ValueError("图中必须有且仅有一个根节点（或指定虚拟根节点）")

    # 递归构建 Tree 数据
    def build_node(current: Any) -> Dict[str, Any]:
        attrs = G.nodes.get(current, {})
        node = {
            "name": attrs.get(name_key, str(current) or default_name),
            "itemStyle": {"color": attrs[color_key]} if color_key in attrs else {},
        }
        children = [build_node(child) for _, child in G.out_edges(current)]
        if children:
            node["children"] = children
        return node

    tree = Tree().set_global_opts(
        title_opts=opts.TitleOpts(title=title),
        tooltip_opts=opts.TooltipOpts(trigger="item", formatter="{b}"),
    )
    for root in roots:
        tree_data = [build_node(root)]
        tree.add(
            series_name=str(root),
            data=tree_data,
            layout=layout,
            orient=orient,
            label_opts=opts.LabelOpts(
                position="left" if orient in ["LR", "RL"] else "top",
                vertical_align="middle",
                horizontal_align="right",
            ),
        )

    return tree


def nx_digraph_to_sankey(
    G: nx.DiGraph,
    title: Optional[str] = None,
    level_key: str = None,
    **kwargs,
) -> Sankey:
    """
    将 networkx.DiGraph 转换为 Pyecharts Sankey 图（适用于有向无环图DAG）

    参数:
        G: 有向图（建议DAG，避免循环影响层级）
        title: 图表标题
        weight_key: 边属性中权重的字段名（用于边的粗细）
        default_weight: 边无权重时的默认值
        level_key: 节点属性中存储层级的字段（如节点有 "level" 属性则优先使用）
                   若为 None，自动通过拓扑排序推断层级
        curve: 边的弯曲度（0为直线，1为最大弯曲）
        node_width: 节点宽度（像素）
        node_gap: 同层级节点间距（像素）
    """
    if level_key is not None:
        # 从节点属性获取层级
        node_levels = {
            node: attrs.get(level_key, 0) for node, attrs in G.nodes(data=True)
        }
    else:
        if not nx.is_directed_acyclic_graph(G):
            raise ValueError(
                "自动推断层级需要输入有向无环图（DAG），或通过 level_key 指定层级"
            )
        topo_order = list(nx.topological_sort(G))
        node_levels = {node: 0 for node in topo_order}
        for node in topo_order:
            for predecessor in G.predecessors(node):
                if node_levels[node] <= node_levels[predecessor]:
                    node_levels[node] = node_levels[predecessor] + 1

    nodes: List[Dict[str, Any]] = []
    for node, attrs in G.nodes(data=True):
        node_name = attrs.get("name", str(node))
        nodes.append(
            {
                "name": node_name,
                "level": node_levels[node],
            }
        )

    links: List[Dict[str, Any]] = []
    for u, v, attrs in G.edges(data=True):
        u_name = G.nodes[u].get("name", str(u))
        v_name = G.nodes[v].get("name", str(v))
        links.append(
            {
                "source": u_name,
                "target": v_name,
                "value": max(1, len(u_name.split(","))) * 5,
            }
        )

    return (
        Sankey()
        .add(
            series_name=title or "Sankey",
            nodes=nodes,
            links=links,
            **kwargs,
        )
        .set_global_opts(title_opts=opts.TitleOpts(title=title))
    )


if __name__ == "__main__":
    grid1 = to_grid(
        [Point.of(0, 0, 0), Point.of(1, 1.5, 1), Point.of(2, 2, 2)], include_z=False
    )
    print(grid1)
