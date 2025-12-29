#!/usr/bin/env python
'''
获取双重因素认证(2FA(Two Factor Authentication))动态验证码。
'''

VER = r'''
tfa version: 2025.8.1.1.0
'''

COPR = r'''
版权所有 2025 锐码[rymaa.cn] 本软件采用 锐码署名传播许可证(RSPL) 授权。详情请见 LICENSE 或 LICENSE-EN 文件。| 网站: rymaa.cn | 邮箱: rybby@163.com
'''

INFO = r'''
tfa: 获取双重因素认证(2FA(Two Factor Authentication))动态验证码。

本工具是用 pyotp 根据指定的密钥生成动态验证码

用来生成动态验证码的密钥, 通常由网络应用服务商提供

本工具有两个用途：

1. 生成一次性动态验证码: rypi ryto tfa key

2. 生成密钥, 用于生成动态验证码, 该用途适用应用服务商: rypi ryto tfa -k
'''

HELP = r'''
+-------------------------------------------+
|               get 2FA code                |
+-------------------------------------------+
|            HomePage: rymaa.cn             |
+-------------------------------------------+

Usage:
    rypi ryto tfa [option]

Options:
    -H, --help   Show help / 显示帮助
    -I, --info   Show info / 显示信息
    -C, --copr   Show copyright / 显示版权
    -V, --version   Show version / 显示版本
    -k, --key   Generate key / 生成密钥, 该密钥用于生成动态验证码
'''

##############################

import pyotp
import argparse

##############################

def main(args=None):
    '''
    入口主函数。
    返回: void
    参数列表：
        args (str): 参数列表，通过命令行传入或调用者传入。
    '''

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('option', nargs='?')
    parser.add_argument('-H', '--help', action='store_true')
    parser.add_argument('-I', '--info', action='store_true')
    parser.add_argument('-C', '--copr', action='store_true')
    parser.add_argument('-V', '--version', action='store_true')
    parser.add_argument('-k', '--key', action='store_true')

    args = parser.parse_args(args)

    if args.version:
        print(VER)
    elif args.copr:
        print(COPR)
    elif args.info:
        print(INFO)
    elif args.key:
        otp = pyotp.random_base32()
        print(f'\n{otp}')
    elif args.option:
        otp = pyotp.TOTP(args.option)
        print(f'\n{otp.now()}')
    else:
        print(HELP)

if __name__ == '__main__':
    main()