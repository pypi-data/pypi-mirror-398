import math
from typing import List, Optional, Tuple, Union

from pyecharts import options as opts


class GridLayout:
    """
    智能网格布局计算器
    根据图表数量和布局要求，自动计算每个图表的GridOpts位置

    示例：
        calculator = GridLayoutCalculator(total_items=6, rows=2, cols=3)
        grid_opts_list = calculator.calculate()

        或自动计算行列：
        calculator = GridLayoutCalculator(total_items=5)
        grid_opts_list = calculator.calculate()  # 自动计算为2行3列
    """

    def __init__(
        self,
        total_items: int,
        rows: Optional[int] = None,
        cols: Optional[int] = None,
        width: str = "1200px",
        height: str = "800px",
        margin_top: str = "5%",
        margin_bottom: str = "5%",
        margin_left: str = "5%",
        margin_right: str = "5%",
        spacing_x: str = "2%",
        spacing_y: str = "2%",
    ):
        """
        初始化布局计算器

        Args:
            total_items: 图表总数量
            rows: 指定行数（如为None则自动计算）
            cols: 指定列数（如为None则自动计算）
            width: 总画布宽度
            height: 总画布高度
            margin_*: 边距（百分比或像素）
            spacing_*: 图表间距（百分比）
        """
        self.total_items = total_items
        self.rows = rows
        self.cols = cols
        self.width = width
        self.height = height
        self.margin_top = margin_top
        self.margin_bottom = margin_bottom
        self.margin_left = margin_left
        self.margin_right = margin_right
        self.spacing_x = spacing_x
        self.spacing_y = spacing_y

        # 自动计算行列数（如果未指定）
        if self.rows is None and self.cols is None:
            self.rows, self.cols = self._auto_calculate_grid()
        elif self.rows is None:
            self.rows = math.ceil(self.total_items / self.cols)
        elif self.cols is None:
            self.cols = math.ceil(self.total_items / self.rows)

    def _auto_calculate_grid(self) -> Tuple[int, int]:
        """自动计算最佳的行列数"""
        # 如果是1个图表，使用1x1
        if self.total_items <= 1:
            return 1, 1

        # 尝试找到一个接近正方形的布局
        sqrt = math.sqrt(self.total_items)
        rows = math.floor(sqrt)
        cols = math.ceil(self.total_items / rows)

        # 如果布局太窄（列数远大于行数），调整一下
        if cols / rows > 2:
            rows = math.ceil(sqrt)
            cols = math.ceil(self.total_items / rows)

        return rows, cols

    def _parse_percentage(self, value: str) -> float:
        """解析百分比字符串为小数"""
        if isinstance(value, str) and value.endswith("%"):
            return float(value.rstrip("%")) / 100
        elif isinstance(value, (int, float)):
            return float(value) / 100
        return 0.0

    def _to_percentage(self, value: float) -> str:
        """将小数转换为百分比字符串"""
        return f"{value * 100:.1f}%"

    def get_all_center_radius(self):
        """
        根据行列自动计算中心点、半径的百分值
        """
        r, c = self.rows, self.cols

        radius = 100 / max(r, c)
        y_per = 100 / (r * 2)
        y_centers = [(i + 1) * y_per for i in range(0, r * 2, 2)]
        x_per = 100 / (c * 2)
        x_centers = [(i + 1) * x_per for i in range(0, c * 2, 2)]

        count = 0
        for y_center in y_centers:
            for x_center in x_centers:
                yield dict(center=(x_center, y_center), radius=radius)
                count += 1
                if count >= self.total_items:
                    return

    def get_all_grid_opts(self) -> List[opts.GridOpts]:
        """
        计算所有图表的GridOpts配置

        Returns:
            按照顺序排列的GridOpts列表
        """
        # 解析边距和间距
        margin_top = self._parse_percentage(self.margin_top)
        margin_bottom = self._parse_percentage(self.margin_bottom)
        margin_left = self._parse_percentage(self.margin_left)
        margin_right = self._parse_percentage(self.margin_right)
        spacing_x = self._parse_percentage(self.spacing_x)
        spacing_y = self._parse_percentage(self.spacing_y)

        # 计算可用空间
        available_width = 1.0 - margin_left - margin_right
        available_height = 1.0 - margin_top - margin_bottom

        # 计算每个单元格的宽度和高度
        cell_width = (available_width - (self.cols - 1) * spacing_x) / self.cols
        cell_height = (available_height - (self.rows - 1) * spacing_y) / self.rows

        grid_opts_list = []

        for i in range(self.total_items):
            # 计算行列索引
            row = i // self.cols
            col = i % self.cols

            # 计算位置
            pos_left = margin_left + col * (cell_width + spacing_x)
            pos_top = margin_top + row * (cell_height + spacing_y)

            # 创建GridOpts
            grid_opts = opts.GridOpts(
                pos_left=self._to_percentage(pos_left),
                pos_top=self._to_percentage(pos_top),
                pos_right=self._to_percentage(1.0 - (pos_left + cell_width)),
                pos_bottom=self._to_percentage(1.0 - (pos_top + cell_height)),
                width=self._to_percentage(cell_width),
                height=self._to_percentage(cell_height),
            )

            grid_opts_list.append(grid_opts)

        return grid_opts_list

    def get_layout_info(self) -> dict:
        """获取布局信息"""
        return {
            "total_items": self.total_items,
            "rows": self.rows,
            "cols": self.cols,
            "actual_items": min(self.total_items, self.rows * self.cols),
            "empty_cells": max(0, self.rows * self.cols - self.total_items),
        }
