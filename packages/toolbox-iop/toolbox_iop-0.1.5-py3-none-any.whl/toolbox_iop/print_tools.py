import json

try:
    from rich.console import Console

    ccprint = Console().print
except ImportError:
    ccprint = print


def dict_printer(process_count_dict: dict, total=None, print_method=print):
    if total is None:
        total = sum(process_count_dict.values())
    for key, value in process_count_dict.items():
        print()
        if isinstance(value, int):
            print_method(f"{key} {value} {value / total:.2%}")
        elif isinstance(value, dict):
            reject_total = sum(value.values())
            if reject_total == 0:
                reject_total = 1
            for k, v in value.items():
                # print(key, k, v, f"{v/reject_total:.2%}")

                print_method(f"{key} {k} {v} {v / reject_total:.2%}")
        else:
            raise NotImplementedError(f"value type {type(value)} not implemented")


def replace_escape_chars(string):
    return string.replace("\\n", "\n").replace("\\t", "\t").replace("\\r", "\r")


def parse_str(words, key="", print_switch=True, prefix="\n\n\n\n\n"):
    try:
        # 解析JSON字符串
        #
        data = json.loads(words)
        data = data[key] if key != "" else data
        # 在控制台输出解析后的结果
        # print(json.dumps(data, indent=4,ensure_ascii=False))
        formatted_json = json.dumps(data, indent=4, ensure_ascii=False, sort_keys=True)

        formatted_json = replace_escape_chars(formatted_json)
        if print_switch:
            print(f"{prefix}解析后的JSON对象:")
            ccprint(formatted_json)
        # print(formatted_json)
    except json.JSONDecodeError as e:
        import traceback

        print("\n输入的字符串不是有效的JSON格式:\n", traceback.format_exc())
