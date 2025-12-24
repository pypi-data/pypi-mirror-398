import pandas as pd
from typing import Literal

from .. import B_os
# from byzh.core import B_os

class B_Record2d:
    def __init__(self, csv_path, mode:Literal["w", "a", "r"]="r", title:str=None):
        self.csv_path = csv_path
        self.mode = mode
        self.title = title

        B_os.makedirs(csv_path)
        self.data = pd.DataFrame()
        if mode == "w":
            B_os.rm(csv_path)
            self.__read()
        elif mode == "a":
            self.__read()
        elif mode == "r":
            self.__read()

        if self.data.index.name is None:
            self.data.index.name = title
    # 支持 recorder[row, col] 访问
    def __getitem__(self, key):
        if isinstance(key, tuple) and len(key) == 2: # 读值操作
            row, col = key
            row, col = str(row), str(col)
            return self.data.loc[row, col]
        if isinstance(key, str): # 读行操作
            row = str(key)
            return self.data.loc[row, :]

    # 支持 recorder[row, col] = value
    def __setitem__(self, key, value):
        assert self.mode!="r", "不允许读模式下赋值"

        if isinstance(key, tuple) and len(key) == 2: # 赋值操作
            row, col = key
            row, col, value = str(row), str(col), str(value)
            self.data.loc[row, col] = value
            self.__save()
        if isinstance(key, str): # 赋值行操作
            assert type(value) == pd.Series, "仅支持 Series 赋值"
            key = str(key)
            self.data.loc[key, :] = value.copy()
            self.__save()

    # 复制一行
    def copy_row(self, new_row, origin_row):
        new_row, origin_row = str(new_row), str(origin_row)

        if origin_row not in self.data.index:
            raise KeyError(f"源行 {origin_row} 不存在")

        # 深拷贝一份行数据
        self.data.loc[new_row] = self.data.loc[origin_row].copy()

        self.__save()
        return self

    # 转置
    def T(self):
        self.data = self.data.T.copy()
        self.__save()
        return self

    def write(self, row, col, value):
        self[row, col] = value
        return self

    def get(self, row, col):
        return self[row, col]

    def get_str(self, row, col) -> str:
        return str(self[row, col])

    def get_int(self, row, col) -> int:
        return int(self[row, col])

    def get_float(self, row, col) -> float:
        return float(self[row, col])

    def get_bool(self, row, col) -> bool:
        result = self.get_str(row, col)
        if result.lower() in ("true", "1"):
            return True
        elif result.lower() in ("false", "0"):
            return False
        else:
            raise ValueError(f"无法转换为布尔值 -> {result}")

    def __read(self):
        try:
            self.data = pd.read_csv(self.csv_path, index_col=0)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            self.data = pd.DataFrame()

    def __save(self, csv_path=None):
        if csv_path is None:
            csv_path = self.csv_path
        self.data.to_csv(csv_path, index=True, encoding='utf-8-sig')

    def __str__(self):
        return str(self.data)


if __name__ == '__main__':
    csv_file = "test_data.csv"

    recorder = B_Record2d(csv_file, mode="w", title='x\y')

    # 用索引方式赋值
    recorder["awa", "OvO"] = 10
    recorder["awa", "TwT"] = 20
    recorder["qwq", "OvO"] = 30
    recorder["qwq", "TwT"] = 40

    recorder['aaa'] = recorder['qwq']

    print("当前内容：")
    print(recorder)

    # 用索引方式读取
    print("awa, OvO =", recorder["awa", "OvO"])

    recorder = B_Record2d(csv_file, mode="r")
    print(recorder)