import pandas as pd
from typing import Literal

from .. import B_os


class B_Record1d:
    '''
    recorder = Record_1d(csv_file, mode="w")
    recorder.write(name="Alice", age=25, city="Shanghai")
    recorder.write(name="Bob", age=30, city="Beijing")
    recorder.write(name="Charlie", age=22, city="Shenzhen")
    '''
    def __init__(self, csv_path, mode:Literal["w", "a"]="w"):
        self.csv_path = csv_path

        B_os.makedirs(csv_path)
        self.data = pd.DataFrame()
        if mode == "w":
            B_os.rm(csv_path)
            self.__read()
        elif mode == "a":
            self.__read()

    def write(self, **kwargs):
        '''
        :param kwargs:
        :return:

        '''
        # 给DataFrame增加一行
        # key作为column, value作为内容
        new_row = pd.DataFrame([kwargs])
        self.data = pd.concat([self.data, new_row], ignore_index=True)
        self.__save()

        return self
    def __read(self):
        try:
            self.data = pd.read_csv(self.csv_path)
        except FileNotFoundError:
            self.data = pd.DataFrame()
        except pd.errors.EmptyDataError:
            self.data = pd.DataFrame()

    def __save(self, csv_path=None):
        if csv_path is None:
            csv_path = self.csv_path
        self.data.to_csv(csv_path, index=False, encoding='utf-8-sig')

    def __str__(self):
        return str(self.data)

if __name__ == '__main__':
    # 指定保存的CSV路径
    csv_file = "test_data.csv"

    # 创建记录器（写模式 w 表示覆盖）
    recorder = B_Record1d(csv_file, mode="w")

    # 写入几条数据
    recorder.write(name="Alice", age=25, city="Shanghai")
    recorder.write(name="Bob", age=30, city="Beijing")
    recorder.write(name="Charlie", age=22, city="Shenzhen")

    # 追加模式 a
    recorder2 = B_Record1d(csv_file, mode="a")
    recorder2.write(name="David", age=28, city="Guangzhou")

    # 打印当前内容
    print("CSV 当前内容：")
    print(recorder2)