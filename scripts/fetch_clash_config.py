import requests
import schedule
import time
import os
from datetime import datetime

# --- 请在这里配置你的信息 ---

# 1. 要下载的文件的 URL
FILE_URL = "https://feed.iggv5.com/c/cfdde660-45ef-4e79-a6e8-578b16ba6aa8/platform/clash/iGG-iGuge" # 示例 URL，请替换成你自己的

# 2. 文件保存的目录（文件夹）
#    - Windows 示例: "C:/Users/YourUser/Downloads/AutoDownloads"
#    - macOS/Linux 示例: "/Users/YourUser/Downloads/AutoDownloads"
#    - 如果目录不存在，脚本会自动创建
SAVE_DIRECTORY = "/home/wanzhengwang/.config/clash" 

# 3. 保存的文件名
#    - 你可以指定一个固定的文件名，比如 "latest_data.csv"
#    - 或者，如果你想每次保存都用不同的名字（例如加上时间戳），可以设置为 None
SAVE_FILENAME = "config.yaml" # 示例文件名，请替换
# SAVE_FILENAME = None # 如果设置为 None，文件名将是 URL 中的原始文件名或加上时间戳

# --- 配置结束 ---


def download_file():
    """下载文件并保存到指定位置的核心函数"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始执行下载任务...")

    try:
        # 确保保存目录存在
        if not os.path.exists(SAVE_DIRECTORY):
            os.makedirs(SAVE_DIRECTORY)
            print(f"创建目录: {SAVE_DIRECTORY}")

        # 发起网络请求，stream=True 表示流式下载，适合大文件
        with requests.get(FILE_URL, stream=True) as r:
            # 检查请求是否成功 (状态码 200)
            r.raise_for_status() 

            # 确定最终的文件名
            final_filename = SAVE_FILENAME
            if final_filename is None:
                # 如果没有指定文件名，尝试从 URL 中获取
                final_filename = FILE_URL.split('/')[-1]
                # 如果 URL 结尾没有文件名，则使用时间戳命名
                if not final_filename:
                    final_filename = f"download_{int(time.time())}.tmp"

            # 拼接完整的文件保存路径
            save_path = os.path.join(SAVE_DIRECTORY, final_filename)

            # 以二进制写入模式 ('wb') 打开文件，并写入下载内容
            with open(save_path, 'wb') as f:
                # 每次写入 8KB 的数据块
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"文件下载成功! 已保存至: {save_path}")

    except requests.exceptions.RequestException as e:
        print(f"下载失败: 网络错误 - {e}")
    except Exception as e:
        print(f"发生未知错误: {e}")

# --- 任务调度 ---

# 设定任务：每隔 1 小时执行一次 download_file 函数
schedule.every(1).hour.do(download_file)

# 你也可以使用其他时间单位
# schedule.every(10).minutes.do(download_file) # 每10分钟
# schedule.every().day.at("10:30").do(download_file) # 每天10:30

print("脚本已启动，将每小时下载一次文件。按 Ctrl+C 停止。")

# 首次立即执行一次
download_file()

# 无限循环，让 schedule 持续检查是否有任务需要运行
while True:
    schedule.run_pending()
    time.sleep(1) # 每秒检查一次，避免 CPU 占用过高