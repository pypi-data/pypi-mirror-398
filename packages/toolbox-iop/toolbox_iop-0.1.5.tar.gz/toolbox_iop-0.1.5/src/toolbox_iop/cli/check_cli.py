from toolbox_iop.json_check_tools import find_duplicate_ids


def parse_args():
    import argparse

    parser = argparse.ArgumentParser(description="检查JSONL文件中的重复ID")
    parser.add_argument("jsonl_file", help="要检查的JSONL文件路径")
    parser.add_argument("--key", "-k", help="要检查的JSONL的键名", default="id")
    return parser.parse_args()


def main():
    args = parse_args()
    duplicates = find_duplicate_ids(args.jsonl_file, args.key)

    if duplicates:
        print("❌发现重复的 id：")
        for id_val, lines in duplicates.items():
            print(f"id '{id_val[args.key]}' 在以下行重复出现: {lines}")
    else:
        print("✅未发现重复的 id。")


if __name__ == "__main__":
    main()
