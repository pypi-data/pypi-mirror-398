import re


def normalize_newlines(text):
    # 将不同平台的换行符统一为 \n
    text = re.sub(r"\r\n", "\n", text)
    # 将空白行替换为换行符
    text = re.sub(r"\n[ \t]*\n", "\n\n", text)
    # 将两个以上的换行符替换为两个换行符
    return re.sub(r"\n{3,}", "\n\n", text)


# 正则表达式保留指定标签，并记录删除的标签
def remove_unwanted_tags(html, allowed_tags=[]):
    # 匹配所有标签
    pattern = re.compile(r"<(/?)([^ >/]+)([^>]*)>")
    deleted_tags = set()  # 记录被删除的标签类型

    def replace_tag(match):
        tag_name = match.group(2)
        if tag_name in allowed_tags:
            return match.group(0)  # 保留匹配的标签
        else:
            deleted_tags.add(tag_name)  # 记录被删除的标签
            return ""  # 移除不匹配的标签

    # 替换 HTML 中的标签
    cleaned_html = pattern.sub(replace_tag, html)
    return cleaned_html, deleted_tags
