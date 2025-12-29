from time import sleep
from loguru import logger
import os
from threading import Thread

from qlsdk import AR4M

#------------------------------------------------------------------
# 日志文件配置
#------------------------------------------------------------------
LOG_DIR = os.path.expanduser("./logs")
LOG_FILE = os.path.join(LOG_DIR, "app_{time}.log")
if not os.path.exists(LOG_DIR):
    os.mkdir(LOG_DIR)

logger.add(LOG_FILE, rotation = "50MB")     

def consumer(q):
    t = Thread(target=deal_data, args=(q,))
    t.daemon = True
    t.start()
        
def deal_data(q):
    while True:
        data = q.get()
        if data is None:
            break
        logger.info(data)

# 主函数
if __name__ == "__main__":
    try:
        ar4m = AR4M()
        ar4m.search()
        sleep(6)
        for dev in list( ar4m.devices.values()):
            ret = dev.start_acquisition()
            topic, queue = dev.subscribe()
            logger.info(f"启动{dev.box_mac}的数据采集{'成功' if ret else '失败'}")
            
        sleep(60)
        
        for dev in list( ar4m.devices.values()):
            ret = dev.stop_acquisition()
            dev.get_acq_start_time() 
            logger.info(f"关闭{dev.box_mac}的数据采集{'成功' if ret else '失败'}")
        sleep(1)
    except Exception as e:
        logger.error(f"程序运行异常: {str(e)}")
    finally:        
        logger.info("程序结束。")