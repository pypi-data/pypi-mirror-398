#!/usr/bin/env python
'''
显示一些常用镜像仓库的国内链接地址。
'''

VER = r'''
mir version: 2025.8.1.1.0
'''

COPR = r'''
版权所有 2025 锐码[rymaa.cn] 本软件采用 锐码署名传播许可证(RSPL) 授权。详情请见 LICENSE 或 LICENSE-EN 文件。| 网站: rymaa.cn | 邮箱: rybby@163.com
'''

INFO = r'''
mir: 显示一些常用镜像仓库的国内链接地址
包括 pypi库和各种 linux 平台的软件仓库
'''

HELP = r'''
+-------------------------------------------+
|        show pythonPkg mirror link         |
+-------------------------------------------+
|            HomePage: rymaa.cn             |
+-------------------------------------------+

Usage:
    rypi ryto mir [option]

Options:
    -H, --help   Show help / 显示帮助
    -I, --info   Show info / 显示信息
    -C, --copr   Show copyright / 显示版权
    -V, --version   Show version / 显示版本
    -c, --conda   Show conda mir link / 显示康达软件镜像仓库链接地址
    -d, --docker   Show docker mir link / 显示刀客容器镜像仓库链接地址
    -m, --macos   Show macos mir link / 显示 macos 软件镜像仓库链接地址
    -p, --pypi   Show pypi mir link / 显示 pypi 库镜像链接地址
    -r, --redhat   Show redhat,centos mir link / 显示红帽软件镜像仓库链接地址
    -u, --debian   Show ubuntu,debian mir link / 显示乌班图软件镜像仓库链接地址
'''

