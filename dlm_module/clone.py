import os
import re
import git
import stat
import logging

def parse_url(full_url):
    """
    解析URL，提取仓库地址、分支名和子目录路径
    Args:
        full_url: 完整的仓库URL地址
    Returns:
        tuple: 包含仓库Git地址、分支名和子目录路径的元组
    """
    # 正则表达式匹配仓库 URL、分支和路径，允许 path 部分为空
    match = re.match(
        # r'(?P<repo>.+)/-/tree/(?P<branch>[^/]+)(/(?P<path>.*))?',
        r'(?P<repo>.+)/tree/(?P<branch>[^/]+)(/(?P<path>.*))?',
        full_url
    )
    if not match:
        raise ValueError("URL 格式不正确")
    # 提取仓库 URL、分支和路径
    repo_path = match.group('repo')
    branch = match.group('branch')
    subdir = match.group('path') if match.group('path') is not None else ''
    # 拼接仓库 URL 同时这个就是 git 地址
    repo_url = f'{repo_path}.git'
    return repo_url, branch, subdir

def clone_repo(repo_url, branch, subdir):
    """
    克隆指定仓库的特定分支到本地sql_file目录
    Args:
        repo_url: Git仓库地址
        branch: 分支名称
        subdir: 仓库中的子目录路径
    Returns:
        str: 目标路径（当前未被使用）
    """
    # 目标目录
    target_dir = 'sql_file'
    # 删除目录及其内容
    if os.path.exists(target_dir):
        for root, dirs, files in os.walk(target_dir, topdown=False):
            for name in files:
                file_path = os.path.join(root, name)
                # 修改文件权限
                os.chmod(file_path, stat.S_IWRITE)
                os.remove(file_path)
            for name in dirs:
                dir_path = os.path.join(root, name)
                # 修改目录权限
                os.chmod(dir_path, stat.S_IWRITE)
                os.rmdir(dir_path)
        os.rmdir(target_dir)
    # 创建目标目录
    os.makedirs(target_dir, exist_ok=True)
    # 克隆仓库到目标目录
    git.Repo.clone_from(repo_url, target_dir, branch=branch, single_branch=True)
    logging.info(f"Repository cloned to: {target_dir}")
    # 获取目标目录的路径
    target_path = os.path.join(target_dir, subdir)
    # 返回的target_path暂时没有作用
    return target_path

def read_files_in_dir(dir_path):
    """
    获取指定目录下所有文件的路径列表
    Args:
        dir_path: 要扫描的目录路径
    Returns:
        list: 包含所有文件完整路径的列表
    """
    files = []
    for root, dirs, filenames in os.walk(dir_path):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            files.append(file_path)
    return files