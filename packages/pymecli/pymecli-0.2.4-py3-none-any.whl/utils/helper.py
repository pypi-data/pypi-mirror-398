import numpy as np


def process_bounding_box(box_data):
    """处理边界框数据的辅助函数"""
    try:
        return np.asarray(box_data).reshape(4, 2).tolist()
    except (ValueError, AttributeError):
        return []
