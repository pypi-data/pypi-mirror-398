from threading import Thread
import psutil
import time

def get_active_ipv4():
    ips = []
    # 获取所有接口地址信息
    all_addrs = psutil.net_if_addrs()
    # 获取接口状态（是否处于UP状态）
    stats = psutil.net_if_stats()
    
    for name, addrs in all_addrs.items():
        # 检查接口是否启用
        if stats[name].isup:
            for addr in addrs:
                # 提取IPv4地址
                if addr.family == socket.AF_INET:
                    ips.append(addr.address)
    return ips
def monitor_up_interfaces(interval=2, callback=None):
    prev_status = {iface: psutil.net_if_stats()[iface].isup 
                  for iface in psutil.net_if_stats()}
    
    while True:
        current_stats = psutil.net_if_stats()
        for iface, stats in current_stats.items():
            current_up = stats.isup
            # 检测状态变化
            if current_up != prev_status.get(iface, None):
                if current_up:
                    print(f"[UP] 接口 {iface} 激活")
                    if callback: callback(iface, "UP")
                else:
                    print(f"[DOWN] 接口 {iface} 断开")
                    if callback: callback(iface, "DOWN")
                prev_status[iface] = current_up
        time.sleep(interval)

# 自定义回调函数示例
def notify(iface, status):
    if status == "UP":
        print(f"接口 {iface} 已激活")

# 启动监听
# monitor_up_interfaces(callback=notify)

monitor = Thread(target=monitor_up_interfaces, name="Network Status Monitor", args=(2, notify))
monitor.start()

import socket
def is_port_in_use(ip, port):
    with socket.socket() as s:
        return s.connect_ex((ip, port)) == 0
    
print(get_active_ipv4())