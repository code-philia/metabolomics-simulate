import yaml
from pathlib import Path


class Reaction:
    def __init__(self, name, substrates, products, capacity, rate=0.1):
        self.name = name
        self.substrates = substrates
        self.products = products
        self.capacity = capacity
        self.rate = rate  # 动态速率参数


def load_reactions_from_folder(folder_path):
    """
    Load all YAML reaction definitions from a folder.
    Each file must contain: name, capacity, substrates, products.
    """
    folder = Path(folder_path)
    if not folder.exists():
        raise FileNotFoundError(f"Reaction folder not found: {folder_path}")

    reactions = []
    for yaml_file in sorted(folder.glob("*.yaml")):
        with open(yaml_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            reactions.append(
                Reaction(
                    name=data["name"],
                    substrates=data.get("substrates", {}),
                    products=data.get("products", {}),
                    capacity=1#data.get("capacity", 1.0)
                )
            )
    return reactions


def load_pool_from_yaml(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)