"""依赖集合排序：不允许循环依赖"""

from typing import TypeVar

T = TypeVar("T")


def _topo_sort(dependencies_tree: dict[T, list[T]]) -> list[T]:
    """拓扑排序的深度优先搜索实现，不允许循环依赖.

    Args:
        dependencies_tree (dict): 依赖关系树，键为依赖项，值为被依赖项列表

    Returns:
        list: 拓扑排序后的节点列表

    Examples:
        >>> dependencies = {
                "WebApp": ["API", "Database"],  # WebApp依赖API和Database
                "API": ["Utils"],                # API依赖Utils
                "Database": ["Utils"]            # Database依赖Utils
            }
        >>> _topo_sort(dependencies)
        ['Utils', 'API', 'Database', 'WebApp']  # 正确的安装顺序

    Raises:
        Exception: 当检测到循环依赖时抛出异常
    """
    visited = {}
    result = []

    def dfs(node: T):
        """dfs(node) 函数用于深度优先遍历每个节点.
        使用 visiting 集合来检测是否发生了循环依赖。如果遇到未访问的邻居节点，则递归调用 DFS。
        """
        if visited.get(node, 0) == 1:
            raise Exception(f"Detected circular dependency at: {node}")
        if visited.get(node, 0) == 2:
            return
        visited[node] = 1
        for dep in sorted(dependencies_tree.get(node, [])):
            dfs(dep)
        visited[node] = 2
        result.append(node)

    for node in sorted(dependencies_tree):
        dfs(node)

    return result
