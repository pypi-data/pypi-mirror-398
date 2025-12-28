"""等价类的拓展功能"""
import importlib
import logging
from pathlib import Path

from ._checker import Checker

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


def get_all_subclasses(cls: type) -> list[type]:
    all_subclasses = []

    for subclass in cls.__subclasses__():
        all_subclasses.append(subclass)
        all_subclasses.extend(get_all_subclasses(subclass))

    return all_subclasses


current_dir = Path(__file__).resolve().parent
package_name = __package__ or current_dir.name

for filename in current_dir.iterdir():
    if filename.suffix == '.py' and filename.stem.endswith('_c'):
        module_name = filename.stem
        logger.info('successfully imported module: "%s"', module_name)
        try:
            module = importlib.import_module(f'{package_name}.{module_name}')
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, Checker) and attr != Checker:
                    locals()[attr_name] = attr
        except ImportError:
            logger.exception('Failed to import %s', module_name)
            continue


dynamic_checkers = [cls.__name__ for cls in get_all_subclasses(Checker)]
__all__ = ['Checker', 'get_all_subclasses']
__all__ += dynamic_checkers  # noqa: PLE0605  # mypy无法识别[] + dynamic的格式
