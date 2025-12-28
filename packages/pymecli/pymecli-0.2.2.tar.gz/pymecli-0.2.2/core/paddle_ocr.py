from typing import List

from onnx_ocr import ONNXPaddleOcr, result_to_json_data, save_to_img, save_to_json

from data.dou_list import card_rec_list
from models.ocr_model import Region
from utils.card import align_y, distinguish_joker, sort_cards
from utils.image import preprocess_image
from utils.text import match_text, normalize_text

model = ONNXPaddleOcr(
    use_angle_cls=False,
    use_gpu=False,
    cpu_threads=8,  # CPU推理线程数
)


def rec(img, region=None, is_preprocess=False, save_result=False):
    # 检查图像是否有效
    if img is None:
        raise ValueError("Image is None")

    if len(img.shape) < 2:
        raise ValueError("Image has invalid shape")

    if img.size == 0:
        raise ValueError("Image is empty")

    orig_img = img
    if region:
        x, y, w, h = region
        # 检查区域参数是否有效
        if w <= 0 or h <= 0:
            raise ValueError("Invalid region dimensions")
        if x < 0 or y < 0:
            raise ValueError("Invalid region coordinates")
        if y + h > img.shape[0] or x + w > img.shape[1]:
            raise ValueError("Region exceeds image boundaries")
        img = img[y : y + h, x : x + w]
    else:
        x, y = 0, 0

    # 对图像进行预处理，增强对比度以便更好地识别黑色字体
    if is_preprocess:
        img = preprocess_image(img)

    # 检查裁剪后的图像是否有效
    if img is None or img.size == 0:
        raise ValueError("Cropped image is empty")

    if len(img.shape) < 2:
        raise ValueError("Cropped image has invalid shape")

    result = model.ocr(img)
    json_data = result_to_json_data(result)
    if save_result:
        save_to_img(img, result, "./output")
        save_to_json(json_data, "./output")

    return json_data, x, y, orig_img


def find_texts(
    img,
    region=None,
    is_preprocess=False,
    is_align_y=False,
    target_list=card_rec_list,
):
    result, x, y, img = rec(img=img, region=region, is_preprocess=is_preprocess)
    matched_results = []

    if not result:
        return matched_results

    for item in result:
        text, score, box = item["text"], item["confidence"], item["bounding_box"]
        global_box = [
            int(box[0][0] + x),  # x1
            int(box[0][1] + y),  # y1
            int(box[2][0] + x),  # x2
            int(box[2][1] + y),  # y2
        ]

        normalized_text = normalize_text(text)

        if not target_list:
            matched_results.append(
                {
                    "text": normalized_text,
                    "target_text": "",
                    "score": float(score),
                    "box": global_box,
                }
            )
        else:
            matched_list: list[str] = []
            matched, remaining_text = match_text(normalized_text, target_list)

            while matched:
                matched_list.append(matched)
                matched, remaining_text = match_text(remaining_text, target_list)

            for item in matched_list:
                if item == "JO" or item == "JOKER" or item == "JOK":
                    item = distinguish_joker(img, global_box)
                elif item == "10":
                    item = "T"
                elif item == "0":
                    item = "Q"

                matched_results.append(
                    {
                        "text": text,
                        "target_text": item,
                        "score": float(score),
                        "box": global_box,
                    }
                )

    if is_align_y:
        matched_results = align_y(matched_results)

    return matched_results


def find_text_one(img, target=None, region=None, is_preprocess=False):
    result, x, y, img = rec(
        img=img,
        region=region,
        is_preprocess=is_preprocess,
    )

    for item in result:
        text, score, box = item["text"], item["confidence"], item["bounding_box"]
        global_box = [
            int(box[0][0] + x),  # x1
            int(box[0][1] + y),  # y1
            int(box[2][0] + x),  # x2
            int(box[2][1] + y),  # y2
        ]

        normalized_text = normalize_text(text)

        if target:
            if normalized_text.startswith(target):
                return {
                    "text": text,
                    "target_text": target,
                    "score": float(score),
                    "box": global_box,
                }
        else:
            return {
                "text": text,
                "target_text": target,
                "score": float(score),
                "box": global_box,
            }

    return None


def find_text_regions(img, regions: List[Region], is_preprocess=False):
    if is_preprocess:
        img = preprocess_image(img)

    final_result = []
    for item in regions:
        if item.type == "list":
            result = find_text_n(
                img,
                item.target_list,
                item.region,
                item.is_preprocess,
            )
            final_result.append(result)
        elif item.type == "text":
            result = find_text_one(
                img,
                item.target,
                item.region,
                item.is_preprocess,
            )
            final_result.append(result)
        elif item.type == "cards":
            result = find_texts(
                img,
                item.region,
                item.is_preprocess,
                item.is_align_y,
                card_rec_list,
            )

            cards = ""
            if result:
                cards = sort_cards([item["target_text"] for item in result])

            final_result.append(cards)

        else:
            raise ValueError("Invalid region type")

    return final_result


def find_text_n(
    img,
    target_list,
    region=None,
    is_preprocess=False,
):
    result, x, y, img = rec(
        img=img,
        region=region,
        is_preprocess=is_preprocess,
    )

    matched_results = []

    for target in target_list:
        matched = False
        for item in result:
            text, score, box = item["text"], item["confidence"], item["bounding_box"]
            normalized_text = normalize_text(text)
            if normalized_text.startswith(target):
                global_box = [
                    int(box[0][0] + x),  # x1
                    int(box[0][1] + y),  # y1
                    int(box[2][0] + x),  # x2
                    int(box[2][1] + y),  # y2
                ]
                matched_results.append(
                    {
                        "text": text,
                        "target_text": target,
                        "score": float(score),
                        "box": global_box,
                    }
                )
                matched = True
                break
        if not matched:
            matched_results.append(None)

    return matched_results
