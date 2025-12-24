"""
可配置参数模块

支持从环境变量或 config.yaml 读取参数。
优先级: 环境变量 > config.yaml > 默认值
"""

import os
from pathlib import Path
from functools import lru_cache


# 默认值
DEFAULTS = {
    # Claim Grouping
    "CLAIM_SPLIT_THRESHOLD": 150,        # 触发拆分的组大小阈值
    "CLAIM_TARGET_SIZE": 120,            # 拆分后目标组大小
    "CLAIM_MAX_PER_DOC": 100,            # 每篇文档最大 claim 数
    "CLAIM_TOP_K_PER_GROUP": 10,         # 导出时每组 top-k claims
    
    # Taxonomy
    "TAXONOMY_MIN_PRIORITY": 1,          # 最小优先级 (越小越优先)
    "TAXONOMY_GENERAL_THRESHOLD": 0.3,   # general 占比警告阈值
    
    # Topic Selection
    "TOPIC_MIN_DF": 3,                   # topic 最小文档频率
    "TOPIC_SELECTION_STRATEGY": "min_df",  # 选择策略: min_df | max_weight
    
    # Relation Canonicalization
    "REL_QUALIFIER_KEYS": "sample_size,time_period,geography,industry",  # 保留的 qualifier keys
}


@lru_cache(maxsize=1)
def load_config() -> dict:
    """加载配置，支持 YAML 文件"""
    config = DEFAULTS.copy()
    
    # 尝试加载 config.yaml
    config_path = Path(__file__).parent.parent.parent.parent / "config.yaml"
    if config_path.exists():
        try:
            import yaml
            with open(config_path, 'r') as f:
                yaml_config = yaml.safe_load(f) or {}
                for key, value in yaml_config.items():
                    key_upper = key.upper()
                    if key_upper in config:
                        config[key_upper] = value
        except ImportError:
            pass  # yaml not installed
        except Exception as e:
            print(f"Warning: Failed to load config.yaml: {e}")
    
    # 环境变量覆盖
    for key in config:
        env_value = os.getenv(key)
        if env_value is not None:
            # 类型转换
            default = DEFAULTS[key]
            if isinstance(default, int):
                config[key] = int(env_value)
            elif isinstance(default, float):
                config[key] = float(env_value)
            elif isinstance(default, bool):
                config[key] = env_value.lower() in ('true', '1', 'yes')
            else:
                config[key] = env_value
    
    return config


def get(key: str, default=None):
    """获取配置值"""
    config = load_config()
    return config.get(key, default)


def reload():
    """重新加载配置"""
    load_config.cache_clear()
    return load_config()


# 便捷访问
def claim_split_threshold() -> int:
    return get("CLAIM_SPLIT_THRESHOLD")

def claim_target_size() -> int:
    return get("CLAIM_TARGET_SIZE")

def claim_max_per_doc() -> int:
    return get("CLAIM_MAX_PER_DOC")

def claim_top_k_per_group() -> int:
    return get("CLAIM_TOP_K_PER_GROUP")

def topic_min_df() -> int:
    return get("TOPIC_MIN_DF")

def taxonomy_general_threshold() -> float:
    return get("TAXONOMY_GENERAL_THRESHOLD")

def rel_qualifier_keys() -> list[str]:
    keys = get("REL_QUALIFIER_KEYS", "")
    return [k.strip() for k in keys.split(",") if k.strip()]
