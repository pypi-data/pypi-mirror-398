import base64

import cv2
import numpy as np
from fastapi import APIRouter, Body

from core.paddle_ocr import find_text_n, find_text_one, find_text_regions, find_texts
from models.ocr_model import (
    FindCardsRequest,
    FindNRequest,
    FindOneRequest,
    FindRegionsRequest,
)
from models.response import SuccessResponse
from utils.card import sort_cards

router = APIRouter()


@router.post("/cards")
async def find_cards(
    request: FindCardsRequest = Body(...),
):
    image_data = base64.b64decode(request.img)
    np_array = np.frombuffer(image_data, np.uint8)
    img = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

    result = find_texts(
        img,
        region=request.region,
        is_preprocess=request.is_preprocess,
        is_align_y=request.is_align_y,
    )

    cards = ""
    if result is not None:
        tmp_list = [item["target_text"] for item in result]
        cards = sort_cards(tmp_list)

    return SuccessResponse(data=cards)


@router.post("/one")
async def find_one(
    request: FindOneRequest = Body(...),
):
    image_data = base64.b64decode(request.img)
    np_array = np.frombuffer(image_data, np.uint8)
    img = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
    result = find_text_one(
        img,
        target=request.target,
        region=request.region,
        is_preprocess=request.is_preprocess,
    )

    return SuccessResponse(data=result)


@router.post("/regions")
async def find_regions(
    request: FindRegionsRequest = Body(...),
):
    image_data = base64.b64decode(request.img)
    np_array = np.frombuffer(image_data, np.uint8)
    img = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
    result = find_text_regions(
        img,
        regions=request.regions,
        is_preprocess=request.is_preprocess,
    )

    return SuccessResponse(data=result)


@router.post("/n")
async def find_n(
    request: FindNRequest = Body(...),
):
    image_data = base64.b64decode(request.img)
    np_array = np.frombuffer(image_data, np.uint8)
    img = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
    result = find_text_n(
        img,
        target_list=request.target_list,
        region=request.region,
        is_preprocess=request.is_preprocess,
    )

    return SuccessResponse(data=result)
