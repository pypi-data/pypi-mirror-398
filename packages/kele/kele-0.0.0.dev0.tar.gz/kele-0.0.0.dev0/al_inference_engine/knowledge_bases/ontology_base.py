"""本体库的导入文件"""

import importlib.util
from pathlib import Path
from types import ModuleType


def _py_auto_load(filename: Path) -> ModuleType:
    """
    从给定的文件路径动态加载一个 Python 模块。

    :param filename: Python 文件路径。
    :type filename: Path
    :return: 加载的模块对象。
    :rtype: types.ModuleType
    :raises ImportError: 如果无法加载模块。
    """  # noqa: DOC501
    module_name = filename.stem  # 获取不带扩展名的文件名作为模块名
    spec = importlib.util.spec_from_file_location(module_name, str(filename))
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    raise ImportError(f"无法从 {filename} 导入模块")


def load_ontologies(
    concept_dir_or_path: str | Path,
    operator_dir_or_path: str | Path,
) -> None:
    """
    从概念目录和算子目录（或文件）加载所有 Python 本体模块。

    :param: concept_dir_or_path: 概念模块的目录或文件路径或yaml文件。
    :param: operator_dir_or_path: 算子模块的目录或文件路径或yaml文件。
    """
    def _collect_files(path: str | Path, suffix: str = '.py') -> list[Path]:
        """
        收集指定路径下所有 Python 文件。

        参数:
            path (str | Path): 文件路径或目录路径。

        返回:
            List[Path]: 所有符合条件的 Python 文件路径。
        """
        path = Path(path)
        if path.is_dir():
            # 返回目录下所有 .py 文件（不包括子目录）
            return sorted(path.glob(f"*{suffix}"))

        if path.is_file() and path.suffix == ".py":
            return [path]

        return []

    # 收集概念和算子模块的 Python 文件
    concept_py_files = _collect_files(concept_dir_or_path)
    operator_py_files = _collect_files(operator_dir_or_path)

    all_modules = []
    for file in concept_py_files + operator_py_files:
        module = _py_auto_load(file)
        all_modules.append(module)

    # TODO: 收集概念和算子模块的 yaml 文件
