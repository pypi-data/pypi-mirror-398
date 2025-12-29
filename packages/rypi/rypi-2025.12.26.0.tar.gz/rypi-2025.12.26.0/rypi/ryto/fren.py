#!/usr/bin/env python
'''
fren: font rename，字体重全名。
'''

VER = r'''
fren version: 2025.10.12.1.0
'''

COPR = r'''
版权所有 2025 锐码[rymaa.cn] 本软件采用 锐码署名传播许可证(RSPL) 授权。详情请见 LICENSE 或 LICENSE-EN 文件。| 网站: rymaa.cn | 邮箱: rybby@163.com
'''

INFO = r'''
功能说明
字体重全名与查看字体属性：显示字体名称、版权、版本等信息。

两个参数:

-p: 字体文件或目录路径

-r: 是否重命名(0=不重命名, 1=重命名)

重命名字体文件: 规则: 字体的中文全名 - [字体的英文全名], 如果字体没有中文名则取原文件名的中文日文韩文部分

示例: 

有中文全名: 思源黑体(Bold) - [SourceHanSans-Bold].ttf

无中文全名: Roboto-Bold.ttf

使用说明

1. 查看字体信息
rypi ryto fren -p /path/to/font.ttf

输出示例：
文件: font.ttf
中文全名: 思源黑体(Bold)
英文全名: Source Han Sans

2. 重命名字体文件
rypi ryto fren -p /path/to/fonts/font.ttf -r 1

重命名结果示例：
原文件：font.ttf
新文件：思源黑体(Bold) - [Source Han Sans].ttf

3. 批量处理目录
rypi ryto fren -p /path/to/fonts/ -r 1

注意事项

依赖安装：
pip install fonttools

若python版本低于或等于3.4，请安装下面的版本
pip install "fonttools==3.44.0"

非法字符：脚本会自动过滤 \/:*?"<>| 等非法字符。

文件名冲突：如果新文件名已存在，会因系统限制导致重命名失败。

此脚本适用于大多数 OpenType/TrueType 字体，并已处理多语言和文件名合法性。


TTFont 核心 Name ID 属性
Name ID	属性名 (常用)	说明
0	copyright	字体版权信息（如 © 2023 Adobe Systems）
1	fontFamily	字体家族名称（如 "Roboto"）
2	fontSubfamily	字体子家族/样式（如 "Bold"）
3	uniqueID	唯一标识符（通常已弃用）
4	fullName	字体全名（如 "Roboto Bold"）
5	version	字体版本（如 "Version 3.001"）
6	postscriptName	PostScript 名称（如 "Roboto-Bold"）
7	trademark	商标信息
8	manufacturer	制造商名称（如 "Adobe"）
9	designer	设计师名字
10	description	字体描述文本
11	vendorURL	制造商网址（如 "https://adobe.com"）
12	designerURL	设计师网址
13	license	许可证描述（非法律条款）
14	licenseURL	许可证链接
16	preferredFamily	首选家族名（多语言支持时使用）
17	preferredSubfamily	首选子家族名
18	compatibleFullName	兼容全名（旧系统用）
19	sampleText	示例文本（如 "aA"）
'''

HELP = r'''
+-------------------------------------------+
|         font rename or view info          |
+-------------------------------------------+
|            HomePage: rymaa.cn             |
+-------------------------------------------+

Usage:
    rypi ryto fren [option]

Options:
    -H, --help   Show help / 显示帮助
    -I, --info   Show info / 显示信息
    -C, --copr   Show copyright / 显示版权
    -V, --version   Show version / 显示版本
    -p, --path   font path / 字体文件路径
    -r, --rename   is rename / 是否重命名字体，重命名模式: 0=不重命名, 1=重命名规则: 字体的中文全名 - [字体的英文全名], 如果字体没有中文名则取原文件名的中文日文韩文部分
'''

##############################

import os
import re
import argparse
import random
import string
from fontTools.ttLib import TTFont
import random
import string

##############################

