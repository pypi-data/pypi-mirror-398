#!/usr/bin/env python
'''
锐通的常用/共用函数(Common Function)，模块调用或命令行调用均可。
'''

VER = r'''
comm version: 2025.8.1.1.0
'''

COPR = r'''
版权所有 2025 锐码[rymaa.cn] 锐码署名传播许可证(RSPL) 授权。详情请见 LICENSE 或 LICENSE-EN 文件。| 网站: rymaa.cn | 邮箱: rybby@163.com
'''

INFO = r'''
锐通的常用/共用函数(Common Function)。
可通过模块调用，也可通过命令行调用。
包含一些实用函数
'''

HELP = r'''
+-------------------------------------------+
|           RyTo Common Functions           |
+-------------------------------------------+
|            HomePage: rymaa.cn             |
+-------------------------------------------+

Usage:
    rypi ryto comm [option]

Options:
    -H, --help   Show help / 显示帮助
    -I, --info   Show info / 显示信息
    -C, --copr   Show copyright / 显示版权
    -V, --version   Show version / 显示版本
    -h, --func_help   Show function help / 显示指定函数的帮助信息
    -f, --func   Show all function / 显示所有函数
    -r, --run   run function / 运行指定的函数
    -p, --para   function parameter / 运行函数的参数列表，多参数需要加引号
'''

##############################

import os
import sys
import re
import argparse
import importlib
import importlib.util
from pathlib import Path
import inspect
import shlex
import subprocess
import time

##############################

def _load(mname):
    '''
    载入指定名称的模块。
    返回: void
    参数列表：
        mname (str): 模块名（不含后缀，可以与包名组合）
    '''

    mod = importlib.import_module(mname)
    return mod

def _loadp(path):
    '''
    载入指定路径的模块。
    返回: void
    参数列表：
        path (str): 模块路径（包含后缀）
    '''

    name = path.replace('/', '_').replace('.', '_')
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

def _run_cmd(cmd, capout=False):
    if capout == False:
        stdout = None
        stderr = None
    else:
        stdout = subprocess.PIPE
        stderr = subprocess.PIPE
    res = subprocess.run(cmd, shell=True, text=True, check=False, timeout=60, stdout=stdout, stderr=stderr)
    return res
    
def _get_functions(mod):
    '''
    获取模块中所有函数名（排除 _ 开头的私有函数）。
    返回: 函数元组列表[(func_name, func_desc)]
    参数列表：
        mod (str): 模块（module name）
    '''

    no_func = ['main']
    func = [
        (name, (inspect.getdoc(obj) or '无描述').split('\n')[0].strip()) for name, obj in inspect.getmembers(mod, inspect.isfunction)
        if not name.startswith('_') and name not in no_func
    ]
    return func

def _parse_args(args):
    '''
    解析如 "arg1 arg2 'with space' --flag" 的字符串
    返回: 列表[str]
    参数列表：
        args (str): 参数列表（args string）
    '''

    res = {}
    args = args.strip()
    if not args:
        return res
    
    if '=' not in args:
        return shlex.split(args)
    
    # 使用 shlex 分词，支持引号
    lexer = shlex.shlex(args, posix=True)
    lexer.whitespace_split = True
    tokens = list(lexer)
    
    for tk in tokens:
        if '=' not in tk:
            raise ValueError(f"无效的键值对: {tk}")
        key, value = tk.split('=', 1)
        res[key] = value
    
    return res

