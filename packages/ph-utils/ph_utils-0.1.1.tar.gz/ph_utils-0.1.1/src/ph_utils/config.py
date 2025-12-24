# Copyright (c) [2023] [Tenny]
# [ph-utils] is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#         http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.
#!/usr/bin/env python3
from configparser import ConfigParser
import os
from pathlib import Path
import json


def load_env(file_dir=None, env_files=None):
    """加载环境变量, 列表后面的会替换列表前面重复的字段

    Args:
        file_dir (str, optional): 环境变量文件目录. Defaults to os.getcwd().
        env_files (list, optional): 环境变量文件名列表. Defaults to None. 如果为空会默认加载: ['.env', '.env.local', '.env.development', '.env.production']

    Returns:
        dict: 环境变量加载为 dict
    """
    envs = {}
    if not file_dir:
        file_dir = os.getcwd()
    if not env_files or len(env_files) == 0:
        env_files = [".env", ".env.local", ".env.development", ".env.production"]
    for envfile in env_files:
        envpath = Path(file_dir, envfile)
        if envpath.exists():
            with envpath.open(encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # 如果不是注释且为规范的内容行
                    if line.startswith("#") == False and line.find("=") != -1:
                        kvs = line.split("=")
                        key = kvs[0].strip()
                        value = kvs[1].strip()
                        os.environ[key] = value
                        envs[key] = value
    return envs


def load_ini(file_dir=None, ini_files=None):
    """加载 ini 配置文件, 列表后的内容会覆盖之前的

    Args:
        file_dir (str, optional): 配置文件所在目录. Defaults to None.
        ini_files (list, optional): 配置文件名列表. Defaults to None. 如果不传, 则为: ['config.ini']

    Returns:
        dict: 将 init 配置文件通过 ConfigParser 解析为字典后的返回
    """
    res = {}
    if not file_dir:
        file_dir = os.getcwd()
    if not ini_files or len(ini_files) == 0:
        ini_files = ["config.ini"]
    for ini_file in ini_files:
        ini_path = Path(file_dir, ini_file)
        if ini_path.exists():
            cfg = ConfigParser()
            cfg.read(ini_path.as_posix())
            res.update(cfg._sections) # ty: ignore[unresolved-attribute]
    return res


def load_json(file_dir=None, json_files=None):
    """加载 json 文件

    Args:
        file_dir (str, optional): 目录. Defaults to None.
        json_files (list, optional): json文件列表. Defaults to None.

    Returns:
        dict: 更新后的字典
    """
    res = {}
    if not file_dir:
        file_dir = os.getcwd()
    if not json_files or len(json_files) == 0:
        json_files = ["config.json"]
    for json_file in json_files:
        json_path = Path(file_dir, json_file)
        if json_path.exists():
            with json_path.open(encoding="utf-8") as f:
                try:
                    res.update(json.loads(f.read()))
                except:
                    pass
    return res
