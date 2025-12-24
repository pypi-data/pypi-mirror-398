import sys

def add(*args):
    """批量添加参数（自动根据空格拆分）"""
    for arg in args:
        if isinstance(arg, str) and " " in arg:
            # 自动拆分空格分隔的参数（如 "--name 张三" → ["--name", "张三"]）
            sys.argv.extend(arg.split(" "))
        else:
            sys.argv.append(str(arg))

def set(target_arg: str, new_value):
    """
    设置 / 更新指定参数的值
    - 若参数存在且有值：覆盖旧值
    - 若参数存在但无值（flag）：插入新值
    - 若参数不存在：追加到末尾
    """
    argv = sys.argv
    new_value = str(new_value)

    i = 0
    while i < len(argv):
        if argv[i] == target_arg:
            # 参数存在
            if i + 1 < len(argv) and not argv[i + 1].startswith("-"):
                argv[i + 1] = new_value
            else:
                argv.insert(i + 1, new_value)
            return
        i += 1

    # 参数不存在，追加
    argv.extend([target_arg, new_value])


def set_batch(param_dict: dict[str, ...]) -> None:
    """批量设置参数"""
    for arg, value in param_dict.items():
        set(arg, value)


def get(key: str, default=None):
    """
    使用“裸参数名”获取参数值
    - key: 不带 - / --，如 "name"、"age"
    """
    argv = sys.argv

    long_opt = f"--{key}"
    short_opt = f"-{key}"

    for i, arg in enumerate(argv):
        if arg == long_opt or arg == short_opt:
            # 有 value
            if i + 1 < len(argv) and not argv[i + 1].startswith("-"):
                return argv[i + 1]
            # flag
            return True

    return default


def clear():
    """清空参数（自动保留脚本名）"""
    sys.argv = sys.argv[:1]

def reset(args_list):
    """完全替换参数（自动保留脚本名）"""
    sys.argv = [sys.argv[0]] + list(args_list)

def remove(target_arg: str):
    """
    删除指定参数及其对应的值（支持多次出现）
    """
    argv = sys.argv
    i = 0

    while i < len(argv):
        if argv[i] == target_arg:
            # 删除参数本身
            del argv[i]

            # 如果后一个元素存在，且它不是一个新的参数名，则认为是 value
            if i < len(argv) and not argv[i].startswith("-"):
                del argv[i]
            # 不递增 i，继续检查当前位置（防止连续参数）
        else:
            i += 1

if __name__ == '__main__':
    import argparse

    add("--name 张三", "-a 20")  # 自动拆分空格分隔的参数
    set("--name", "李四")
    set("-a", 67)

    # 解析参数（此时 argparse 会读取修改后的 sys.argv）
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", type=str)
    parser.add_argument("-a", "--age", type=int)
    args = parser.parse_args()

    print(f"姓名：{args.name}，年龄：{args.age}")  # 姓名：张三，年龄：20