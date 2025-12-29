#!/usr/bin/env python3
'''
自动挂载数据盘脚本(auto mount data disk)
'''

VER = r'''
amdd version: 2025.12.26.0
'''

COPR = r'''
版权所有 2025 锐码[rymaa.cn] 锐码署名传播许可证(RSPL) 授权。详情请见 LICENSE 或 LICENSE-EN 文件。| 网站: rymaa.cn | 邮箱: rybby@163.com
'''

INFO = r'''
自动挂载数据盘脚本(auto mount data disk)
功能：
1. 识别未挂载的数据盘
2. 格式化数据盘（可选）
3. 挂载到指定目录
4. 设置开机自动挂载
5. 备份原 fstab 文件
'''

HELP = r'''
+-------------------------------------------+
|           Auto Mount Data Disk            |
+-------------------------------------------+
|            HomePage: rymaa.cn             |
+-------------------------------------------+

Usage:
    rypi ryto amdd [option]

Options:
    -H, --help   Show help / 显示帮助
    -I, --info   Show info / 显示信息
    -C, --copr   Show copyright / 显示版权
    -V, --version   Show version / 显示版本
    -p, --path   Mount path / 挂载路径
    -f, --format   Format disk / 格式化磁盘
    -t, --type   File system type / 文件系统类型(默认: ext4)
    
用法
交互式挂载：rypi ryto amdd
指定挂载路径：rypi ryto amdd -p /data
格式化并挂载：rypi ryto amdd -p /data -f
使用 XFS 文件系统：rypi ryto amdd -p /data -f -t xfs
'''

##############################

import os
import sys
import subprocess
import argparse
import re
import shutil
import time
from datetime import datetime

##############################

