from pathlib import Path

# def get_version():
#     script_dir = Path(__file__).resolve().parent
#     pyproject_path = script_dir / "../pyproject.toml"
#     pyproject_path = pyproject_path.resolve()
#     with open(pyproject_path, "r") as f:
#         pyproject = toml.load(f)
#     return pyproject["tool"]["poetry"]["version"]


__version__ = "2.2.3"
