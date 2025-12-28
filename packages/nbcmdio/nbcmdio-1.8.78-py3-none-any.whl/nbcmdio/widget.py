import time
from typing import Union, Iterable
import sys
class ProgressBar:
    """ ## 进度条 
    未单开线程，如需及时刷新：update(0)"""
    CHARS = " ▏▎▍▌▋▊▉█" # 其实是半宽字符
    INVLEN = 1/len(CHARS)
    CENSUS = 2 # 统计speed的时间s
    FORMAT={
        'all': "{percentage}|{bar}| {progress} [{time}, {speed}]",
        'percentage': "{percentage:5.1f}%",
        'progress': "{processed:d}/{total:d}",
        'time': "{elapsed:.3f}<{remaining:.3f}",
        'speed': "{speed:.3f}{unit}/s"
    }
    def __init__(self, 
        iterator:Union[Iterable, None]=None, 
        total=0, 
        format="", 
        fmt_dict = None, 
        row=-1, col=-1, 
        ncols=10, 
        start=1, 
        interval=0.2, 
        unit='') -> None:
        """
        Args:
        - 0: iterator
        - format (str): 进度条格式 
          - progress
          - current/total, speed 
          - percent
          - elapsed, ramaining
          - 0[key]
        - row, col 位置
        - total 
        - color
        - ncols

        """
        self.format = format
        print(format)
        if total <= 0 and not isinstance(iterator, Iterable):
            total = -1
        self.num_total = total if total>0 else len(iterator)
        self.num_processed = 0
        self.ncols = ncols
        self.progress_bar = " " * self.ncols
        self.fmt_dict = fmt_dict if isinstance(fmt_dict, dict) else {}
        self.unit = unit
        self.speed = 0.0
        self.percentage = 0.0
        self.time_elapsed = 0.0
        self.time_remaining = 0.0
        self.time_total = 0.0
        self.time_start = 0.0
        self.time_last_draw = 0.0
        self.census_time = [0.0]
        self.census_num = [] # 最近两秒的数据池
        self.paused_start = 0.0
        self.paused_end = 0.0
        self.paused_time = 0.0
        self.__max_len = 0
        if start:
            self.start()


    def update(self, num):
        t = time.perf_counter()
        self.num_processed += num
        self.percentage = self.num_processed / self.num_total
        if self.census_num and t - self.census_time[0] > self.CENSUS:
            self.census_time.pop(0)
            self.census_num.pop(0)
        self.census_time.append(t)
        self.census_num.append(num)
        self.speed = sum(self.census_num)/(self.census_time[-1] - self.census_time[0])
        self.time_elapsed = t - self.time_start
        self.time_remaining = (self.num_total - self.num_processed) / self.speed # 使用CENSUS内的瞬时速度
        self.time_total = self.time_elapsed + self.time_remaining
        # self.draw()
    
    def draw(self):
        self.time_last_draw = time.perf_counter()
        n = self.percentage * self.ncols
        intN = int(n)
        remN = n - intN
        # print(n,remN,int(remN//self.INVLEN),self.CHARS[int(remN//self.INVLEN)])
        self.progress_bar = self.CHARS[-1] * intN + self.CHARS[int(remN//self.INVLEN)]
        self.progress_bar += ' '*(self.ncols - intN - 1)
        string = self.format.format(
            percentage=self.percentage*100, 
            bar=self.progress_bar, 
            processed = self.num_processed,
            total=self.num_total,
            elapsed = self.time_elapsed,
            remaining=self.time_remaining,
            speed = self.speed,
            unit=self.unit,
            **self.fmt_dict
        )
        l = len(string)
        if l >= self.__max_len:
            self.__max_len = l
        else:
            string += ' '*(self.__max_len-l)
        # sys.stdout.write('\r'+string)

    def start(self):
        if not self.time_start:
            self.time_start = time.perf_counter()
            self.census_time = [self.time_start]
            self.census_num = []
            self.draw()

    def pause(self):
        self.paused_start = time.perf_counter()

    def goon(self):
        self.paused_end = time.perf_counter()
        self.census_time = [self.paused_end]
        self.census_num = []
        self.paused_time += self.paused_end - self.paused_start
