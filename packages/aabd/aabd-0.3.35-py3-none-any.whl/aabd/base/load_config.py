import os

from omegaconf import OmegaConf
from aabd.base.path_util import list_files


def load_yaml_dir(path, overridden=None, override=None):
    if os.path.isdir:
        yml_file_paths = list_files(path, suffixes=['.yaml', '.yml'])
    else:
        yml_file_paths = [path]
    omega_confs = [OmegaConf.load(yml_file_path) for yml_file_path in yml_file_paths]
    if len(omega_confs) == 0:
        file_omega_conf = {}
    else:
        file_omega_conf = OmegaConf.merge(*omega_confs)
    if override is not None:
        file_omega_conf = OmegaConf.merge(file_omega_conf, override)
    if overridden is not None:
        file_omega_conf = OmegaConf.merge(overridden, file_omega_conf)
    return OmegaConf.to_container(file_omega_conf, resolve=True)