class DiskMounter:
    def __init__(self, mount_path=None, format_disk=False, filesystem='ext4'):
        """
        初始化挂载器
        :param mount_path: 挂载路径
        :param format_disk: 是否格式化磁盘
        :param filesystem: 文件系统类型
        """
        self.mount_path = mount_path
        self.format_disk = format_disk
        self.filesystem = filesystem
        self.data_disk = None
        self.mount_point = None
        
        # 颜色输出
        self.GREEN = '\033[92m'
        self.YELLOW = '\033[93m'
        self.RED = '\033[91m'
        self.BLUE = '\033[94m'
        self.ENDC = '\033[0m'
        self.BOLD = '\033[1m'
    
    def print_colored(self, text, color=''):
        """彩色输出"""
        if color and sys.stdout.isatty():
            print(f"{color}{text}{self.ENDC}")
        else:
            print(text)
    
    def run_command(self, cmd, capture_output=True, check=False):
        """执行命令并返回结果"""
        try:
            if capture_output:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
                return result.stdout.strip()
            else:
                subprocess.run(cmd, shell=True, check=check)
                return True
        except subprocess.CalledProcessError as e:
            # 对于某些命令，没有输出是正常的
            if "blkid" in cmd and e.returncode == 2:
                # blkid 返回 2 表示没有找到文件系统，这是正常情况
                return ""
            if "grep" in cmd and e.returncode == 1:
                # grep 没有找到匹配项
                return ""
            if check:
                raise
            return None
    
    def get_disk_info(self):
        """获取磁盘信息"""
        disks_info = []
        
        # 获取所有磁盘设备
        output = self.run_command("lsblk -o NAME,TYPE,SIZE,MOUNTPOINT -n")
        if output is None:
            return disks_info
        
        lines = output.strip().split('\n')
        
        # 先找出所有磁盘设备
        disks = []
        current_disk = None
        
        for line in lines:
            if not line.strip():
                continue
                
            parts = line.strip().split(None, 3)
            if len(parts) < 3:
                continue
                
            # 清理设备名中的特殊字符
            raw_name = parts[0]
            name = raw_name.replace('├─', '').replace('└─', '').replace('│', '').strip()
            dev_type = parts[1]
            size = parts[2]
            mountpoint = parts[3] if len(parts) > 3 else ""
            
            # 如果是磁盘设备（不是loop设备）
            if dev_type == 'disk' and not name.startswith('loop'):
                disks.append({
                    'name': name,
                    'raw_name': raw_name,  # 保存原始名称用于显示
                    'device': f"/dev/{name}",
                    'size': size,
                    'mounted': False,
                    'mountpoints': [],  # 所有挂载点
                    'is_system': False,
                    'has_partitions': False
                })
                current_disk = name
            # 如果是分区或逻辑卷
            elif dev_type in ['part', 'lvm'] and current_disk:
                # 找到对应的磁盘
                for disk in disks:
                    if disk['name'] == current_disk:
                        disk['has_partitions'] = True
                        if mountpoint:  # 如果有挂载点
                            disk['mounted'] = True
                            disk['mountpoints'].append(mountpoint)
                            # 如果是系统挂载点，标记为系统盘
                            if mountpoint in ['/', '/boot', '/home', '/var', '/usr']:
                                disk['is_system'] = True
                        break
        
        # 获取磁盘型号
        for disk in disks:
            model = self.run_command(f"lsblk -o MODEL /dev/{disk['name']} -n -d")
            if model and not model.isspace():
                disk['model'] = model.strip()
            else:
                disk['model'] = "Unknown"
        
        return disks
    
    def select_data_disk(self, disks):
        """选择数据盘"""
        if not disks:
            self.print_colored("未找到可用的数据盘！", self.RED)
            return None
        
        # 显示所有磁盘状态
        self.print_colored(f"\n{self.BOLD}所有磁盘状态:{self.ENDC}", self.BLUE)
        
        available_disks = []
        for i, disk in enumerate(disks, 1):
            # 确定显示颜色和状态
            if disk['is_system']:
                color = self.YELLOW
                status = "（系统盘）"
                if disk['mountpoints']:
                    status += f"（已挂载: {', '.join(disk['mountpoints'])}）"
            elif disk['mounted']:
                color = self.GREEN
                status = f"（已挂载: {', '.join(disk['mountpoints'])}）"
            else:
                color = self.RED
                status = "（未挂载）"
                available_disks.append(disk)
            
            model_info = disk['model']
            self.print_colored(f"{i}. {disk['device']} ({disk['size']}) - {model_info}{status}", color)
        
        if not available_disks:
            self.print_colored("\n没有找到未挂载的数据盘！", self.RED)
            return None
        
        # 过滤掉太小的磁盘（如软盘fd0）
        filtered_disks = []
        for disk in available_disks:
            # 尝试解析大小
            size_gb = 0
            size_str = disk['size'].upper()
            if 'G' in size_str:
                try:
                    size_gb = float(size_str.replace('G', '').replace('B', '').strip())
                except:
                    pass
            elif 'M' in size_str:
                try:
                    size_mb = float(size_str.replace('M', '').replace('B', '').strip())
                    size_gb = size_mb / 1024
                except:
                    pass
            
            # 只保留大于1GB的磁盘
            if size_gb > 1:
                filtered_disks.append(disk)
            else:
                self.print_colored(f"跳过小磁盘: {disk['device']} ({disk['size']})", self.YELLOW)
        
        if not filtered_disks:
            self.print_colored("警告：没有找到合适大小的数据盘", self.YELLOW)
            return None
        
        # 显示可用数据盘
        self.print_colored(f"\n{self.BOLD}可用数据盘:{self.ENDC}", self.GREEN)
        for i, disk in enumerate(filtered_disks, 1):
            self.print_colored(f"{i}. {disk['device']} ({disk['size']}) - {disk['model']}", self.GREEN)
        
        # 如果只有一个可用磁盘，自动选择
        if len(filtered_disks) == 1:
            self.print_colored(f"\n自动选择磁盘: {filtered_disks[0]['device']}", self.GREEN)
            return filtered_disks[0]
        
        # 如果有多个可用磁盘，让用户选择
        choice = input(f"\n{self.GREEN}请选择要挂载的磁盘编号 (1-{len(filtered_disks)}): {self.ENDC}")
        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(filtered_disks):
                return filtered_disks[choice_idx]
            else:
                self.print_colored("选择无效，使用第一个磁盘", self.YELLOW)
                return filtered_disks[0]
        except ValueError:
            self.print_colored("输入无效，使用第一个磁盘", self.YELLOW)
            return filtered_disks[0]
    
    def get_partition_info(self, disk_device):
        """获取磁盘的分区信息"""
        # 获取磁盘的所有分区
        partitions_output = self.run_command(f"lsblk -o NAME,TYPE,FSTYPE {disk_device} -n")
        if not partitions_output:
            return []
        
        partitions = []
        for line in partitions_output.strip().split('\n'):
            if not line.strip():
                continue
            parts = line.strip().split(None, 2)
            if len(parts) >= 2 and parts[1] == 'part':
                # 清理分区名中的特殊字符
                raw_name = parts[0]
                clean_name = raw_name.replace('├─', '').replace('└─', '').replace('│', '').strip()
                fstype = parts[2] if len(parts) > 2 else ""
                partitions.append({
                    'raw_name': raw_name,
                    'clean_name': clean_name,
                    'device': f"/dev/{clean_name}",
                    'fstype': fstype
                })
        
        return partitions
    
    def check_and_prepare_disk(self, disk_device):
        """检查和准备磁盘"""
        self.print_colored(f"\n检查磁盘 {disk_device}...", self.BLUE)
        
        # 获取磁盘的分区信息
        partitions = self.get_partition_info(disk_device)
        
        # 检查分区是否有文件系统
        target_device = None
        filesystem = None
        
        for partition in partitions:
            # 检查这个分区是否有文件系统
            blkid_output = self.run_command(f"blkid {partition['device']}")
            
            if blkid_output and 'TYPE=' in blkid_output:
                match = re.search(r'TYPE="([^"]+)"', blkid_output)
                if match:
                    target_device = partition['device']
                    filesystem = match.group(1)
                    self.print_colored(f"找到分区 {target_device} 有文件系统: {filesystem}", self.GREEN)
                    break
        
        # 如果没有找到有文件系统的分区
        if not target_device:
            self.print_colored("磁盘没有可用的文件系统分区", self.YELLOW)
            
            # 检查是否有分区但没文件系统
            if partitions:
                self.print_colored(f"找到 {len(partitions)} 个分区，但没有文件系统", self.YELLOW)
                # 使用第一个分区
                target_device = partitions[0]['device']
                self.print_colored(f"将使用分区: {target_device}", self.YELLOW)
            
            # 检查是否需要格式化
            if not self.format_disk:
                confirm = input(f"{self.YELLOW}磁盘没有文件系统，需要格式化。是否继续？(y/N): {self.ENDC}")
                if confirm.lower() != 'y':
                    self.print_colored("取消操作", self.YELLOW)
                    return None, None
                self.format_disk = True
            
            # 准备格式化
            return self._format_disk(disk_device, bool(partitions), target_device if partitions else None)
        
        return filesystem, target_device
    
    def _format_disk(self, disk_device, has_partitions, target_partition=None):
        """格式化磁盘"""
        self.print_colored(f"正在准备格式化 {disk_device}...", self.BLUE)
        
        # 如果没有分区，先创建分区
        if not has_partitions:
            self.print_colored("创建新分区...", self.YELLOW)
            
            # 清除现有分区表
            self.print_colored("清除现有分区表...", self.YELLOW)
            self.run_command(f"wipefs -a {disk_device}", check=False)
            self.run_command(f"dd if=/dev/zero of={disk_device} bs=1M count=10", check=False)
            
            # 创建新的GPT分区表和一个分区
            try:
                # 使用 parted 创建分区
                cmds = [
                    f"parted -s {disk_device} mklabel gpt",
                    f"parted -s {disk_device} mkpart primary {self.filesystem} 0% 100%",
                    f"parted -s {disk_device} set 1 lvm off",
                    f"partprobe {disk_device}"
                ]
                
                for cmd in cmds:
                    result = self.run_command(cmd, check=False)
                    if result is None:
                        self.print_colored(f"警告: {cmd} 执行可能有问题", self.YELLOW)
                
                # 等待分区出现
                time.sleep(3)
                
                # 查找新分区
                partitions = self.get_partition_info(disk_device)
                if partitions:
                    target_partition = partitions[0]['device']
                    self.print_colored(f"创建新分区: {target_partition}", self.GREEN)
                else:
                    self.print_colored("无法找到新分区，尝试直接格式化整个磁盘", self.RED)
                    target_partition = disk_device
                    
            except Exception as e:
                self.print_colored(f"创建分区时出错: {e}", self.RED)
                # 尝试直接格式化整个磁盘
                target_partition = disk_device
        
        # 如果还没有目标设备，使用磁盘本身
        if not target_partition:
            target_partition = disk_device
        
        # 格式化目标设备
        self.print_colored(f"格式化 {target_partition} 为 {self.filesystem}...", self.BLUE)
        
        # 先尝试使用 -F 强制格式化
        format_cmd = f"mkfs.{self.filesystem} -F {target_partition}"
        self.print_colored(f"执行: {format_cmd}", self.YELLOW)
        
        result = self.run_command(format_cmd, check=False)
        if result is None:
            # 如果强制格式化失败，尝试不带 -F
            format_cmd = f"mkfs.{self.filesystem} {target_partition}"
            self.print_colored(f"尝试: {format_cmd}", self.YELLOW)
            result = self.run_command(format_cmd, check=False)
        
        if result is None:
            self.print_colored(f"格式化失败", self.RED)
            return None, None
        
        self.print_colored(f"格式化成功", self.GREEN)
        
        # 验证格式化结果
        time.sleep(2)
        fs_check = self.run_command(f"blkid {target_partition}")
        if fs_check and 'TYPE=' in fs_check:
            match = re.search(r'TYPE="([^"]+)"', fs_check)
            if match:
                actual_fs = match.group(1)
                self.print_colored(f"验证: 文件系统类型为 {actual_fs}", self.GREEN)
                return actual_fs, target_partition
        
        return self.filesystem, target_partition
    
    def prepare_mount_point(self, mount_path):
        """准备挂载点"""
        if not os.path.exists(mount_path):
            self.print_colored(f"创建挂载目录: {mount_path}", self.BLUE)
            try:
                os.makedirs(mount_path, exist_ok=True)
                self.run_command(f"chmod 755 {mount_path}")
                return True
            except Exception as e:
                self.print_colored(f"创建目录失败: {e}", self.RED)
                return False
        else:
            # 检查目录是否为空
            try:
                contents = os.listdir(mount_path)
                if contents:
                    self.print_colored(f"警告: {mount_path} 目录不为空！", self.YELLOW)
                    self.print_colored(f"包含 {len(contents)} 个文件/目录", self.YELLOW)
                    confirm = input(f"继续挂载可能会覆盖现有文件。继续吗？(y/N): ")
                    if confirm.lower() != 'y':
                        return False
            except Exception as e:
                self.print_colored(f"检查目录失败: {e}", self.RED)
                return False
        
        return True
    
    def mount_disk(self, disk_device, mount_path):
        """挂载磁盘"""
        self.print_colored(f"挂载 {disk_device} 到 {mount_path}...", self.BLUE)
        
        # 检查是否已经挂载
        mounted = self.run_command(f"mount | grep '{disk_device}\\s'")
        if mounted:
            for line in mounted.split('\n'):
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 3:
                        current_mount = parts[2]
                        if current_mount == mount_path:
                            self.print_colored(f"磁盘已经挂载到 {mount_path}", self.GREEN)
                            return True
                        else:
                            self.print_colored(f"磁盘已挂载到其他位置: {current_mount}", self.YELLOW)
                            confirm = input(f"卸载并重新挂载到 {mount_path}？(y/N): ")
                            if confirm.lower() != 'y':
                                return False
                            # 卸载
                            self.run_command(f"umount {disk_device}", check=False)
                            time.sleep(1)
                            break
        
        # 尝试挂载
        for i in range(3):
            self.print_colored(f"尝试挂载 (第 {i+1}/3 次)...", self.YELLOW)
            
            # 执行挂载命令
            result = self.run_command(f"mount -v {disk_device} {mount_path}", check=False)
            
            # 检查是否挂载成功
            verify = self.run_command(f"mount | grep '{disk_device}.*{mount_path}'")
            if verify:
                self.print_colored("挂载成功", self.GREEN)
                
                # 设置权限
                self.run_command(f"chmod 755 {mount_path}", check=False)
                
                # 显示挂载信息
                df_output = self.run_command(f"df -h {mount_path} | tail -1")
                if df_output:
                    self.print_colored(f"挂载信息: {df_output}", self.BLUE)
                
                return True
            
            if i < 2:
                time.sleep(2)
        
        # 如果仍然失败，提供详细错误信息
        self.print_colored("挂载失败", self.RED)
        
        # 提供更多诊断信息
        self.print_colored("\n详细诊断:", self.YELLOW)
        
        # 检查设备状态
        self.print_colored(f"1. 检查设备 {disk_device}:", self.YELLOW)
        lsblk_output = self.run_command(f"lsblk {disk_device} -o NAME,SIZE,FSTYPE,MOUNTPOINT")
        if lsblk_output:
            print(lsblk_output)
        
        # 检查文件系统
        self.print_colored(f"\n2. 检查文件系统:", self.YELLOW)
        blkid_output = self.run_command(f"blkid {disk_device}")
        if blkid_output:
            print(blkid_output)
        else:
            self.print_colored("没有文件系统信息 - 可能需要重新格式化", self.RED)
            
            # 尝试重新格式化
            confirm = input(f"\n{self.YELLOW}是否尝试重新格式化？(y/N): {self.ENDC}")
            if confirm.lower() == 'y':
                self.print_colored(f"重新格式化 {disk_device}...", self.BLUE)
                format_cmd = f"mkfs.ext4 -F {disk_device}"
                self.run_command(format_cmd, check=False)
                time.sleep(2)
                
                # 再次尝试挂载
                self.print_colored("再次尝试挂载...", self.BLUE)
                result = self.run_command(f"mount {disk_device} {mount_path}", check=False)
                if result is not None:
                    self.print_colored("挂载成功！", self.GREEN)
                    return True
        
        # 检查挂载点
        self.print_colored(f"\n3. 检查挂载点 {mount_path}:", self.YELLOW)
        if os.path.exists(mount_path):
            ls_output = self.run_command(f"ls -la {mount_path}")
            if ls_output:
                print(f"目录内容:\n{ls_output}")
        
        # 建议手动解决方案
        self.print_colored(f"\n4. 建议手动解决方案:", self.YELLOW)
        self.print_colored(f"   运行: sudo mkfs.ext4 -F {disk_device}", self.GREEN)
        self.print_colored(f"   然后: sudo mount {disk_device} {mount_path}", self.GREEN)
        
        return False
    
    def backup_fstab(self):
        """备份 fstab 文件"""
        fstab_path = "/etc/fstab"
        backup_path = f"/etc/fstab.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if os.path.exists(fstab_path):
            try:
                shutil.copy2(fstab_path, backup_path)
                self.print_colored(f"已备份 fstab 到 {backup_path}", self.GREEN)
                return backup_path
            except Exception as e:
                self.print_colored(f"备份失败: {e}", self.RED)
        
        return None
    
    def add_to_fstab(self, disk_device, mount_path, filesystem):
        """添加到 fstab 实现开机自动挂载"""
        fstab_path = "/etc/fstab"
        
        # 获取磁盘的 UUID
        uuid_output = self.run_command(f"blkid -s UUID -o value {disk_device}")
        uuid = uuid_output.strip() if uuid_output else None
        
        if not uuid:
            self.print_colored(f"错误: 无法获取 {disk_device} 的 UUID！", self.RED)
            self.print_colored("请手动检查文件系统：", self.YELLOW)
            self.print_colored(f"  sudo blkid {disk_device}", self.GREEN)
            return False
        
        # 使用 UUID 而不是设备路径
        device_str = f"UUID={uuid}"
        
        # fstab 条目
        fstab_entry = f"\n# Data disk mounted by auto_mount_data_disk.py\n{device_str}\t{mount_path}\t{filesystem}\tdefaults,nofail\t0\t2\n"
        
        # 备份原文件
        backup_file = self.backup_fstab()
        
        try:
            # 读取现有内容
            with open(fstab_path, 'r') as f:
                content = f.read()
            
            # 检查是否已存在相同挂载点的条目
            lines = content.split('\n')
            new_lines = []
            
            for line in lines:
                # 跳过相同的挂载点或相同的 UUID
                if (mount_path in line and (line.startswith('/dev/') or line.startswith('UUID='))):
                    self.print_colored(f"移除旧的挂载条目: {line}", self.YELLOW)
                    continue
                new_lines.append(line)
            
            # 添加新条目
            new_lines.append(fstab_entry.strip())
            
            # 写入新文件
            with open(fstab_path, 'w') as f:
                f.write('\n'.join(new_lines))
            
            self.print_colored(f"已更新 /etc/fstab", self.GREEN)
            self.print_colored(f"新条目: {fstab_entry.strip()}", self.BLUE)
            
            # 显示 UUID 信息供用户参考
            self.print_colored(f"\n磁盘信息:", self.BLUE)
            blkid_output = self.run_command(f"blkid {disk_device}")
            if blkid_output:
                print(blkid_output)
            
            return True
        except Exception as e:
            self.print_colored(f"更新 fstab 失败: {e}", self.RED)
            return False
    
    def main(self):
        """主函数"""
        self.print_colored(f"{'='*60}", self.BLUE)
        self.print_colored(f"{self.BOLD}自动挂载数据盘脚本{self.ENDC}", self.BLUE)
        self.print_colored(f"{'='*60}", self.BLUE)
        
        # 检查权限
        if os.geteuid() != 0:
            self.print_colored("错误：需要 root 权限运行此脚本！", self.RED)
            self.print_colored("请使用 sudo 运行: sudo python3 amdd.py", self.RED)
            return False
        
        # 获取磁盘信息
        disks = self.get_disk_info()
        if not disks:
            self.print_colored("没有找到磁盘", self.RED)
            return False
        
        # 选择数据盘
        self.data_disk = self.select_data_disk(disks)
        if not self.data_disk:
            return False
        
        self.print_colored(f"\n选择磁盘: {self.data_disk['device']}", self.GREEN)
        
        # 如果没有指定挂载路径，使用默认路径 /data
        if not self.mount_path:
            default_path = "/data"
            if os.path.exists(default_path):
                # 如果 /data 已存在，尝试创建带磁盘名的目录
                disk_name = self.data_disk['name']
                default_path = f"/data_{disk_name}"
            
            user_path = input(f"\n{self.GREEN}请输入挂载路径 (默认: {default_path}): {self.ENDC}")
            self.mount_path = user_path.strip() if user_path.strip() else default_path
        
        # 准备挂载点
        if not self.prepare_mount_point(self.mount_path):
            return False
        
        # 检查和准备磁盘（包括格式化）
        filesystem, final_device = self.check_and_prepare_disk(self.data_disk['device'])
        if not filesystem:
            return False
        
        # 挂载
        if not self.mount_disk(final_device, self.mount_path):
            return False
        
        # 添加到 fstab
        self.add_to_fstab(final_device, self.mount_path, filesystem)
        
        # 验证挂载
        self.print_colored(f"\n{'='*60}", self.GREEN)
        self.print_colored(f"{self.BOLD}挂载完成！{self.ENDC}", self.GREEN)
        self.print_colored(f"磁盘: {final_device}", self.GREEN)
        self.print_colored(f"挂载点: {self.mount_path}", self.GREEN)
        self.print_colored(f"文件系统: {filesystem}", self.GREEN)
        
        # 显示最终磁盘使用情况
        df_output = self.run_command(f"df -h {self.mount_path}")
        if df_output:
            self.print_colored(f"\n磁盘使用情况:", self.BLUE)
            print(df_output)
        
        self.print_colored(f"{'='*60}", self.GREEN)
        
        return True

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
    parser.add_argument('-p', '--path', default='/data')
    parser.add_argument('-f', '--format', action='store_true')
    parser.add_argument('-t', '--type', default='ext4', choices=['ext4', 'xfs', 'btrfs'])
    
    args = parser.parse_args(args)
    
    mounter = DiskMounter(
        mount_path = args.path,
        format_disk = args.format,
        filesystem = args.type
    )
    
    if args.version:
        print(VER)
        sys.exit(0)
    elif args.copr:
        print(COPR)
        sys.exit(0)
    elif args.info:
        print(INFO)
        sys.exit(0)
    elif args.help:
        print(HELP)
        sys.exit(0)

    if mounter.main():
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()