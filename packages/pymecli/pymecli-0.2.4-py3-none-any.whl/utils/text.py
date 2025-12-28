import unicodedata


def normalize_text(text):
    """
    将全角字符转换为半角字符
    """
    normalized = ""
    for char in text:
        # 将全角字符转换为半角字符
        normalized_char = unicodedata.normalize("NFKC", char)
        normalized += normalized_char
    return normalized


def match_text(text: str, target_list: list[str]):
    text = text.strip()
    # text = str.replace(text, "I", "")
    remaining_text = ""

    if not text:
        return None, remaining_text

    for target_text in target_list:
        if text.startswith(target_text):
            len_target_text = len(target_text)
            # if target_text == "JO":
            #     len_target_text = 5
            remaining_text = text[len_target_text:]

            return target_text, remaining_text

    return None, remaining_text
