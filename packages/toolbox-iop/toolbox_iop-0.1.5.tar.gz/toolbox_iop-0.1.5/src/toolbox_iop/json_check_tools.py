from collections import defaultdict

from .json_tools import load_json


def find_duplicate_ids(jsonl_file, key="id"):
    # 用于记录每个 id 出现的行号
    id_to_lines = defaultdict(list)

    load_json(jsonl_file, lambda x: id_to_lines[x[key]].append(x) if key in x else None)

    # 筛选出重复的 id
    duplicates = {
        id_val: lines for id_val, lines in id_to_lines.items() if len(lines) > 1
    }

    return duplicates
