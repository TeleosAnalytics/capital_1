import yaml
from pathlib import Path

proj_path = Path(__file__).resolve().parents[2]

params_path = proj_path / "params.yml"
params = {}
if params_path.exists():
    with open(params_path, "r") as f:
        # Load the file into the 'params' dictionary
        params = yaml.safe_load(f) or {}