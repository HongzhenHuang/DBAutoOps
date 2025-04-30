from contextlib import redirect_stderr
import logging
import argparse
import os
import sys
sys.path.append('/home/ldaphome/hhz/workspace/DBAutoOps/dlm_module')
from os.path import dirname
from to_db import write_to_db, write_to_db_with_config
from clone import read_files_in_dir, clone_repo, parse_url
from sql_extract import process_files, process_files_with_config
from flask import flash, request, render_template, redirect, url_for

def run_gitlab_scanner():
    if request.method == 'POST':
        url = request.form.get('gitlab_url')  # 使用 .get() 更安全
        try:
            # 解析 URL
            repo_url, branch, subdir = parse_url(url)
            print(subdir)
            # 克隆仓库
            clone_path = clone_repo(repo_url, branch, subdir)
            target_path = os.path.join('sql_file', subdir)

            # 遍历文件夹
            for root, dirs, filenames in os.walk(target_path):
                files = [os.path.join(root, filename) for filename in filenames]
                if not files:
                    continue

                parts = files[0].split(os.sep)
                subdir = os.sep.join(parts[1:-1]).replace(os.sep, '/')

                # 处理文件并写入数据库
                results = process_files_with_config(files)
                write_to_db_with_config(repo_url, results, branch, subdir)

            print('扫描成功了')
            flash('扫描成功！', 'gitlab_scan_status')  # 添加成功提示

        except ValueError as e:
            logging.error(f"Error: {e}")
            flash(f'扫描失败：{e}', 'gitlab_scan_status')  # 添加失败提示

        # return render_template('data_lineage.html')
        return redirect(url_for('to_data_lineage'))

