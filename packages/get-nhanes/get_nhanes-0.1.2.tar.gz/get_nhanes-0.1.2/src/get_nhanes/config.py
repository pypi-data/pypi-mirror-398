# config.py

import os
import json

# 配置文件路径
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "nhanes_config.json")

# 初始化为 None，表示尚未在内存中加载
_BASE_PATH = None


def set_base_path(path, persist=True):
    """设置NHANES数据的基础路径

    Args:
        path (str): NHANES数据的基础路径
        persist (bool): 是否将配置保存到文件中，默认为True

    Raises:
        ValueError: 如果路径不存在
    """
    global _BASE_PATH

    # 验证路径是否存在
    if not os.path.exists(path):
        raise ValueError(f"路径不存在: {path}")

    # 规范化路径，移除尾部斜杠
    path = os.path.normpath(path)
    _BASE_PATH = path

    # 如果需要持久化，则保存到配置文件
    if persist:
        save_config({"base_path": path})

    print(f"NHANES基础路径已设置为: {path}")
    return path


def get_base_path():
    """获取NHANES数据的基础路径

    Returns:
        str: 配置的基础路径

    Raises:
        RuntimeError: 如果基础路径尚未配置
    """
    global _BASE_PATH

    # 如果内存中没有配置，尝试从文件加载
    if _BASE_PATH is None:
        try:
            config_data = load_config()
            if "base_path" in config_data:
                _BASE_PATH = config_data["base_path"]
                # 验证路径是否仍然存在
                if not os.path.exists(_BASE_PATH):
                    print(f"警告: 配置的路径不再存在: {_BASE_PATH}")
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    # 如果仍然没有配置，则抛出异常
    if _BASE_PATH is None:
        raise RuntimeError("NHANES基础路径未配置，请先调用set_base_path()")

    return _BASE_PATH


def save_config(config_data):
    """保存配置到文件

    Args:
        config_data (dict): 要保存的配置数据
    """
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_data, f, indent=2)
    except Exception as e:
        print(f"警告: 无法保存配置文件: {e}")


def load_config():
    """从文件加载配置

    Returns:
        dict: 加载的配置数据
    """
    if not os.path.exists(CONFIG_FILE):
        return {}

    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)


def reset_config():
    """重置配置（删除配置文件）"""
    global _BASE_PATH
    _BASE_PATH = None
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
        print("配置已重置")


# 为方便访问，创建一个属性形式的接口
def __getattr__(name):
    if name == "BASE_PATH":
        return get_base_path()
    raise AttributeError(f"模块 'config' 没有属性 '{name}'")


# 启动时尝试加载配置
try:
    get_base_path()
    print(f"已从配置文件加载基础路径: {_BASE_PATH}")
except RuntimeError:
    # 尚未配置路径，这是正常的
    pass