import os
from pathlib import Path
from typing import Optional, Set

def path_abbr(
    path: str,
    scan_siblings: bool = False,
    min_length: int = 1,
    parent_dir: Optional[str] = None
) -> str:
    """
    智能路径简写函数
    
    Args:
        path: 要简写的路径
        scan_siblings: 是否扫描同级目录以避免冲突
        min_length: 最小缩写长度
        parent_dir: 指定扫描的同级目录父路径（默认自动提取）
    Returns:
        简写后的路径
    """
    # 处理相对路径
    p = Path(path)
    is_absolute = p.is_absolute()
    
    # 分离文件名和目录
    if p.suffix or p.name.startswith('.'):  # 简单判断是否为文件
        dir_parts = list(p.parent.parts)
        filename = p.name
    else:
        dir_parts = list(p.parts)
        filename = ""
    
    if not dir_parts:
        return path
    
    # 准备同级目录信息（如果需要扫描）
    siblings_map = {}
    if scan_siblings:
        # 确定要扫描的父目录
        if parent_dir:
            scan_base = Path(parent_dir)
        else:
            # 自动确定需要扫描的父目录
            for i in range(len(dir_parts)):
                # 从当前目录向上，找到第一个存在的目录作为扫描基准
                test_path = Path(*dir_parts[:i+1])
                if test_path.exists():
                    scan_base = test_path
                    break
            else:
                # 如果没有目录存在，则不扫描
                scan_base = None
        
        if scan_base and scan_base.is_dir():
            # 扫描每个可能发生冲突的目录层级
            current_path = scan_base
            for i, part in enumerate(dir_parts[len(scan_base.parts):], 1):
                if not current_path.exists():
                    break
                
                try:
                    # 获取当前目录下的所有条目
                    siblings = [item.name for item in current_path.iterdir() 
                               if item.is_dir() or (item.is_file() and i == len(dir_parts) - 1)]
                    # 映射父路径到同级目录列表
                    parent_key = str(current_path)
                    siblings_map[parent_key] = siblings
                except (PermissionError, OSError):
                    # 权限不足等异常，跳过扫描
                    pass
                
                # 更新到下一级目录
                current_path = current_path / part if i < len(dir_parts) else current_path
    
    # 处理每个目录部分
    result_parts = []
    used_abbrevs = set()
    
    for i, part in enumerate(dir_parts):
        # 处理特殊目录（根目录、当前目录、上级目录）
        if part in (os.path.sep, "", ".", ".."):
            result_parts.append(part)
            continue
        
        # 确定当前目录的父路径（用于扫描）
        if i == 0:
            parent_path = ""
        else:
            parent_path = str(Path(*dir_parts[:i]))
        
        # 获取同级目录列表
        siblings = []
        if scan_siblings and parent_path in siblings_map:
            siblings = siblings_map[parent_path]
        
        # 生成缩写
        abbrev = _generate_unique_abbrev(
            part=part,
            siblings=siblings,
            used_abbrevs=used_abbrevs,
            min_length=min_length,
            current_level=i
        )
        
        result_parts.append(abbrev)
        used_abbrevs.add(abbrev)
    
    # 添加文件名
    if filename:
        result_parts.append(filename)
    
    # 重新组合路径
    if is_absolute:
        # 绝对路径：确保以分隔符开头
        result = os.path.sep + os.path.sep.join(result_parts[1:]) if result_parts[0] == os.path.sep else os.path.sep.join(result_parts)
    else:
        result = os.path.join(*result_parts)
    
    return result

def _generate_unique_abbrev(
    part: str,
    siblings: list,
    used_abbrevs: Set[str],
    min_length: int,
    current_level: int
) -> str:
    """生成唯一的缩写"""
    # 查找第一个字母数字字符
    first_alnum = None
    for idx, char in enumerate(part):
        if char.isalnum():
            first_alnum = idx
            break
    
    # 如果没有字母数字字符，返回完整名称
    if first_alnum is None:
        return part
    
    # 尝试不同的长度
    for length in range(max(min_length, 1), len(part) + 1):
        # 确保包含第一个字母数字字符
        actual_length = max(length, first_alnum + 1)
        candidate = part[:actual_length]
        
        # 检查是否以字母数字开头
        if not candidate[0].isalnum():
            continue
        
        # 检查冲突：1) 已使用的缩写 2) 同级目录
        has_conflict = False
        
        # 检查已使用的缩写
        if candidate in used_abbrevs:
            has_conflict = True
        
        # 检查同级目录冲突
        if not has_conflict and siblings:
            for sibling in siblings:
                if sibling == part:
                    continue
                if sibling.startswith(candidate) or candidate.startswith(sibling):
                    has_conflict = True
                    break
        
        if not has_conflict:
            return candidate
    
    # 如果都冲突，尝试完整名称
    if part not in used_abbrevs:
        return part
    
    # 添加数字后缀解决冲突
    suffix = 1
    while True:
        candidate = f"{part[:min_length]}_{suffix}"
        if candidate not in used_abbrevs:
            return candidate
        suffix += 1