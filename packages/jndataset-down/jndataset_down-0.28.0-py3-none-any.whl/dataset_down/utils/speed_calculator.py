import collections
import time

class DownloadSpeedCalculator:
    def __init__(self, window_size=30):  # 60秒的滑动窗口
        self.window_size = window_size
        self.samples = collections.deque()  # 存储 (timestamp, bytes) 的双端队列
        
    def add_sample(self, current_bytes):
        """添加当前下载字节数的采样"""
        current_time = time.time()
        self.samples.append((current_time, current_bytes))
        
        # 移除窗口外的旧样本
        while self.samples and (current_time - self.samples[0][0]) > self.window_size:
            self.samples.popleft()
            
    def get_speed(self):
        """计算并返回平均下载速度 (bytes/second)"""
        if len(self.samples) < 2:
            return 0
            
        # 计算窗口期内的平均速度
        first_sample = self.samples[0]
        last_sample = self.samples[-1]
        
        time_diff = last_sample[0] - first_sample[0]
        bytes_diff = last_sample[1] - first_sample[1]
        
        if time_diff <= 0 or bytes_diff <= 0:
            return 0
            
        return bytes_diff / time_diff

# 在 Downloader 类中添加一个实例变量
# self.speed_calculator = DownloadSpeedCalculator()

# 然后在 download_folder 方法中替换原有的速度计算逻辑：