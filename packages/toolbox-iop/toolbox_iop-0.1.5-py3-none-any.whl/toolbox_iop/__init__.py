from .json_check_tools import find_duplicate_ids
from .json_tools import load_json, save_normal_json, load_json_file, save_json_file
from .logger_tools import get_logger
from .print_tools import dict_printer
from .string_tools import normalize_newlines, remove_unwanted_tags


def main() -> None:
    print("Hello from toolbox-iop!")
