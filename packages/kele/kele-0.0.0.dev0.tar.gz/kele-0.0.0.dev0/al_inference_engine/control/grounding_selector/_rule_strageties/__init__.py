import importlib
import logging
import pathlib

from .strategy_protocol import get_strategy_class

current_dir = pathlib.Path(__file__).resolve().parent
package_name = __package__ or current_dir.name

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

for filename in current_dir.iterdir():
    if filename.suffix == '.py' and filename.stem.endswith('_strategy') and filename.stem.startswith('_'):
        module_name = filename.stem
        logger.info('successfully imported module: "%s"', module_name)
        try:
            module = importlib.import_module(f'{package_name}.{module_name}')
        except ImportError:
            logger.exception('Failed to import %s', module_name)
            continue

__all__ = ["get_strategy_class"]
