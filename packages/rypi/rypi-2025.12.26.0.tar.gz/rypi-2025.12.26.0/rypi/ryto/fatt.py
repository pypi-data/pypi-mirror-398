#!/usr/bin/env python
'''
字体属性提取工具(font attribute)。
'''

VER = r'''
faat version: 2025.8.1.1.0
'''

COPR = r'''
版权所有 2025 锐码[rymaa.cn] 本软件采用 锐码署名传播许可证(RSPL) 授权。详情请见 LICENSE 或 LICENSE-EN 文件。| 网站: rymaa.cn | 邮箱: rybby@163.com
'''

INFO = r'''
fatt: 字体属性提取工具(font attribute)

用于提取字体文件的名称、版权、协议等信息

安装依赖：
pip install fontTools

使用方法：

基本用法
python fatt -f /path/to/font.ttf

示例
python fatt -f /System/Library/Fonts/Arial.ttf
python fatt -f C:/Windows/Fonts/simhei.ttf

功能特点

多语言支持：优先显示中文名称，支持中英文字体信息提取

完整属性：提取字体名称、家族、版本、版权、制造商、设计师等信息

格式支持：支持 TTF、OTF、TTC 等常见字体格式

输出示例

┌──── 字体属性信息 ──────────────────────────────

中文全名: Noto Sans CJK SC

英文全名: Noto Sans CJK SC

家族名称: Noto Sans CJK SC

子家族名: Regular

脚本名称: NotoSansCJKsc-Regular

字体版本: Version 2.000;hotconv 1.0.107;makeotfexe 2.5.65593

版权声明: © 2014, 2015, 2018 Adobe (http://www.adobe.com/).

制造厂商: Adobe

合法商标: Noto is a trademark of Google Inc.

许可描述: This Font Software is licensed under the SIL Open Font License, Version 1.1. This Font Software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the SIL Open Font License for the specific language, permissions and limitations governing your use of this Font Software.

字体说明: Dr. Ken Lunde (project architect, glyph set definition & overall production); Masataka HATTORI 服部正貴 (production & ideograph elements)

字体作者: Ryoko NISHIZUKA 西塚涼子 (kana, bopomofo & ideographs); Paul D. Hunt (Latin, Greek & Cyrillic); Sandoll Communications 산돌커뮤니케이션, Soo-young JANG 장수영 & Joo-yeon KANG 강주연 (hangul elements, letters & syllables)

字体字重: 常规 (400: Normal/Regular)

字体宽度: 5

字体方向: 横向

创建时间: 2018-11-02 10:25:48

修改时间: 2018-11-02 10:25:48

厂商网址: http://www.google.com/get/noto/

作者网址: http://www.adobe.com/type/

许可网址: http://scripts.sil.org/OFL

└──────────────────────────────────
'''

HELP = r'''
+-------------------------------------------+
|           fatt: font attribute            |
+-------------------------------------------+
|            HomePage: rymaa.cn             |
+-------------------------------------------+

Usage:
    rypi ryto fatt [option]

Options:
    -H, --help   Show help / 显示帮助
    -I, --info   Show info / 显示信息
    -C, --copr   Show copyright / 显示版权
    -V, --version   Show version / 显示版本
    -f, --font   font file path / 字体文件路径
'''

##############################

import os
import sys
import argparse
from pathlib import Path

##############################

try:
    from fontTools.ttLib import TTFont
except ImportError:
    print("错误：请先安装 fontTools 库：pip install fontTools")
    sys.exit(1)

