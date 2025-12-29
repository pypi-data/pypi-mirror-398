#!/usr/bin/env python
'''
显示 256 色，方便在设计命令行窗口时选择色彩。
'''

VER = r'''
c256 version: 2025.10.12.1.0
'''

COPR = r'''
版权所有 2025 锐码[rymaa.cn] 本软件采用 锐码署名传播许可证(RSPL) 授权。详情请见 LICENSE 或 LICENSE-EN 文件。| 网站: rymaa.cn | 邮箱: rybby@163.com
'''

INFO = r'''
c256: 显示 256 色，方便在设计命令行窗口时选择色彩。
'''

HELP = r'''
+-------------------------------------------+
|              show 256 color               |
+-------------------------------------------+
|            HomePage: rymaa.cn             |
+-------------------------------------------+

Usage:
    rypi rycy c256 [option]

Options:
    -H, --help   Show help / 显示帮助
    -I, --info   Show info / 显示信息
    -C, --copr   Show copyright / 显示版权
    -V, --version   Show version / 显示版本
    -c, --color   Show 256 color / 显示 256 色
'''

##############################

import os
import sys
import argparse

##############################

# 首先确保终端支持256色
os.system('')  # 这行很重要，用于初始化Windows终端

def print_256_colors():
    # 检查是否支持256色
    # 终端可能不支持256色，尝试设置环境变量
    if '256color' not in os.environ.get('TERM', ''):
        os.environ['TERM'] = 'xterm-256color'
    
    print()
    print("256色显示（带颜色ID）:")
    print("=" * 40)
    
    # 标准16色
    print("标准16色:")
    print()
    for i in range(16):
        # 根据背景色智能选择前景色（深色背景用白字，浅色背景用黑字）
        fg_color = 15 if i < 8 else 0
        sys.stdout.write(f"\033[48;5;{i}m\033[38;5;{fg_color}m {i:3d} \033[0m")
        if (i + 1) % 8 == 0:
            print()
    print()
    
    # 216色（6x6x6颜色立方体）
    print("216色 (16-231):")
    print()
    for green in range(6):
        for red in range(6):
            for blue in range(6):
                color_code = 16 + (red * 36) + (green * 6) + blue
                # 根据颜色亮度选择前景色
                brightness = red + green + blue
                fg_color = 0 if brightness > 7 else 15  # 亮背景用黑字，暗背景用白字
                sys.stdout.write(f"\033[48;5;{color_code}m\033[38;5;{fg_color}m {color_code:3d} \033[0m")
            print()
        print()
    
    # 24级灰度 - 每行显示6个色块
    print("24级灰度 (232-255):")
    print()
    for i in range(232, 256):
        # 灰度色：前几个用白字，后几个用黑字
        fg_color = 0 if i >= 244 else 15
        sys.stdout.write(f"\033[48;5;{i}m\033[38;5;{fg_color}m {i:3d} \033[0m")
        
        # 每6个色块换一行
        if (i - 231) % 6 == 0:  # 232-255共24个，每6个换行
            print()
    print()

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
    parser.add_argument('-c', '--color', action='store_true')

    args = parser.parse_args(args)

    if args.version:
        print(VER)
    elif args.copr:
        print(COPR)
    elif args.info:
        print(INFO)
    elif args.color:
        print_256_colors()
    else:
        print(HELP)

if __name__ == '__main__':
    main()