def rstr(type: str = 'lun', len: int = 8) -> str:
    '''
    生成指定类型和长度的随机字符串。

    函数原型:
        rstr(type: str, len: int) -> str

    返回值:
        str: 生成的随机字符串

    参数列表:
        type (str): 字符集类型，可选值：
            - 'l'  : 小写字母（a-z）
            - 'u'  : 大写字母（A-Z）
            - 'n'  : 数字（0-9）
            - 'lu' : 小写 + 大写
            - 'ln' : 小写 + 数字
            - 'un' : 大写 + 数字
            - 'lun': 小写 + 大写 + 数字
        len (int): 随机字符串长度，必须 > 0，默认为 8

    使用示例1:
        rstr('lu', 6) → 可能返回 "Ab3XyZ"

    使用示例2:
        rstr('n', 4) → 可能返回 "7291"

    注意:
        - 如果 type 不在支持列表中，抛出 ValueError
        - len 必须是正整数
    '''

    len = int(len)

    # 构建字符集
    chars = ''
    if 'l' in type:
        chars += string.ascii_lowercase
    if 'u' in type:
        chars += string.ascii_uppercase
    if 'n' in type:
        chars += string.digits

    if not chars:
        raise ValueError("type 必须包含 l, u, n 中至少一个")

    if len < 1:
        raise ValueError("len 必须大于 0")

    return ''.join(random.choices(chars, k=len))

def sanitize_filename(text):
    '''清理文件名中的非法字符'''
    if not text:
        return text
    illegal_chars = r'[\/:*?"<>|]'
    text = re.sub(illegal_chars, "", text)
    return text

def is_cjk(text):
    '''
    是否包含中文、日文、韩文
    print(is_cjk("Hello"))     # False
    print(is_cjk("你好"))      # True
    print(is_cjk("こんにちは")) # True（日文）
    print(is_cjk("안녕하세요")) # True（韩文）
    '''
    if not isinstance(text, str):
        return False
    return re.search(r'[\u4e00-\u9fff\u3400-\u4dbf\u3040-\u30ff\uac00-\ud7af]', text) is not None

def is_cjk_or_ascii(c):
    cp = ord(c)
    return (
        cp <= 127 or  # ASCII（英文、数字、基本符号）
        0x4E00 <= cp <= 0x9FFF or  # 中文（基本汉字）
        0x3400 <= cp <= 0x4DBF or  # 中文（扩展A汉字）
        0x3040 <= cp <= 0x30FF or  # 日文（平假名 + 片假名）
        0xAC00 <= cp <= 0xD7AF or  # 韩文（谚文）
        c in '()[]（）【】-_,. '  # 额外允许的符号
    )

def replace_non_cjk(text, replace_char=''):
    '''
    # 测试
    text = "Hello你好こんにちは안녕하세요【𝄞】"
    clean_text = replace_non_cjk(text, '?')
    print(clean_text)  # 输出: Hello你好こんにちは안녕하세요【?】
    '''
    return ''.join(c if (is_cjk_or_ascii(c) and (c != '?')) else replace_char for c in text)

