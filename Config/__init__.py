import yaml
from typing import Dict

from pathlib import Path
from loguru import logger


class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


ConfigPath = Path(r'./Config')

if not ConfigPath.joinpath('config.yaml').exists() or not ConfigPath.joinpath('permission.yaml').exists():
    logger.error("不存在配置文件！")
    exit()
else:
    with ConfigPath.joinpath("config.yaml").open("r", encoding="utf-8") as conf_r:
        config_data: Dict = yaml.load(conf_r.read(), Loader=yaml.FullLoader)

    with ConfigPath.joinpath("permission.yaml").open("r", encoding="utf-8") as perm_r:
        permission_data: Dict = yaml.load(perm_r.read(), Loader=yaml.FullLoader)

    bot_Admin = config_data['botAdmin']


def save_config():
    logger.info("正在保存配置文件")
    with ConfigPath.joinpath("config.yaml").open("w", encoding="utf-8") as conf_w:
        yaml.dump(config_data, conf_w, allow_unicode=True, Dumper=NoAliasDumper)

    with ConfigPath.joinpath("permission.yaml").open("w", encoding="utf-8") as perm_w:
        yaml.dump(permission_data, perm_w, allow_unicode=True, Dumper=NoAliasDumper)

    logger.info("配置文件保存成功")
