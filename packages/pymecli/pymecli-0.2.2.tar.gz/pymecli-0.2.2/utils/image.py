import cv2
import numpy as np


def preprocess_image(img):
    # 获取图像的各个颜色通道
    if img.shape[2] == 3:  # RGB/BGR 图像
        b, g, r = cv2.split(img)
    elif img.shape[2] == 4:  # RGBA/BGRA 图像
        b, g, r, _ = cv2.split(img)
    else:
        return img

    # 对每个颜色通道应用处理
    processed_channels = []
    for channel in [b, g, r]:
        # 应用高斯模糊减少噪声
        blurred = cv2.GaussianBlur(channel, (3, 3), 0)

        # 增强对比度 - 使用CLAHE（限制对比度自适应直方图均衡化）
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(blurred)

        processed_channels.append(enhanced)

    # 合并处理后的通道
    if img.shape[2] == 3:
        final_img = cv2.merge(processed_channels)
    elif img.shape[2] == 4:
        # 如果原图有alpha通道，保留它
        final_img = cv2.merge(
            processed_channels + [np.ones_like(processed_channels[0]) * 255]
        )
    else:
        final_img = img

    return final_img
