from hydra import initialize_config_dir, compose
from omegaconf import OmegaConf
import math

def load_hydra_config(config_dir: str, config_name: str):
    with initialize_config_dir(version_base=None, config_dir=config_dir):
        cfg_tree = compose(config_name=config_name)

    OmegaConf.register_new_resolver(
        "deg2rad",
        lambda deg: float(deg) * math.pi / 180.0,
    )

    # Resolved config
    cfg = OmegaConf.to_container(
        cfg_tree,
        resolve=True,
        throw_on_missing=True
    )
    return cfg
