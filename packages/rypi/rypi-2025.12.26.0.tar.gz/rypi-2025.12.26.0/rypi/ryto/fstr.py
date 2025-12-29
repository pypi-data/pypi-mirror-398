#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
增强版文件内容搜索工具

功能：
- 搜索指定目录中包含指定字符串的文件
- 支持通配符：*str*, *str, str*
- 支持多种文件类型过滤（-t *.txt,*.py）
- 支持递归深度控制（-d 2）
- 支持 UTF-8 和 ANSI (GBK) 编码自动检测
- 显示匹配行的行号
- 显示匹配字符串前后上下文（可配置）

用法：
python fstr.py -p /ebook -s "*hello*" -t "*.txt,*.py" -d 2 -c 20
'''

VER = r'''
fstr version: 2025.8.1.1.0
'''

COPR = r'''
版权所有 2025 锐码[rymaa.cn] 本软件采用 锐码署名传播许可证(RSPL) 授权。详情请见 LICENSE 或 LICENSE-EN 文件。| 网站: rymaa.cn | 邮箱: rybby@163.com
'''

INFO = r'''
fstr: Find str，增强版文件内容搜索工具

功能：
- 搜索指定目录中包含指定字符串的文件
- 支持通配符：*str*, *str, str*
- 支持多种文件类型过滤（-t *.txt,*.py）
- 支持递归深度控制（-d 2）
- 支持 UTF-8 和 ANSI (GBK) 编码自动检测
- 显示匹配行的行号
- 显示匹配字符串前后上下文（可配置）

用法：
python fstr.py -p /ebook -s "*hello*" -t "*.txt,*.py" -d 2 -c 20
'''

HELP = r'''
+-------------------------------------------+
|                 find str                  |
+-------------------------------------------+
|            HomePage: rymaa.cn             |
+-------------------------------------------+

Usage:
    rypi ryto fstr [option]

Options:
    -H, --help   Show help / 显示帮助
    -I, --info   Show info / 显示信息
    -C, --copr   Show copyright / 显示版权
    -V, --version   Show version / 显示版本
    -p, --path   搜索路径
    -s, --string   要搜索的字符串，支持 * 通配符（如 *str*, *str, str*）
    -t, --type   文件类型，多个用逗号分隔（如 *.txt,*.py），支持 *.* 表示所有文件
    -d, --depth   递归目录深度（1,2,3...），默认为无限深度
    -c, --context   显示匹配字符串前后各 N 个字符的上下文，默认 30
'''

##############################

import os
import sys
import argparse
import re
from pathlib import Path

##############################

def build_pattern(search_str):
    """将包含 * 的搜索字符串转换为正则表达式（保留原字符串用于高亮）"""
    escaped = re.escape(search_str)
    regex = escaped.replace(r'\*', '.*')
    return re.compile(regex, re.IGNORECASE)

def get_files_by_patterns(root_path, patterns):
    """根据 glob 模式获取文件列表"""
    root = Path(root_path)
    files = []
    for pattern in patterns:
        if pattern == '*.*':
            pattern = '*'  # 所有文件
        files.extend(root.rglob(pattern))
    return [f for f in set(files) if f.is_file()]

def should_include_in_depth(file_path, root_path, max_depth):
    """判断文件是否在指定深度内"""
    try:
        relative_parts = Path(file_path).relative_to(root_path).parts
        return len(relative_parts) <= max_depth
    except ValueError:
        return False

def read_file_with_encoding(file_path):
    """尝试多种编码读取文件"""
    encodings = ['utf-8', 'gbk', 'latin1']
    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, PermissionError):
            continue
    return ""

def main(args=None):
    '''
    入口主函数。
    返回: void
    参数列表：
        args (str): 参数列表，通过命令行传入或调用者传入。
    '''

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-H', '--help', action='store_true')
    parser.add_argument('-I', '--info', action='store_true')
    parser.add_argument('-C', '--copr', action='store_true')
    parser.add_argument('-V', '--version', action='store_true')
    parser.add_argument('-p', '--path')
    parser.add_argument('-s', '--string')
    parser.add_argument('-t', '--type', default='*.txt')
    parser.add_argument('-d', '--depth', type=int, default=None)
    parser.add_argument('-c', '--context', type=int, default=30)

    args = parser.parse_args(args)
    
    if args.version:
        print(VER)
        return
    elif args.copr:
        print(COPR)
        return
    elif args.info:
        print(INFO)
        return
    elif args.help:
        print(HELP)
        return

    root_path = os.path.abspath(args.path).replace('\\', '/')
    search_str = args.string
    file_types = [t.strip() for t in args.type.split(',')]
    max_depth = args.depth
    context_len = args.context

    if not os.path.exists(root_path):
        print(f"错误：路径不存在: {root_path}")
        sys.exit(1)

    # 构建正则表达式
    pattern = build_pattern(search_str)
    print(f"\n搜索路径: {root_path}")
    print(f"搜索字符串: {search_str} → 正则: {pattern.pattern}")
    print(f"文件类型: {file_types}")
    print(f"最大深度: {'无限制' if max_depth is None else max_depth}")
    print(f"上下文长度: ±{context_len} 字符\n")
    print("=" * 50)
    print()

    files = get_files_by_patterns(root_path, file_types)
    if max_depth is not None:
        files = [f for f in files if should_include_in_depth(f, root_path, max_depth)]

    total_matches = 0
    matched_files = 0

    for file_path in sorted(files):
        content = read_file_with_encoding(file_path)
        if not content:
            continue

        lines = content.splitlines()
        file_matches = 0

        for line_no, line in enumerate(lines, 1):
            if pattern.search(line):
                # 提取上下文
                start = max(0, line.find(pattern.pattern.split('.*')[0]) - context_len)
                end = min(len(line), line.rfind(pattern.pattern.split('.*')[-1]) + context_len)

                context = line[start:end]
                if start > 0:
                    context = "..." + context
                if end < len(line):
                    context = context + "..."

                rel_path = os.path.join(root_path, file_path)
                rel_path = os.path.abspath(rel_path).replace('\\', '/')

                print(f"{rel_path} ( Line: {line_no} )")
                print(f"  {context}")
                print()

                file_matches += 1
                total_matches += 1

        if file_matches > 0:
            matched_files += 1

    print("=" * 50)
    print(f"\n✅ 搜索完成：共扫描 {len(files)} 个文件，{matched_files} 个文件包含匹配，总计 {total_matches} 处匹配。")

if __name__ == '__main__':
    main()