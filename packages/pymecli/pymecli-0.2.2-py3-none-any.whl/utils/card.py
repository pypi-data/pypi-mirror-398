from collections import Counter

import numpy as np

from data.dou_dict import TYPE_PRIORITY, to_card_map, to_env_card_map
from data.dou_list import all_env_card
from douzero.env.move_detector import get_move_type


def distinguish_joker(img, box):
    x1, y1, x2, y2 = box

    img_array = img[y1:y2, x1:x2]

    # 计算区域内的平均颜色值
    avg_color = np.mean(img_array, axis=(0, 1))

    # 初始化默认值
    blue_channel = 0
    green_channel = 0
    red_channel = 0

    # 获取各通道值 (注意: OpenCV使用BGR格式)
    if len(avg_color) >= 3:
        blue_channel = avg_color[0]  # Blue通道 (OpenCV使用BGR)
        green_channel = avg_color[1]  # Green通道
        red_channel = avg_color[2]  # Red通道

    # blue_channel:151.59661354581672,green_channel:153.34578353253653,red_channel:190.43027888446215

    # 计算亮度 (基于人眼对不同颜色敏感度的不同)
    # brightness = 0.299 * red_channel + 0.587 * green_channel + 0.114 * blue_channel
    # 计算红色占比
    total_color = red_channel + green_channel + blue_channel
    if total_color > 0:
        red_ratio = red_channel / total_color
    else:
        red_ratio = 0

    # 如果红色通道值明显大于蓝色通道值,则认为是大王
    if red_channel - blue_channel > 20 and red_ratio > 0.3:
        return "D"
    else:
        return "X"


def align_y(matched_results, offset=20):
    if not matched_results:
        return []
    # 取第一个元素的Y坐标作为标准
    standard_y = matched_results[0]["box"][1]

    # 筛选Y坐标在标准值范围内的元素
    filtered_results = []
    for result in matched_results:
        box = result["box"]
        y_coord = box[1]  # box[1]是y1坐标

        # 判断Y坐标是否在允许范围内
        if standard_y - offset <= y_coord <= standard_y + offset:
            filtered_results.append(result)

    return filtered_results


def sort_cards(cards) -> str:
    sorted_cards = sorted(
        cards,
        key=lambda x: to_env_card_map.get(x, len(to_env_card_map)),
        reverse=True,
    )

    return "".join(sorted_cards)


def cards_to_env(cards) -> list[int]:
    if cards == "pass":
        return []
    env_cards = [to_env_card_map[c] for c in cards]
    env_cards.sort()
    return env_cards


def env_to_cards(env_list: list[int]) -> str:
    return sort_cards([to_card_map[c] for c in env_list])


all_env_count = Counter(all_env_card)


def cards_env_to_other_env(cards_env: list[int]):
    cards_env_count = Counter(cards_env)
    other_env: list[int] = []

    for card, count in all_env_count.items():
        remaining = count - cards_env_count.get(card, 0)
        other_env.extend([card] * remaining)

    return other_env


def is_valid_cards(cards):
    """
    检查牌型是否符合斗地主规则
    :param cards: 牌的字符串表示,如 "AAA3"
    :return: True表示合法,False表示不合法
    """
    if cards == "pass":
        return True

    cards_env = cards_to_env(cards)
    move_type = get_move_type(cards_env)

    # 如果牌型类型不是错误类型,则认为是合法的
    return move_type["type"] != 15  # TYPE_15_WRONG


def compare_cards(cards1, cards2):
    """
    比较两组牌的大小
    :param cards1: 第一组牌的字符串表示,如 "AAA3"
    :param cards2: 第二组牌的字符串表示,如 "KKK2"
    :return: 1表示第一组牌大,-1表示第二组牌大,0表示无法比较或相等
    """

    if not is_valid_cards(cards1) or not is_valid_cards(cards2):
        return 0  # 不合法的牌型无法比较
    cards1_env = cards_to_env(cards1)
    cards2_env = cards_to_env(cards2)

    type1 = get_move_type(cards1_env)
    type2 = get_move_type(cards2_env)

    if type1["type"] == 15 or type2["type"] == 15:
        return 0  # 错误牌型

    # 获取牌型优先级
    priority1 = TYPE_PRIORITY[type1["type"]]
    priority2 = TYPE_PRIORITY[type2["type"]]

    # 牌型优先级不同,只有高优先级的牌型可以压制低优先级的牌型
    if priority1 > priority2:
        # 只有炸弹和王炸可以压制其他牌型
        if priority1 >= 2 or priority2 == 0:  # 炸弹或王炸
            return 1
        else:
            return 0  # 普通牌型不能压制其他牌型
    elif priority1 < priority2:
        # 只有炸弹和王炸可以压制其他牌型
        if priority2 >= 2 or priority1 == 0:  # 炸弹或王炸
            return -1
        else:
            return 0  # 普通牌型不能压制其他牌型
    else:
        # 牌型优先级相同,必须是相同类型才能比较
        if type1["type"] != type2["type"]:
            return 0  # 不同类型无法比较

        # 相同类型牌型比较
        # 对于无法比较rank的牌型（如PASS）,返回0
        if "rank" not in type1 or "rank" not in type2:
            return 0

        # 对于序列牌型,还需要比较长度
        if "len" in type1 and "len" in type2:
            if type1["len"] != type2["len"]:
                return 0  # 长度不同无法比较

        # 比较rank值
        if type1["rank"] > type2["rank"]:
            return 1  # 第一组牌大（rank值高）
        elif type1["rank"] < type2["rank"]:
            return -1  # 第二组牌大（rank值高）
        else:
            return 0  # rank值相等


if __name__ == "__main__":
    # print(cards_to_env("pass"))
    # print(sort_cards("765432AKQJT98"))
    # print(env_to_cards([3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 17]))
    # print(cards_env_to_other_env(cards_to_env("D2AKKQQJT98777643")))

    print(cards_to_env("pass"))
    print(get_move_type(cards_to_env("pass")))
    print(get_move_type(cards_to_env("666777345")))
    print(compare_cards("22", "K"))
    print(compare_cards("pass", "345678"))
    print(compare_cards("4AAA", "KKK3"))
    print(compare_cards("QQQ3", "pass"))