def is_constr2ucted_by_str2(str1, str2):
    # 找到 str2 第一次出现的位置
    first_occurrence = str1.find(str2)
    if first_occurrence == -1:
        return False  # str2 不在字符串中
    
    # 检查后面的部分是否完全由 str2 重复构成
    remaining_str2 = str1[first_occurrence:]
    return remaining_str2 == str2 * (len(remaining_str2) // len(str2))

def is_constructed_by_any_substring_of_str2(str1, str2):
    for i in range(1, len(str2) + 1):
        substring = str2[:i]
        if str1 == substring * (len(str1) // len(substring)):
            return True
    return False

def get_font_names(font_path):
    '''获取字体的中英文全名'''
    try:
        font = TTFont(font_path)
    except Exception as e:
        print("\n错误：无法读取字体文件 {} - {}".format(font_path, str(e)).encode('gbk', errors='ignore').decode('gbk'))
        return None, None
    
    name_table = font["name"]
    en_name, zh_name = None, None

    for entry in name_table.names:
        if entry.nameID == 4:  # fullName
            try:
                name = entry.toUnicode()
                name = replace_non_cjk(name, '-')
                # 覆盖更多可能的平台和语言组合
                if entry.platformID == 3:  # Windows
                    if entry.langID == 0x0409:  # en-US
                        en_name = name
                    elif entry.langID == 0x0804:  # zh-CN
                        zh_name = name
                elif entry.platformID == 1:  # Mac
                    if entry.langID == 0:  # 英语（传统Mac格式）
                        en_name = name
            except UnicodeDecodeError:
                continue
    font.close()
    
    return zh_name, en_name

def generate_new_name(zh_name, en_name, ext, original_name=None, rename_mode=0):
    '''
    param rename_mode:
    生成符合规则的字体文件名
    重命名模式:
    0=不重命名
    1=重命名规则：字体的中文全名(字体的英文全名)
    如果字体没有中文名则取原文件名的中文日文韩文部分
    '''
    # 清理非法字符
    zh_name = sanitize_filename(zh_name) if zh_name else None
    en_name = sanitize_filename(en_name) if en_name else None
    original_name = sanitize_filename(original_name) if original_name else None

    # 模式2：使用原文件名中的中文部分
    if rename_mode > 0:
        if original_name:
            # 如果字体有中文名且不是英语字符则用字体的中文名
            if zh_name and is_cjk(zh_name):
                zh_name = zh_name
            else:
                # 否则用原文件名的中文名
                original_zh = original_name.split(" - [")[0]
                if original_zh and en_name:
                    like1 = is_constr2ucted_by_str2(original_zh, en_name)
                    like2 = is_constructed_by_any_substring_of_str2(original_zh, en_name)
                    if like1 or like2 or not is_cjk(original_zh):
                        # 如果原名和英文名相似或原名由英文名拼接组成的则用英文名
                        # 或者原名非中文名也用字体的英文名
                        zh_name = en_name
                    else:
                        zh_name = original_zh
                elif original_zh:
                    zh_name = original_zh

    # 生成新文件名
    if zh_name and en_name:
        if zh_name == en_name:
            new_name = "{}{}".format(zh_name, ext)
        else:
            new_name = "{} - [{}]{}".format(zh_name, en_name, ext)
    elif zh_name:
        new_name = "{}{}".format(zh_name, ext)
    elif en_name:
        new_name = "{}{}".format(en_name, ext)  # 只有英文名时不加括号
    else:
        new_name = "未知字体名称_" + rstr() + ext

    # 最终检查：确保文件名长度合理
    return new_name[:200] if len(new_name) > 200 else new_name

def process_font(path, rename_mode=0):
    '''处理单个字体文件'''
    if not os.path.isfile(path):
        return False

    ext = os.path.splitext(path)[1].lower()
    if ext not in (".ttf", ".otf", ".woff", ".woff2"):
        return False

    zh_name, en_name = get_font_names(path)
    original_name = os.path.splitext(os.path.basename(path))[0]
    
    print("\n原文件名: {}".format(original_name or '无').encode('gbk', errors='ignore').decode('gbk'))
    print("中文全名: {}".format(zh_name or '无').encode('gbk', errors='ignore').decode('gbk'))
    print("英文全名: {}".format(en_name or '无').encode('gbk', errors='ignore').decode('gbk'))
    # print("英文全名: {}".format(en_name or '无'))
    # safe_name = (en_name or '无').encode('gbk', errors='replace').decode('gbk')
    # print("英文全名: {}".format(safe_name))

    if rename_mode > 0:
        new_name = generate_new_name(
            zh_name, en_name, ext, 
            original_name=original_name, 
            rename_mode=rename_mode
        )
        if new_name:
            new_path = os.path.join(os.path.dirname(path), new_name)
            try:
                os.rename(path, new_path)
                print("新文件名: {}".format(new_name).encode('gbk', errors='ignore').decode('gbk'))
            except OSError as e:
                new_name2 = new_name +'_'+ rstr() + ext
                new_path2 = os.path.join(os.path.dirname(path), new_name2)
                os.rename(path, new_path2)
                print("新命名失败: {}".format(e).encode('gbk', errors='ignore').decode('gbk'))
                print("使用新文件名取代: {}".format(new_name2).encode('gbk', errors='ignore').decode('gbk'))
        else:
            print("无法生成有效的新文件名")
    return True

def process_directory(directory, rename_mode=0):
    '''处理目录下的所有字体文件'''
    if not os.path.isdir(directory):
        print("错误: {} 不是有效目录".format(directory).encode('gbk', errors='ignore').decode('gbk'))
        return

    for root, _, files in os.walk(directory):
        for file in files:
            process_font(os.path.join(root, file), rename_mode)

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
    parser.add_argument("-p", "--path", default='')
    parser.add_argument("-r", "--rename", type=int, choices=[0, 1], default=0)

    args = parser.parse_args(args)

    if args.version:
        print(VER)
    elif args.copr:
        print(COPR)
    elif args.info:
        print(INFO)
    elif args.path:
        if os.path.isfile(args.path):
            process_font(args.path, args.rename)
        elif os.path.isdir(args.path):
            process_directory(args.path, args.rename)
    else:
        print(HELP)

if __name__ == '__main__':
    main()