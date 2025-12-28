import cv2
import numpy as np
from PIL import Image, ImageOps


def image_loader(image):
    """
    根据输入类型（numpy数组、Pillow图像或字符串路径）加载图像。
    返回灰度图像和原始彩色图像（如果有的话）。支持中文路径。
    """
    if isinstance(image, str):  # 如果是字符串，则认为是文件路径
        try:
            # 使用Pillow尝试打开图片以支持中文路径
            with Image.open(image) as img:
                img = ImageOps.exif_transpose(img)  # 处理EXIF方向信息
                img = np.array(img)
                gray_img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
                return gray_img, img
        except Exception as e:
            raise ValueError(f"无法读取图像文件 {image}，请检查路径是否正确。错误信息：{e}")
    elif isinstance(image, Image.Image):  # 如果是Pillow图像
        img = ImageOps.exif_transpose(image)  # 处理EXIF方向信息
        img = np.array(img)
        gray_img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        return gray_img, img
    elif isinstance(image, np.ndarray):  # 如果是numpy数组
        if len(image.shape) == 3:  # 彩色图
            gray_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            return gray_img, image
        else:  # 灰度图
            return image, cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    else:
        raise ValueError("不支持的图像格式，请提供文件路径、Pillow图像或numpy数组。")


def find_subimage_position(large_image, small_image, method=cv2.TM_CCOEFF_NORMED):
    """
    使用模板匹配在大图中查找小图的位置。

    参数:
        large_image (str, PIL.Image, np.ndarray): 大图的文件路径、Pillow图像或numpy数组
        small_image (str, PIL.Image, np.ndarray): 小图（子图）的文件路径、Pillow图像或numpy数组
        method (int): 匹配方法，推荐使用 cv2.TM_CCOEFF_NORMED

    返回:
        tuple: (top_left, bottom_right, confidence)
               top_left: 匹配区域左上角坐标 (x, y)
               bottom_right: 匹配区域右下角坐标 (x, y)
               confidence: 匹配置信度 (0~1)，值越接近1表示匹配度越高
               如果未找到有效匹配，返回 (None, None, 0)
    """
    # 加载图像
    large_gray, large_img = image_loader(large_image)
    small_gray, _ = image_loader(small_image)

    # 获取小图的宽度和高度
    small_h, small_w = small_gray.shape
    large_h, large_w = large_gray.shape

    # 检查小图是否比大图大
    if small_h > large_h or small_w > large_w:
        print("小图比大图大，无法匹配。")
        return None, None, 0

    # 执行模板匹配
    result = cv2.matchTemplate(large_gray, small_gray, method)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    # 计算匹配区域的边界
    top_left = max_loc
    bottom_right = (top_left[0] + small_w, top_left[1] + small_h)

    x1, y1 = top_left
    x2, y2 = bottom_right
    h, w, c = large_img.shape
    return ((x1 + x2) / 2 / w, (y1 + y2) / 2 / h, (x2 - x1) / w, (y2 - y1) / h), max_val
