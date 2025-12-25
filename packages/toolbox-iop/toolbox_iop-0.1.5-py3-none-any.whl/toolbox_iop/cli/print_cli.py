import argparse
import random
import traceback

from tqdm import tqdm

from toolbox_iop.print_tools import parse_str

# def convert_str_to_number(s):
#     if "." in s:
#         return float(s)
#     else:
#         return int(s)


def read_file(
    file_path,
    random_order=False,
    key="",
    auto_scroll=False,
    print_switch=True,
    number="1.0",
):
    number = eval(number)
    # print(number)
    # print(type(number))
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()

            # 去除两端的空白符号（包括换行符）
            lines = [line for line in lines if line.strip()]

            # 如果指定了随机顺序，则打乱顺序
            if random_order:
                random.shuffle(lines)

            if number < 1:
                lines = lines[: int(len(lines) * number)]
            elif number == 1 and isinstance(number, float):
                lines = lines[:]
            else:
                lines = lines[:number]

            for line in tqdm(lines):
                parse_str(line, key, print_switch, "")
                if not auto_scroll:
                    user_input = input("按Enter后继续, Exit退出：\n").strip()
                    if user_input.lower() == "exit":
                        print("程序已退出。")
                        break
                if print_switch:
                    print("\n" * 5)
    except KeyboardInterrupt:
        print("程序已退出。")
    except FileNotFoundError:
        print(f"文件 {file_path} 未找到。")
    except Exception as e:
        print(f"读取文件时发生错误: {e}")
        traceback.print_exc()
    print("完成！")


def main():
    # 设置命令行参数解析
    parser = argparse.ArgumentParser(description="读取文件并逐行处理")
    parser.add_argument("file_path", type=str, help="文件路径")
    parser.add_argument(
        "-r", "--random", action="store_true", help="是否随机顺序读取文件内容"
    )
    parser.add_argument(
        "-k", "--key", type=str, help="读取关键词，默认显示全部", default=""
    )
    parser.add_argument("-a", "--all", action="store_true", help="循环显示全部")
    parser.add_argument(
        "-n", "--number", type=str, help="读取数量，默认读取全部", default="1.0"
    )
    parser.add_argument("--print_off", action="store_false", help="不显示输出")

    args = parser.parse_args()

    print(args)

    # 调用函数处理文件
    read_file(
        args.file_path, args.random, args.key, args.all, args.print_off, args.number
    )


if __name__ == "__main__":
    main()
