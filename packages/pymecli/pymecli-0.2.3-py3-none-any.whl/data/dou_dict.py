from pathlib import Path
from typing import Dict

text_map: Dict[str, str] = dict(
    D="JOKER",  # 大王
    X="JOKER",
    dizhu="地主",
    jiaodizhu_btn="叫地主",
    qiangdizhu_btn="抢地主",
    jiabei_btn="加倍",
    chaojijiabei_btn="超级加倍",
    bujiabei_btn="不加倍",
    liantian_btn="聊天",
    start_btn="开始游戏",
    chat_btn="聊天",
    chupai_btn="出牌",
    buchu_btn="不出",
    yaobuqi_btn="要不起",
    mingpai_btn="明牌",
    mingpaistart_btn="明牌开始",
    jixuyouxi_btn="继续游戏",
)

region_map: Dict[str, tuple] = dict(
    general_btn=(210, 450, 1000, 120),  # 叫地主、抢地主、加倍按钮截图区域
    # pass_btn=(200, 450, 1000, 120),  # 要不起截图区域
    # # 出牌区
    my_hand_cards=(210, 560, 1000, 180),  # 我的手牌截图区域
    left_played_cards=(320, 320, 400, 120),  # 左边出牌截图区域
    right_played_cards=(720, 320, 400, 120),  # 右边出牌截图区域
    my_played_cards=(320, 422, 800, 120),  # 我的出牌截图区域
    # # 过牌区
    three_cards=(600, 33, 220, 103),  # 地主底牌截图区域
    # left_pass=(360, 360, 120, 80),  # 左边不出截图区域
    # right_pass=(940, 360, 120, 80),  # 右边不出截图区域
    # my_pass=(636, 469, 152, 87),  # 我的不出截图区域
    # 豆子区域
    # bean=(308, 204, 254, 60),
    # bean1=(295, 474, 264, 60),
    # bean2=(882, 203, 230, 60),
    chat_btn=(1302, 744, 117, 56),
    # landlord_cards=(602, 88, 218, 104),
    end_btn=(800, 610, 510, 80),
    landlord_flag_left=(114, 236, 70, 70),
    landlord_flag_right=(1226, 236, 70, 70),
    cards_num_left=(273, 388, 33, 42),
    cards_num_right=(1117, 387, 33, 44),
    # my_pass=(636, 469, 152, 87),
    right_animation=(720, 210, 360, 100),  # 下家动画位置
    left_animation=(360, 210, 360, 100),  # 上家动画位置
    my_animation=(540, 340, 350, 120),  # 自己上方动画位置
    # (1440, 810)
    weile_test=(130, 600, 2000, 380),
    weile_test_three=(990, 16, 300, 80),
)

draw_rect_map = dict(
    # c1=(270, 600, 1900, 380),
    weile_test=region_map["weile_test"],
    weile_test_three=region_map["weile_test_three"],
    # left_played_cards=rect_map["left_played_cards"],
    # right_played_cards=rect_map["right_played_cards"],
    # my_played_cards=rect_map["my_played_cards"],
    # three_cards=rect_map["three_cards"],
    # cards_num_left=rect_map["cards_num_left"],
    # cards_num_right=rect_map["cards_num_right"],
    # general_btn=rect_map["general_btn"],
    # rect_map["right_animation"],  # 下家动画位置
    # rect_map["left_animation"],  # 上家动画位置
    # rect_map["my_animation"],  # 自己上方动画位置
    # right_animation=rect_map["right_animation"],
    # left_animation=rect_map["left_animation"],
    # my_animation=rect_map["my_animation"],
    # all=(5, 5, 1430, 800),
    # my_pass=rect_map["my_pass"],
)

threshold_map: Dict[str, float | tuple[float, float]] = dict(
    jiaodizhu=-0.68,  # 叫地主阈值
    fanqiangdizhu=0.3,  # 反抢地主阈值
    qiangdizhu=0.12,  # 抢地主阈值
    landlord_jiabei=(0.4, 0.01),
    # landlord_jiabei=(0.37, -0.4),
    qiang_landlord_jiabei=(0.45, 0.12),
    farmer_jaibei=(2, 1.22),
    farmer_jaibei_low=(1.22, 0.45),
    mingpai=1.14,
    # jiabei1=0.37,
    # jiabei2=-0.4,
    # jiabei3=0.45,
    # jiabei4=0.12,
    # jiabei5=2,
    # jiabei6=1.22,
    # jiabei7=1.22,
    # jiabei8=0.45,
)
to_card_map = {
    30: "D",
    20: "X",
    17: "2",
    14: "A",
    13: "K",
    12: "Q",
    11: "J",
    10: "T",
    9: "9",
    8: "8",
    7: "7",
    6: "6",
    5: "5",
    4: "4",
    3: "3",
}
to_env_card_map = {
    "D": 30,
    "X": 20,
    "2": 17,
    "A": 14,
    "K": 13,
    "Q": 12,
    "J": 11,
    "T": 10,
    "9": 9,
    "8": 8,
    "7": 7,
    "6": 6,
    "5": 5,
    "4": 4,
    "3": 3,
}

module_dir = Path(__file__).resolve().parent.parent

model_path_map = {
    "landlord": str(module_dir / "baselines/resnet/resnet_landlord.ckpt"),
    "landlord_up": str(module_dir / "baselines/resnet/resnet_landlord_up.ckpt"),
    "landlord_down": str(module_dir / "baselines/resnet/resnet_landlord_down.ckpt"),
}

weights_path_map = {
    "bid_weights": str(module_dir / "douzero/weights/bid_weights.pkl"),
    "farmer_weights": str(module_dir / "douzero/weights/farmer_weights.pkl"),
    "landlord_down_weights": str(
        module_dir / "douzero/weights/landlord_down_weights.pkl"
    ),
    "landlord_up_weights": str(module_dir / "douzero/weights/landlord_up_weights.pkl"),
    "landlord_weights": str(module_dir / "douzero/weights/landlord_weights.pkl"),
}

position_name_map = {
    "landlord": "地主",
    "landlord_up": "地主上家",
    "landlord_down": "地主下家",
}

TYPE_PRIORITY = {
    0: 0,  # PASS
    1: 1,  # SINGLE
    2: 1,  # PAIR
    3: 1,  # TRIPLE
    4: 2,  # BOMB
    5: 3,  # KING_BOMB
    6: 1,  # 3+1
    7: 1,  # 3+2
    8: 1,  # SERIAL_SINGLE
    9: 1,  # SERIAL_PAIR
    10: 1,  # SERIAL_TRIPLE
    11: 1,  # SERIAL_3+1
    12: 1,  # SERIAL_3+2
    13: 1,  # 4+2
    14: 1,  # 4+2+2
}
