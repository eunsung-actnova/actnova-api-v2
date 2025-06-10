import sys
from pathlib import Path

# Ensure the project root, common utilities and api_gateway packages are on PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parents[5]

sys.path.insert(0, str(ROOT_DIR / "common"))
sys.path.insert(0, str(ROOT_DIR / "api_gateway"))