CON = r'''

Conda 国内镜像加速
bash
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/msys2/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/bioconda/
conda config --set show_channel_urls yes

禁用自动激活 base 环境
bash
conda config --set auto_activate_base false

安装 Conda（Miniconda 或 Anaconda）的步骤如下：

1. 选择 Conda 发行版

Miniconda（推荐）：轻量版，仅包含 Conda 和 Python 基础环境，按需安装其他包。

Anaconda：完整版，预装大量科学计算包，占用空间较大（约 3GB）。

2. 下载安装脚本

下载地址：

Miniconda: https://docs.conda.io/en/latest/miniconda.html

Anaconda: https://www.anaconda.com/products/distribution

在终端执行以下命令下载 Miniconda（以 Linux x86_64 为例）：

bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
如需其他版本，替换链接中的 Linux-x86_64（如 Linux-aarch64 适用于 ARM 芯片）。

Miniconda3 安装脚本国内镜像源 下载地址

1. 清华大学镜像站 (推荐)
https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/

Miniconda3-latest-Linux-aarch64.sh	145.7 MiB	2025-07-19 02:45
https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-latest-Linux-aarch64.sh

Miniconda3-latest-Linux-armv7l.sh	29.9 MiB	2025-02-14 03:43
https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-latest-Linux-armv7l.sh

Miniconda3-latest-Linux-ppc64le.sh	94.9 MiB	2025-02-14 03:43
https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-latest-Linux-ppc64le.sh

Miniconda3-latest-Linux-s390x.sh	143.4 MiB	2025-02-14 03:43
https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-latest-Linux-s390x.sh

Miniconda3-latest-Linux-x86.sh	62.7 MiB	2025-02-14 03:43
https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-latest-Linux-x86.sh

Miniconda3-latest-Linux-x86_64.sh	152.6 MiB	2025-07-19 02:45
https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-latest-Linux-x86_64.sh

Miniconda3-latest-MacOSX-arm64.pkg	108.8 MiB	2025-07-19 02:45
https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-latest-MacOSX-arm64.pkg

Miniconda3-latest-MacOSX-arm64.sh	109.5 MiB	2025-07-19 02:45
https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-latest-MacOSX-arm64.sh

Miniconda3-latest-MacOSX-x86.sh	26.0 MiB	2025-02-14 03:43
https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-latest-MacOSX-x86.sh

Miniconda3-latest-MacOSX-x86_64.pkg	112.2 MiB	2025-07-19 02:45
https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-latest-MacOSX-x86_64.pkg

Miniconda3-latest-MacOSX-x86_64.sh	112.8 MiB	2025-07-19 02:45
https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-latest-MacOSX-x86_64.sh

Miniconda3-latest-Windows-x86.exe	67.8 MiB	2025-02-14 03:43
https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-latest-Windows-x86.exe

Miniconda3-latest-Windows-x86_64.exe	88.2 MiB	2025-07-19 02:45
https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-latest-Windows-x86_64.exe

2. 中科大镜像站
https://mirrors.ustc.edu.cn/anaconda/miniconda/

Miniconda3-latest-Linux-aarch64.sh                 19-Jul-2025 02:45           152,742,878
https://mirrors.ustc.edu.cn/anaconda/miniconda/Miniconda3-latest-Linux-aarch64.sh

Miniconda3-latest-Linux-armv7l.sh                  14-Feb-2025 03:43            31,334,793
https://mirrors.ustc.edu.cn/anaconda/miniconda/Miniconda3-latest-Linux-armv7l.sh

Miniconda3-latest-Linux-x86.sh                     14-Feb-2025 03:43            65,741,329
https://mirrors.ustc.edu.cn/anaconda/miniconda/Miniconda3-latest-Linux-x86.sh

Miniconda3-latest-Linux-x86_64.sh                  19-Jul-2025 02:45           160,039,710
https://mirrors.ustc.edu.cn/anaconda/miniconda/Miniconda3-latest-Linux-x86_64.sh

Miniconda3-latest-MacOSX-arm64.pkg                 19-Jul-2025 02:45           114,105,865
https://mirrors.ustc.edu.cn/anaconda/miniconda/Miniconda3-latest-MacOSX-arm64.pkg

Miniconda3-latest-MacOSX-arm64.sh                  19-Jul-2025 02:45           114,835,350
https://mirrors.ustc.edu.cn/anaconda/miniconda/Miniconda3-latest-MacOSX-arm64.sh

Miniconda3-latest-MacOSX-x86.sh                    14-Feb-2025 03:43            27,228,109
https://mirrors.ustc.edu.cn/anaconda/miniconda/Miniconda3-latest-MacOSX-x86.sh

Miniconda3-latest-MacOSX-x86_64.pkg                19-Jul-2025 02:45           117,653,053
https://mirrors.ustc.edu.cn/anaconda/miniconda/Miniconda3-latest-MacOSX-x86_64.pkg

Miniconda3-latest-MacOSX-x86_64.sh                 19-Jul-2025 02:45           118,297,456
https://mirrors.ustc.edu.cn/anaconda/miniconda/Miniconda3-latest-MacOSX-x86_64.sh

Miniconda3-latest-Windows-x86.exe                  14-Feb-2025 03:43            71,081,736
https://mirrors.ustc.edu.cn/anaconda/miniconda/Miniconda3-latest-Windows-x86.exe

Miniconda3-latest-Windows-x86_64.exe               19-Jul-2025 02:45            92,478,432
https://mirrors.ustc.edu.cn/anaconda/miniconda/Miniconda3-latest-Windows-x86_64.exe

3. 运行安装脚本

bash
bash Miniconda3-latest-Linux-x86_64.sh
按提示操作：

阅读许可协议，按 Enter 继续，输入 yes 同意条款。

设置安装路径（默认 ~/miniconda3），直接按 Enter 使用默认路径。

询问是否初始化 Conda，输入 yes（会自动将 Conda 添加到 ~/.bashrc）。

4. 激活 Conda

关闭并重新打开终端，或运行以下命令使配置生效：

bash
source ~/.bashrc
验证安装：

bash
conda --version
# 输出类似：conda 23.11.0

5. 配置 Conda（可选）

换国内镜像加速
bash
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/
conda config --set show_channel_urls yes

禁用自动激活 base 环境
bash
conda config --set auto_activate_base false
新版命令是
conda config --set auto_activate false

6. 基本使用示例

bash
# 创建新环境
conda create --name my_env python=3.9

# 激活环境
conda activate my_env

# 安装包（如 numpy）
conda install numpy

# 退出环境
conda deactivate

常见问题

权限问题

如果无法写入默认路径，改用 sudo bash Miniconda3-latest-Linux-x86_64.sh 并指定可写路径（如 /opt/miniconda3）。

非管理员用户建议安装在 ~/miniconda3。

Shell 不识别 conda 命令

确保 ~/.bashrc 中有以下内容（安装时选 yes 会自动添加）：

bash
export PATH="~/miniconda3/bin:$PATH"
手动添加后运行 source ~/.bashrc。

卸载 Conda

bash
rm -rf ~/miniconda3  # 删除安装目录
nano ~/.bashrc       # 删除 PATH 中的 Conda 相关行

总结

推荐使用 Miniconda 节省空间。

通过 conda activate 管理环境，避免包冲突。

换国内镜像可大幅提升下载速度。
'''

