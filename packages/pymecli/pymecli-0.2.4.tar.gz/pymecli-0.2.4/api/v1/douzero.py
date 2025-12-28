from pathlib import Path
from typing import cast

from fastapi import APIRouter, Body, Query

from data.dou_dict import model_path_map, threshold_map
from douzero import BidModel, FarmerModel, LandlordModel
from douzero.env.game import GameEnv
from douzero.evaluation.deep_agent import DeepAgent
from models.douzero_model import BidScoreRequest, PlayRequest, PreGameScoreRequest
from models.response import SuccessResponse
from utils.card import cards_env_to_other_env, cards_to_env, env_to_cards

module_dir = Path(__file__).resolve().parent.parent.parent
router = APIRouter()


@router.get("/bid")
async def bid_score(
    request: BidScoreRequest = Query(...),
):
    landlord_score = round(BidModel.predict_score(request.cards), 4)
    farmer_score = round(FarmerModel.predict(request.cards, "farmer"), 4)

    if landlord_score > threshold_map["jiaodizhu"]:
        message = "叫地主,不抢"
    elif landlord_score > threshold_map["qiangdizhu"]:
        message = "叫地主或抢地主一次"
    elif landlord_score > threshold_map["fanqiangdizhu"]:
        message = "叫|抢地主"
    else:
        message = "不叫"

    return SuccessResponse(
        data={
            "landlord_score": landlord_score,
            "farmer_score": farmer_score,
            "message": message,
        }
    )


@router.get("/pre")
async def pre_game_score(
    request: PreGameScoreRequest = Query(...),
):
    cards = request.cards
    three = request.three
    position_code = int(request.position_code)

    position = ["up", "landlord", "down"][position_code]

    if len(cards) == 20:
        score = round(
            LandlordModel.predict_by_model(cards, three),
            4,
        )

        if score > threshold_map["mingpai"]:
            message = "明牌"
        elif score > cast(tuple[float, float], threshold_map["landlord_jiabei"])[0]:
            message = "超级加倍"
        elif score > cast(tuple[float, float], threshold_map["landlord_jiabei"])[1]:
            message = "加倍"
        else:
            message = "不加倍"
    else:
        score = round(FarmerModel.predict(cards, position), 4)

        if score > cast(tuple[float, float], threshold_map["farmer_jaibei"])[0]:
            message = "超级加倍"
        elif score > cast(tuple[float, float], threshold_map["farmer_jaibei"])[1]:
            message = "加倍"
        else:
            message = "不加倍"

    return SuccessResponse(
        data={
            "score": score,
            "three": three,
            "position": position,
            "message": message,
        }
    )


@router.post("/play")
async def play(
    request: PlayRequest = Body(...),
):
    cards = request.cards
    other_cards = request.other_cards
    played_list = request.played_list
    three = request.three
    position_code = int(request.position_code)
    position = ["landlord_up", "landlord", "landlord_down"][position_code]

    cards_env = cards_to_env(cards)
    three_env = cards_to_env(three)

    if not other_cards:
        other_env = cards_env_to_other_env(cards_env)
        other_cards = env_to_cards(other_env)
    else:
        other_env = cards_to_env(other_cards)

    play_data_list = {
        "three_landlord_cards": three_env,
        ["landlord_up", "landlord", "landlord_down"][
            (position_code + 0) % 3
        ]: cards_env,
        ["landlord_up", "landlord", "landlord_down"][
            (position_code + 1) % 3
        ]: other_env[0:17] if (position_code + 1) % 3 != 1 else other_env[17:],
        ["landlord_up", "landlord", "landlord_down"][
            (position_code + 2) % 3
        ]: other_env[0:17] if (position_code + 1) % 3 == 1 else other_env[17:],
    }

    AI = [
        position,
        DeepAgent(
            position,
            str(module_dir / model_path_map[position]),
        ),
    ]
    game_env = GameEnv(AI)
    game_env.card_play_init(play_data_list)
    for i, played_cards in enumerate(played_list):
        player_pos = ["landlord", "landlord_down", "landlord_up"][i % 3]
        game_env.step(player_pos, cards_to_env(played_cards))

    action_message, action_list = game_env.step(position, update=False)
    game_env.step(position, cards_to_env(action_message["action"]))
    remaining_cards = env_to_cards(game_env.info_sets[position].player_hand_cards)
    game_over = game_env.game_over

    return SuccessResponse(
        data={
            "action_list": action_list,
            "action_message": action_message,
            "starting_cards": cards,
            "starting_other_cards": other_cards,
            "remaining_cards": remaining_cards,
            "game_over": game_over,
        }
    )
