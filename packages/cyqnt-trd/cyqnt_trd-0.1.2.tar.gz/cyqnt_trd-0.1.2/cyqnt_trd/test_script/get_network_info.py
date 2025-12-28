#!/usr/bin/env python3
"""
获取本机IP地址和网关IP地址
"""

import socket
import subprocess
import platform
import re


def get_local_ip():
    """
    获取本机IP地址（IPv4）
    
    Returns:
        str: 本机IP地址，如果获取失败返回None
    """
    try:
        # 方法1: 通过连接外部地址获取本机IP
        # 不实际发送数据，只是获取本机地址
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # 连接到外部地址（不需要实际连接成功）
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        except Exception:
            # 如果连接失败，尝试获取主机名对应的IP
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
        finally:
            s.close()
        return ip
    except Exception as e:
        print(f"获取本机IP失败: {e}")
        return None


def get_all_local_ips():
    """
    获取所有本机IP地址（包括所有网络接口）
    
    Returns:
        list: IP地址列表
    """
    ips = []
    try:
        hostname = socket.gethostname()
        # 获取所有IP地址
        addrinfo = socket.getaddrinfo(hostname, None)
        for item in addrinfo:
            ip = item[4][0]
            if ip not in ips and not ip.startswith('127.'):
                ips.append(ip)
    except Exception as e:
        print(f"获取所有IP地址失败: {e}")
    
    return ips


def get_gateway_ip():
    """
    获取网关IP地址
    
    Returns:
        str: 网关IP地址，如果获取失败返回None
    """
    system = platform.system()
    
    try:
        if system == 'Darwin':  # macOS
            # 使用 netstat 命令获取默认网关
            result = subprocess.run(
                ['netstat', '-rn'],
                capture_output=True,
                text=True,
                check=True
            )
            
            # 查找默认路由（Destination为default或0.0.0.0）
            lines = result.stdout.split('\n')
            for line in lines:
                if 'default' in line or line.startswith('0.0.0.0'):
                    parts = line.split()
                    if len(parts) >= 2:
                        # Gateway通常在第二列
                        gateway = parts[1]
                        # 验证是否为有效的IP地址
                        if re.match(r'^\d+\.\d+\.\d+\.\d+$', gateway):
                            return gateway
            
            # 如果netstat方法失败，尝试使用route命令
            result = subprocess.run(
                ['route', '-n', 'get', 'default'],
                capture_output=True,
                text=True,
                check=True
            )
            
            for line in result.stdout.split('\n'):
                if 'gateway:' in line.lower():
                    gateway = line.split(':')[-1].strip()
                    if re.match(r'^\d+\.\d+\.\d+\.\d+$', gateway):
                        return gateway
        
        elif system == 'Linux':
            # Linux系统
            result = subprocess.run(
                ['ip', 'route', 'show', 'default'],
                capture_output=True,
                text=True,
                check=True
            )
            
            # 查找via后面的IP地址
            match = re.search(r'via\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
            if match:
                return match.group(1)
            
            # 如果ip命令失败，尝试route命令
            result = subprocess.run(
                ['route', '-n'],
                capture_output=True,
                text=True,
                check=True
            )
            
            for line in result.stdout.split('\n'):
                if line.startswith('0.0.0.0'):
                    parts = line.split()
                    if len(parts) >= 2:
                        gateway = parts[1]
                        if re.match(r'^\d+\.\d+\.\d+\.\d+$', gateway):
                            return gateway
        
        elif system == 'Windows':
            # Windows系统
            result = subprocess.run(
                ['ipconfig'],
                capture_output=True,
                text=True,
                check=True
            )
            
            # 查找默认网关
            for line in result.stdout.split('\n'):
                if '默认网关' in line or 'Default Gateway' in line:
                    match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                    if match:
                        return match.group(1)
        
    except subprocess.CalledProcessError as e:
        print(f"执行系统命令失败: {e}")
    except Exception as e:
        print(f"获取网关IP失败: {e}")
    
    return None


def main():
    """主函数"""
    print("=" * 50)
    print("网络信息查询")
    print("=" * 50)
    
    # 获取本机IP
    print("\n【本机IP地址】")
    local_ip = get_local_ip()
    if local_ip:
        print(f"主要IP地址: {local_ip}")
    else:
        print("无法获取主要IP地址")
    
    # 获取所有IP地址
    all_ips = get_all_local_ips()
    if all_ips:
        print(f"所有IP地址: {', '.join(all_ips)}")
    
    # 获取网关IP
    print("\n【网关IP地址】")
    gateway_ip = get_gateway_ip()
    if gateway_ip:
        print(f"默认网关: {gateway_ip}")
    else:
        print("无法获取网关IP地址")
    
    print("\n" + "=" * 50)


if __name__ == '__main__':
    main()