DOC = r'''

方法一: 临时使用镜像站

bash
docker run --rm -it registry.cn-hangzhou.aliyuncs.com/library/python:3.8 pip install jnius

方法二: 永久修改配置

Linux/macOS: 

bash
sudo tee /etc/docker/daemon.json << 'EOF'
{
  "registry-mirrors": [
    "https://registry.cn-hangzhou.aliyuncs.com",
    "https://docker.mirrors.ustc.edu.cn"
  ],
  "ipv6": false,
  "dns": ["1.1.1.1", "8.8.8.8"]
}
EOF
sudo systemctl restart docker

Windows: 

右键 Docker 托盘图标 → Settings → Docker Engine

添加镜像地址: 

json
{
  "registry-mirrors": [
    "https://registry.cn-hangzhou.aliyuncs.com",
    "https://docker.mirrors.ustc.edu.cn"
  ],
  "ipv6": false,
  "dns": ["1.1.1.1", "8.8.8.8"]
}
点击 "Apply & Restart"
'''

MAC = r'''

'''

PYPI = r'''

以下国内镜像源更稳定, 按优先级推荐: 

清华源: https://pypi.tuna.tsinghua.edu.cn/simple

阿里云源: https://mirrors.aliyun.com/pypi/simple

腾讯云源: https://mirrors.cloud.tencent.com/pypi/simple

华为云源: https://repo.huaweicloud.com/repository/pypi/simple

豆瓣: https://pypi.doubanio.com/simple/

中科大: https://pypi.mirrors.ustc.edu.cn/simple/

方法 1: 临时使用镜像源

在安装包时通过 -i 参数指定镜像源: 

bash
pip install 包名 -i https://pypi.tuna.tsinghua.edu.cn/simple

方法 2: 永久修改 pip 源

Windows 系统
在用户目录下创建 pip 文件夹（如 C:\Users\你的用户名\pip）。

在文件夹内新建文件 pip.ini, 写入以下内容: 

ini
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
如果使用其他源, 替换 index-url 即可（如阿里云 https://mirrors.aliyun.com/pypi/simple/）。

Linux/macOS 系统

创建配置文件（当前用户生效）

bash
mkdir -p ~/.pip  # 如果目录不存在则创建
echo "[global]\nindex-url = https://pypi.tuna.tsinghua.edu.cn/simple\ntrusted-host = pypi.tuna.tsinghua.edu.cn" > ~/.pip/pip.conf

创建全局配置文件（所有用户生效）

bash
sudo mkdir -p /etc/pip  # 确保目录存在
sudo echo "[global]\nindex-url = https://pypi.tuna.tsinghua.edu.cn/simple\ntrusted-host = pypi.tuna.tsinghua.edu.cn" > /etc/pip.conf

方法 3: 通过命令行直接配置

运行以下命令自动修改配置: 

bash
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
'''

RED = r'''

'''

UBU = r'''

'''

##############################

import argparse

##############################

def main(args=None):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-H', '--help', action='store_true')
    parser.add_argument('-I', '--info', action='store_true')
    parser.add_argument('-C', '--copr', action='store_true')
    parser.add_argument('-V', '--version', action='store_true')
    parser.add_argument('-c', '--conda', action='store_true')
    parser.add_argument('-d', '--docker', action='store_true')
    parser.add_argument('-m', '--macos', action='store_true')
    parser.add_argument('-p', '--pypi', action='store_true')
    parser.add_argument('-r', '--redhat', action='store_true')
    parser.add_argument('-u', '--ubuntu', action='store_true')

    args = parser.parse_args(args)

    if args.version:
        print(VER)
    elif args.copr:
        print(COPR)
    elif args.info:
        print(INFO)
    elif args.conda:
        print(CON)
    elif args.docker:
        print(DOC)
    elif args.macos:
        print(MAC)
    elif args.pypi:
        print(PYPI)
    elif args.redhat:
        print(RED)
    elif args.ubuntu:
        print(UBU)
    else:
        print(HELP)

if __name__ == '__main__':
    main()