def extract_font_properties(font_path):
    '''
    提取字体文件的属性信息
    '''
    try:
        font = TTFont(font_path)
    except Exception as e:
        return {"error": f"无法读取字体文件: {e}"}
    
    properties = {}
    
    # 获取名称表（name table）
    name_table = font['name']
    en_name, zh_name = None, None

    # 定义名称ID对应的属性
    name_ids = {
        0: "版权声明",
        1: "家族名称",
        2: "子家族名", 
        4: "字体名称",
        5: "字体版本",
        6: "脚本名称",
        7: "合法商标",
        8: "制造厂商",
        9: "字体作者",
        10: "字体说明",
        11: "厂商网址",
        12: "作者网址",
        13: "许可描述",
        14: "许可网址",
        16: "首选家族",
        17: "首选子族",
        21: "网站名称",
        22: "网站地址"
    }
    
    # 提取各种语言的名称信息
    name_records = {}
    for record in name_table.names:
        name_id = record.nameID
        if name_id == 4:  # fullName
            try:
                name = record.toUnicode()
                # 覆盖更多可能的平台和语言组合
                if record.platformID == 3:  # Windows
                    if record.langID == 0x0409:  # en-US
                        en_name = name
                    elif record.langID == 0x0804:  # zh-CN
                        zh_name = name
                elif record.platformID == 1:  # Mac
                    if record.langID == 0:  # 英语（传统Mac格式）
                        en_name = name
            except UnicodeDecodeError:
                continue
            continue

        lang_code = f"{record.platformID}-{record.platEncID}-{record.langID}"
        
        try:
            text = record.toUnicode()
            if name_id not in name_records:
                name_records[name_id] = {}
            name_records[name_id][lang_code] = text
        except:
            continue
    
    # 设置字体全名
    properties["中文全名"] = zh_name
    properties["英文全名"] = en_name
    
    # 整理提取到的信息
    properties["文件路径"] = str(font_path)
    properties["文件大小"] = f"{os.path.getsize(font_path)} 字节"
    
    # 优先提取中文信息，如果没有则使用英文
    for name_id, desc in name_ids.items():
        if name_id in name_records:
            # 优先查找中文（简体）
            chinese_text = None
            english_text = None
            
            for lang_code, text in name_records[name_id].items():
                # 简单判断中文（根据平台和语言ID）
                if '3-1-2052' in lang_code or '1-0-0' in lang_code:  # 简体中文
                    chinese_text = text
                elif '3-1-1033' in lang_code or '1-0-0' in lang_code:  # 英文
                    english_text = text
            
            # 优先使用中文，如果没有则使用英文
            if chinese_text:
                properties[desc] = chinese_text
            elif english_text:
                properties[desc] = english_text
            else:
                # 如果没有找到中英文，使用第一个可用的文本
                first_text = list(name_records[name_id].values())[0]
                properties[desc] = first_text
    
    # 获取OS/2表信息（如果存在）
    if 'OS/2' in font:
        os2 = font['OS/2']
        properties["字体字重"] = os2.usWeightClass
        properties["字体宽度"] = os2.usWidthClass
        # properties["嵌入权限"] = os2.fsType
    
    # 获取head表信息
    if 'head' in font:
        head = font['head']
        properties["创建时间"] = head.created
        properties["修改时间"] = head.modified
        properties["字体方向"] = "横向" if head.macStyle == 0 else "纵向"
    
    font.close()
    return properties

def format_output(properties):
    '''格式化输出'''
    if "error" in properties:
        print(f"错误: {properties['error']}")
        return
    
    print()
    print("┌──── 字体属性信息 " + "─" * 30)
    
    display_order = [
        "中文全名",
        "英文全名",
        "家族名称", 
        "子家族名",
        "首选家族",
        "首选子族",
        "脚本名称",
        "字体版本",
        "字体路径",
        "字体大小",
        "版权声明",
        "制造厂商",
        "合法商标",
        "许可描述",
        "字体说明",
        "字体作者",
        "字体字重",
        "字体宽度",
        "字体方向",
        "创建时间",
        "修改时间"
    ]
    
    for key in display_order:
        if key in properties and properties[key]:
            value = properties[key]
            if key == "字体字重":
                # 将数字字重转换为描述
                weight_map = {
                    100: "细体 (100: Thin)",
                    200: "特细体 (200: Extra-Light)", 
                    300: "细体 (300: Light)",
                    400: "常规 (400: Normal/Regular)",
                    500: "中等 (500: Medium)",
                    600: "半粗体 (600: Semi-Bold)",
                    700: "粗体 (700: Bold)",
                    800: "特粗体 (800: Extra-Bold)",
                    900: "黑体 (900: Black)"
                }
                value = weight_map.get(value, value)
            elif key in ["创建时间", "修改时间"]:
                # 转换时间格式（从1904年1月1日开始的秒数）
                from datetime import datetime, timedelta
                try:
                    base_date = datetime(1904, 1, 1)
                    actual_date = base_date + timedelta(seconds=value)
                    value = actual_date.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    value = str(value)
            
            print(f"\n{key}: {value}")
    
    # 显示其他未在预定顺序中的属性
    for key, value in properties.items():
        if key not in display_order and key not in ["文件路径", "文件大小", "error"]:
            print(f"\n{key}: {value}")
    
    print()
    print("└────" + "─" * 30)

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
    parser.add_argument('-f', '--font', default='')

    args = parser.parse_args(args)

    if args.version:
        print(VER)
    elif args.copr:
        print(COPR)
    elif args.info:
        print(INFO)
    elif args.font:
        font_path = Path(args.font)
        if not font_path.exists():
            print(f"错误: 文件不存在: {font_path}")
            sys.exit(1)
        
        if font_path.suffix.lower() not in ['.ttf', '.otf', '.ttc']:
            print(f"警告: 文件可能不是支持的字体格式: {font_path.suffix}")
            print("支持的格式: .ttf, .otf, .ttc")
        
        properties = extract_font_properties(font_path)
        format_output(properties)
    else:
        print(HELP)

if __name__ == '__main__':
    main()