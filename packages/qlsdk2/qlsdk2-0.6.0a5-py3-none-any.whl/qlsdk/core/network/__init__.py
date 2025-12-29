import psutil
import socket

def get_active_interfaces():
    interfaces = {}
    # 获取所有接口地址信息
    all_addrs = psutil.net_if_addrs()
    # 获取接口状态（是否处于UP状态）
    stats = psutil.net_if_stats()
    
    for name, addrs in all_addrs.items():
        # 检查接口是否启用
        if stats[name].isup:
            ips = []
            for addr in addrs:
                # 提取IPv4和IPv6地址
                if addr.family == socket.AF_INET:
                    ips.append(f"IPv4: {addr.address}")
                elif addr.family == socket.AF_INET6:
                    ips.append(f"IPv6: {addr.address}")
            # 过滤无IP的接口（可选）
            if ips:
                interfaces[name] = {
                    "status": "UP",
                    "IPs": ips
                }
    return interfaces

# 调用并打印结果
active_ifs = get_active_interfaces()
for iface, info in active_ifs.items():
    print(f"接口: {iface}")
    print(f"状态: {info['status']}")
    print(f"IP地址: {info['IPs']}\n")