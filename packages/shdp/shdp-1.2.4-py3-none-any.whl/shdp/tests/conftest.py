import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.DEBUG)

# Ajouter le répertoire racine au PYTHONPATH
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

# print(sys.path)
# print(root_dir)


def pytest_configure(config):
    """Configure pytest options."""
    config.option.asyncio_mode = "strict"
