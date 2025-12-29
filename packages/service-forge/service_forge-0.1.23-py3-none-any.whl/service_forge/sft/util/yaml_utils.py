import yaml
from pathlib import Path
from typing import Any, Dict


def extract_yaml_content_without_comments(yaml_file: Path) -> str:
    """
    读取 YAML 文件，去除注释，返回格式化的 YAML 字符串

    Args:
        yaml_file: YAML 文件路径

    Returns:
        去除注释后的 YAML 字符串
    """
    with open(yaml_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 移除注释行（以 # 开头的行，但不包含字符串中的 #）
    lines = content.split('\n')
    filtered_lines = []

    for line in lines:
        stripped = line.strip()
        # 跳过空行和纯注释行
        if not stripped or stripped.startswith('#'):
            continue
        filtered_lines.append(line)

    # 重新组合并解析为 Python 对象，然后重新序列化
    yaml_content = '\n'.join(filtered_lines)

    try:
        # 使用 yaml.safe_load 解析，然后重新序列化确保格式正确
        data = yaml.safe_load(yaml_content)
        if data is None:
            return ""
        return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
    except yaml.YAMLError:
        # 如果解析失败，返回原始过滤后的内容
        return yaml_content


def load_sf_metadata_as_string(metadata_file: Path) -> str:
    """
    加载 sf-meta.yaml 文件，去除注释后返回字符串格式

    Args:
        metadata_file: sf-meta.yaml 文件路径

    Returns:
        去除注释后的 YAML 内容字符串
    """
    if not metadata_file.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_file}")

    return extract_yaml_content_without_comments(metadata_file)