def apt(path="/etc/apt/sources.list"):
    '''
    为 apt 包管理器配置多个国内源与官方源。
    
    该函数会生成包含清华、阿里云、中科大等国内镜像源以及 Ubuntu 官方源的完整 sources.list 内容，
    并将其写入指定路径的文件中（默认为 /etc/apt/sources.list）。
    
    参数列表：
        path (str): 目标 sources.list 文件的完整路径，默认为 "/etc/apt/sources.list"
    '''

    def _get_ubuntu_codename():
        """获取当前 Ubuntu 系统的 codename（如 jammy, noble, hirsute 等）"""
        try:
            result = _run_cmd("lsb_release -cs", capout=True)
            if result.returncode == 0:
                return result.stdout.strip().lower()
            else:
                # 尝试从 /etc/os-release 获取
                try:
                    with open('/etc/os-release', 'r') as f:
                        content = f.read()
                        # 查找 VERSION_CODENAME
                        match = re.search(r'VERSION_CODENAME=(\w+)', content)
                        if match:
                            return match.group(1).lower()
                        
                        # 查找 UBUNTU_CODENAME
                        match = re.search(r'UBUNTU_CODENAME=(\w+)', content)
                        if match:
                            return match.group(1).lower()
                except:
                    pass
                
                # 尝试从 /etc/lsb-release 获取
                try:
                    with open('/etc/lsb-release', 'r') as f:
                        content = f.read()
                        match = re.search(r'DISTRIB_CODENAME=(\w+)', content)
                        if match:
                            return match.group(1).lower()
                except:
                    pass
        except Exception:
            pass
        raise RuntimeError("无法确定 Ubuntu codename，请确保在 Ubuntu 系统上运行。")

    codename = _get_ubuntu_codename()
    print(f"检测到系统 Codename: {codename}")
    
    # Ubuntu 版本映射（用于显示）
    version_map = {
        "xenial": "16.04 LTS",
        "bionic": "18.04 LTS", 
        "focal": "20.04 LTS",
        "jammy": "22.04 LTS",
        "lunar": "23.04",
        "mantic": "23.10",
        "noble": "24.04 LTS",
        "hirsute": "21.04",
        "impish": "21.10",
        "kinetic": "22.10",
        "trusty": "14.04 LTS"
    }
    
    version_info = version_map.get(codename, "未知版本")
    print(f"Ubuntu 版本: {version_info} ({codename})")
    
    # 确保目录存在
    path = os.path.expanduser(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    ctt = f'''
# 清华镜像 (主源)
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ {codename} main restricted universe multiverse
deb-src https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ {codename} main restricted universe multiverse

# 阿里云镜像 (备用源1)
deb https://mirrors.aliyun.com/ubuntu/ {codename} main restricted universe multiverse
deb-src https://mirrors.aliyun.com/ubuntu/ {codename} main restricted universe multiverse

# 中科大镜像 (备用源2)
deb https://mirrors.ustc.edu.cn/ubuntu/ {codename} main restricted universe multiverse
deb-src https://mirrors.ustc.edu.cn/ubuntu/ {codename} main restricted universe multiverse

# 官方源 (最终备用)
deb http://archive.ubuntu.com/ubuntu/ {codename} main restricted universe multiverse
deb-src http://archive.ubuntu.com/ubuntu/ {codename} main restricted universe multiverse

# 安全更新
deb https://mirrors.aliyun.com/ubuntu/ {codename}-security main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ {codename}-security main restricted universe multiverse
deb http://security.ubuntu.com/ubuntu/ {codename}-security main restricted universe multiverse

# 软件更新
deb https://mirrors.aliyun.com/ubuntu/ {codename}-updates main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ {codename}-updates main restricted universe multiverse
deb http://archive.ubuntu.com/ubuntu/ {codename}-updates main restricted universe multiverse

# 向后兼容
deb https://mirrors.aliyun.com/ubuntu/ {codename}-backports main restricted universe multiverse
deb http://archive.ubuntu.com/ubuntu/ {codename}-backports main restricted universe multiverse
'''

    if os.path.isfile(path):
        _run_cmd(f'mv {path} {path}.bak')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(ctt.strip() + '\n')

    print(f'cat {path}\n')
    _run_cmd(f'cat {path}')

def pip(path=None):
    '''
    为 pip 包管理器配置多个国内源与官方源。

    该函数生成包含清华源（主源）、腾讯云源和 PyPI 官方源的 pip 配置内容，
    并写入指定的配置文件路径。若未指定路径，则根据操作系统自动选择默认位置：
    - Linux / macOS: ~/.pip/pip.conf
    - Windows: %APPDATA%\pip\pip.ini

    参数列表：
        path (str or None): pip 配置文件的完整路径。若为 None，则使用系统默认路径。
    '''
    
    # 自动确定默认配置路径
    if path is None:
        if os.name == 'nt':  # Windows
            path = os.path.join(os.environ.get('APPDATA', ''), 'pip', 'pip.ini')
        else:  # Linux / macOS
            path = '~/.pip/pip.conf'

    # 确保目录存在
    path = os.path.expanduser(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    ctt = '''
[global]
# 主镜像源 - 清华源
index-url = https://pypi.tuna.tsinghua.edu.cn/simple/

# 备用镜像源: 腾讯源, 官方源
extra-index-url =
    https://mirrors.cloud.tencent.com/pypi/simple/
    https://pypi.org/simple/

trusted-host =
    pypi.tuna.tsinghua.edu.cn
    mirrors.cloud.tencent.com
    pypi.org

timeout = 60
retries = 10
'''

    if os.path.isfile(path):
        _run_cmd(f'mv {path} {path}.bak')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(ctt.strip() + '\n')

    print(f'cat {path}\n')
    _run_cmd(f'cat {path}')

def conda(path=None):
    '''
    禁用 Conda 的自动激活 base 环境。

    该函数生成或更新 Conda 的配置文件（.condarc），设置 auto_activate_base 为 false，
    并保留常用的 channels 配置（conda-forge 和 defaults）。
    若未指定配置文件路径，则使用当前用户的默认 Conda 配置路径（~/.condarc）。

    参数列表：
        path (str or None): Conda 配置文件路径。若为 None，则默认为 ~/.condarc。
    '''
    
    if path is None:
        path = '~/.condarc'

    # 确保目录存在
    path = os.path.expanduser(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    ctt = '''
channels:
  - conda-forge
  - defaults
auto_activate_base: false
'''

    if os.path.isfile(path):
        _run_cmd(f'mv {path} {path}.bak')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(ctt.strip() + '\n')

    print(f'cat {path}\n')
    _run_cmd(f'cat {path}')

def nano(path=None):
    '''
    为 nano 启用鼠标支持并修改快捷键。

    参数列表：
        path (str or None): nano 配置文件的完整路径。若为 None，则使用系统默认路径。

    默认情况下，nano 编辑器不支持鼠标点击定位光标。它是一个纯键盘操作的终端文本编辑器。
    不过，新版本的 nano（2.0.0+）支持有限的鼠标功能，但需要手动启用。
    写入指定内容到配置文件。若未指定路径，则根据操作系统自动选择默认位置：
    - Linux / macOS: ~/.nanorc 或为全用户配置 /etc/nanorc

    该函数在配置文件添加以下内容：
    
    # 启用鼠标支持
    set mouse

    # 修改快捷键，^ 代表 Ctrl 键
    # 退出
    bind ^Q exit all

    # 保存文件
    bind ^S savefile main

    # 重写到新文件
    bind ^W writeout main

    # 剪切
    bind ^X cut all

    # 复制
    bind ^C copy main

    # 粘贴
    bind ^V paste all

    # 全选（实际是通过鼠标进行点选）
    bind ^A mark main

    # 撤销
    bind ^Z undo main

    # 重做
    bind ^Y redo main
    '''
    
    # 自动确定默认配置路径
    if path is None:
        path = '~/.nanorc'

    # 确保目录存在
    path = os.path.expanduser(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    ctt = '''
# 启用鼠标支持
set mouse

# 修改快捷键，^ 代表 Ctrl 键
# 退出
bind ^Q exit all

# 保存文件
bind ^S savefile main

# 重写到新文件
bind ^W writeout main

# 剪切
bind ^X cut all

# 复制
bind ^C copy main

# 粘贴
bind ^V paste all

# 全选（实际是通过鼠标进行点选）
bind ^A mark main

# 撤销
bind ^Z undo main

# 重做
bind ^Y redo main
'''

    if os.path.isfile(path):
        _run_cmd(f'mv {path} {path}.bak')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(ctt.strip() + '\n')

    print(f'cat {path}\n')
    _run_cmd(f'cat {path}')

def pkgpip(pkg=None):
    '''
    为 pip 源码进行打包并上传到官方源仓库然后安装。

    参数列表：
        pkg (str or None): pip 程序包名称，安装时代入。
    
    该函数自动完成以下操作流程

    1. 删除旧资源
    rm -rf dist/ build/ *.egg-info/
    或者
    rd /s /q dist
    rd /s /q build
    rd /s /q rypi.egg-info

    2. 构建
    python -m build

    3. 上传
    twine upload dist/*
    或者
    python -m twine upload dist/*

    4. 安装
    pip install --upgrade rypi -i https://pypi.org/simple

    PS: 上传过程可能需要进行双重验证，到 pypi 官网获取自己的 双重验证密钥，然后用 rypi ryto tfa 双重验证密钥 命令生成自己的 双重验证码 进行验证即可。操作时需要进入自己的项目根目录（通常是包名称）的上级目录，比如锐派的包名目录是 rypi，它的上级目录是 pjt_rypi，打包时就是在工程目录 pjt_rypi 下进行操作，rypi 目录下有各种模块和子模块。生产环境使用 pip install rypi 进行安装，开发环境使用 pip install -e . 进行安装。
    '''

    if not pkg:
        print('包名不能为空')
        return
    
    print('\n删除旧资源...')
    if os.name == 'nt':
        _run_cmd('rd /s /q dist')
        _run_cmd('rd /s /q build')
        _run_cmd(f'rd /s /q {pkg}.egg-info')
    else:
        _run_cmd('rm -rf dist/ build/ *.egg-info/')
    
    print('\n构建...')
    _run_cmd('python -m build')
    
    print('\n上传...')
    _run_cmd('twine upload dist/*')
    
    print('\n休眠 15 秒后安装...')
    time.sleep(15)
    cmd = f'pip install --upgrade {pkg} -i https://pypi.org/simple'
    print(f'\n安装: {cmd}\n')
    _run_cmd(cmd)
    
def cpl(name='python3'):
    '''
    为 python3 创建两个软链接：py, python
    参数列表：
        name (str): 当前 python 命令名，默认为 python3
    '''
    real_path = os.popen(f"readlink -f $(which {name})").read().strip()
    if not real_path or not os.path.isfile(real_path):
        raise RuntimeError("无法找到 python3 可执行文件")
    dirname = os.path.dirname(real_path)
    for cn in ["python", "py"]:
        os.system(f"sudo ln -sf '{real_path}' {dirname}/{cn}")

    pycmd = _run_cmd('py -V', capout=True).stdout.strip()
    python = _run_cmd('python -V', capout=True).stdout.strip()
    print(f'\n检查命令(py -V)：{pycmd}')
    print(f'\n检查命令(python -V)：{python}')

def main(args=None):
    '''
    入口主函数。
    返回: void
    参数列表：
        args (str): 参数列表，通过命令行传入或调用者传入。
    '''

    # 全局选项
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-H', '--help', action='store_true')
    parser.add_argument('-I', '--info', action='store_true')
    parser.add_argument('-C', '--copr', action='store_true')
    parser.add_argument('-V', '--version', action='store_true')
    parser.add_argument('-f', '--func', action='store_true')
    parser.add_argument('-h', '--func_help', default='')
    parser.add_argument('-r', '--run')
    parser.add_argument('-p', '--para', default='')

    args = parser.parse_args(args)
    
    if args.version:
        print(VER)
    elif args.copr:
        print(COPR)
    elif args.info:
        print(INFO)
    elif args.help:
        print(HELP)

    # 显示所有函数
    elif args.func:
        # mod = _load(f"{__package__}.{mname}")
        mod = sys.modules[__name__]
        funcs = _get_functions(mod)
        print(f'\n可以在参数(-h)后加函数名称查看该函数的帮助信息，如：rypi comm -h b64。')
        print(f'\n运行函数时输入的参数值可使用列表或字典两种模式，如：')
        print(f'\n列表模式：rypi comm -r sha -p "abcdef 2"')
        print(f'\n字典模式：rypi comm -r sha -p "data=abcdef type=2"')
        print(f'\n如果参数值有空格需要加引号，如：')
        print(f'\n列表模式：rypi comm -r sha -p "\'abc def\' 3"')
        print(f'\n字典模式：rypi comm -r sha -p "data=\'abc def\' type=3"')
        print(f'\nfunction list:')
        for name, desc in funcs:
            print(f'\n    {name}: {desc}')

    # 显示指定函数的帮助信息
    elif args.func_help:
        # mod = sys.modules[__name__]
        # func = getattr(mod, args.func_help, None)
        func = globals().get(args.func_help)
        if not func or not inspect.isfunction(func):
            print(f'函数 {args.run} 不存在或不是函数')
            return
        doc = inspect.getdoc(func) or '无描述'
        print(f'\n{doc}')

    # 运行指定函数
    elif args.run:
        # mod = sys.modules[__name__]
        # func = getattr(mod, args.run, None)
        func = globals().get(args.run)
        if not func or not inspect.isfunction(func):
            print(f'函数 {args.run} 不存在或不是函数')
            return

        # 解析参数
        plist = _parse_args(args.para)
        print(f'\n运行: {args.run}({plist})')
        if isinstance(plist, list):
            res = func(*plist)
        elif isinstance(plist, dict):
            res = func(**plist)
        else:
            raise TypeError(f"不支持的参数类型: {type(plist)}")
        print(f'\n运行结果: {res}')

    # 显示帮助
    else:
        print(HELP)

if __name__ == '__main__':
    main()