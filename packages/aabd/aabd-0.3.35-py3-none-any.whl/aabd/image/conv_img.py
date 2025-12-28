import os
import io
import sys
import logging
from typing import Union, List
from enum import Enum
import cv2
import numpy
from PIL import Image
import base64
from aabd.base import path_util

logger = logging.getLogger(__name__)

try:
    import requests
except:
    pass

try:
    import numpy as np


    def np_gray_transform(imgs):
        """
        将 (H, W, 3) 或 (B, H, W, 3) 的 RGB 图像转为灰度图。
        支持 float32/64 ([0, 1]) 和 uint8 ([0, 255]) 输入。
        输出保持与输入相同的 dtype 和数值范围，形状为 (..., 1)。
        """

        if imgs.shape[-1] != 3:
            raise ValueError("Last dimension must be 3 (RGB channels).")

        # 定义权重（与 torchvision / PIL / OpenCV 一致）
        weights = np.array([0.2989, 0.5870, 0.1140], dtype=np.float32)

        # 执行灰度转换（使用 float32 计算以避免溢出）
        gray = np.dot(imgs.astype(np.float32), weights)

        # 恢复原始 dtype
        if imgs.dtype == np.uint8:
            gray = np.clip(gray, 0, 255).astype(np.uint8)
        else:
            # 对于 float 类型，通常范围是 [0, 1]，但可能略超（如归一化后），可选是否 clip
            gray = gray.astype(imgs.dtype)

        return gray[..., np.newaxis]
except:
    pass

try:
    import torch
    import torchvision

    def_torch_device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    gray_transform = torchvision.transforms.Grayscale(num_output_channels=1)
except:
    pass

# input_type/out_type : pil numpy tensor base64 file bytes url
# pil <-> file
# pil <-> bytes
# url -> bytes
# pil <-> numpy
# numpy <-> tensor
# pil <-> tensor
# numpy -> bytes
# base64 <-> bytes

# pil <-> base64: pil <-> bytes <-> base64
# url -> pil: url -> bytes -> pil
# base64 -> numpy: base64 -> bytes -> pil -> numpy
# numpy <-> file: numpy <-> pil <-> file
# bytes -> numpy: bytes -> pil -> numpy
# url -> numpy: url -> bytes -> pil -> numpy
# tensor <-> base64: tensor <-> pil <-> bytes <-> base64
# tensor <-> file: tensor <-> pil <-> file
# tensor -> bytes: tensor -> numpy -> bytes
# bytes -> tensor: bytes -> pil -> tensor
# url -> tensor: url -> bytes -> pil -> tensor
# base64 <-> file: base64 -> bytes -> pil -> file
# url -> base64: url -> bytes -> base64
# url -> file: url -> bytes -> pil -> file

# data_format: CHW HWC BCHW BHWC
# device: cpu gpu
# color_order: RGB RGBA BGR BGRA
# normalized: 0-255 0-1
# image_format: PNG JPG  WEBP
from enum import Enum, EnumMeta


class CaseInsensitiveEnumMeta(EnumMeta):
    def __call__(cls, value, *args, **kwargs):
        if isinstance(value, str):
            # 尝试忽略大小写匹配
            upper_value = value.upper()
            for member in cls:
                if member.value == upper_value:
                    return member
        # 否则走默认逻辑（比如传入的是枚举成员本身）
        return super().__call__(value, *args, **kwargs)


class DimOrder(Enum, metaclass=CaseInsensitiveEnumMeta):
    CHW = 'CHW'
    HWC = 'HWC'
    BCHW = 'BCHW'
    BHWC = 'BHWC'


class ColorOrder(Enum, metaclass=CaseInsensitiveEnumMeta):
    RGB = 'RGB'
    RGBA = 'RGBA'
    BGR = 'BGR'
    BGRA = 'BGRA'
    GRAY = 'GRAY'


class ImageFormat(Enum, metaclass=CaseInsensitiveEnumMeta):
    PNG = 'PNG'
    JPG = 'JPG'
    WEBP = 'WEBP'


def eq_image_format(a: ImageFormat, b: ImageFormat):
    if isinstance(a, ImageFormat):
        a = a.value
    if isinstance(b, ImageFormat):
        b = b.value
    a = a.lower()
    b = b.lower()

    if a == b:
        return True

    if a in ['jpg', 'jpeg'] and b in ['jpg', 'jpeg']:
        return True
    return False


class PilColorModel(Enum, metaclass=CaseInsensitiveEnumMeta):
    RGB = 'RGB'
    L = 'L'
    RGBA = 'RGBA'


ImageNet_mean = [0.485, 0.456, 0.406]
ImageNet_std = [0.229, 0.224, 0.225]


def parse_source_numpy_BHWC(source,
                            source_dim_order: Union[DimOrder, str] = None,
                            source_color_order: Union[ColorOrder, str] = None,
                            source_normalized: bool = None,
                            source_normalized_mean: Union[list[float], tuple[float], np.ndarray] = None,
                            source_normalized_std: Union[list[float], tuple[float], np.ndarray] = None):
    if source_dim_order is not None and isinstance(source_dim_order, str):
        source_dim_order = DimOrder(source_dim_order)
    if source_color_order is not None and isinstance(source_color_order, str):
        source_color_order = ColorOrder(source_color_order)

    if source_dim_order is not None and isinstance(source_dim_order, str):
        source_dim_order = DimOrder(source_dim_order)
    if source_color_order is not None and isinstance(source_color_order, str):
        source_color_order = ColorOrder(source_color_order)

    if source_dim_order is None:
        if source.ndim == 2:
            source = np.expand_dims(source, axis=-1)
        if source.ndim == 3:
            source_dim_order = DimOrder.HWC
        elif source.ndim == 4:
            source_dim_order = DimOrder.BHWC
        else:
            raise ValueError(f"source.ndim: {source.ndim} not support")
    if source_color_order is None:
        if source_dim_order == DimOrder.HWC or source_dim_order == DimOrder.BHWC:
            color_count = source.shape[-1]
        elif source_dim_order == DimOrder.BCHW or source_dim_order == DimOrder.CHW:
            color_count = source.shape[-3]
        else:
            raise ValueError(f"dim_order: {source_dim_order.value} not support")
        if color_count == 1:
            source_color_order = ColorOrder.GRAY
        elif color_count == 3:
            source_color_order = ColorOrder.BGR
        elif color_count == 4:
            source_color_order = ColorOrder.BGRA
        else:
            raise ValueError(f"color_count: {color_count} not support")
    if source_normalized is None:
        if source.dtype == np.float32 or source.dtype == np.float64:
            source_normalized = True
        elif source.dtype == np.uint8:
            source_normalized = False
        else:
            raise ValueError(f"source.dtype: {source.dtype} not support")

    if source_normalized and source_normalized_mean is not None and source_normalized_std is not None:
        source_normalized_mean = np.array(source_normalized_mean, dtype=np.float32)
        source_normalized_std = np.array(source_normalized_std, dtype=np.float32)
    else:
        source_normalized_mean = None
        source_normalized_std = None

    if source_dim_order == DimOrder.BCHW:
        source = np.transpose(source, (0, 2, 3, 1))
    elif source_dim_order == DimOrder.CHW:
        source = np.expand_dims(source, axis=0).transpose(0, 2, 3, 1)
    elif source_dim_order == DimOrder.HWC:
        source = np.expand_dims(source, axis=0)

    return (source, DimOrder.BHWC, source_color_order,
            source_normalized, source_normalized_mean, source_normalized_std)


def parse_source_tensor_BCHW(source: torch.Tensor,
                             source_dim_order: Union[DimOrder, str] = None,
                             source_color_order: Union[ColorOrder, str] = None,
                             source_normalized: bool = None,
                             source_normalized_mean: Union[list[float], tuple[float], np.ndarray, torch.Tensor] = None,
                             source_normalized_std: Union[list[float], tuple[float], np.ndarray, torch.Tensor] = None):
    if source_dim_order is not None and isinstance(source_dim_order, str):
        source_dim_order = DimOrder(source_dim_order)
    if source_color_order is not None and isinstance(source_color_order, str):
        source_color_order = ColorOrder(source_color_order)

    if source_dim_order is not None and isinstance(source_dim_order, str):
        source_dim_order = DimOrder(source_dim_order)
    if source_color_order is not None and isinstance(source_color_order, str):
        source_color_order = ColorOrder(source_color_order)

    if source_dim_order is None:
        if source.ndim == 2:
            source = np.expand_dims(source, axis=-1)
        if source.ndim == 3:
            source_dim_order = DimOrder.CHW
        elif source.ndim == 4:
            source_dim_order = DimOrder.BCHW
        else:
            raise ValueError(f"source.ndim: {source.ndim} not support")
    if source_color_order is None:
        if source_dim_order == DimOrder.HWC or source_dim_order == DimOrder.BHWC:
            color_count = source.shape[-1]
        elif source_dim_order == DimOrder.BCHW or source_dim_order == DimOrder.CHW:
            color_count = source.shape[-3]
        else:
            raise ValueError(f"dim_order: {source_dim_order.value} not support")
        if color_count == 1:
            source_color_order = ColorOrder.GRAY
        elif color_count == 3:
            source_color_order = ColorOrder.RGB
        elif color_count == 4:
            source_color_order = ColorOrder.RGBA
        else:
            raise ValueError(f"color_count: {color_count} not support")
    if source_normalized is None:
        if source.dtype == torch.float32 or source.dtype == torch.float64:
            source_normalized = True
        elif source.dtype == torch.uint8:
            source_normalized = False
        else:
            raise ValueError(f"source.dtype: {source.dtype} not support")

    if source_normalized and source_normalized_mean is not None and source_normalized_std is not None:
        if not isinstance(source_normalized_mean, torch.Tensor):
            source_normalized_mean = np.array(source_normalized_mean, dtype=np.float32)
        if isinstance(source_normalized_mean, np.ndarray):
            source_normalized_mean = torch.from_numpy(source_normalized_mean)
        source_normalized_mean = source_normalized_mean.to(source.device)
        if not isinstance(source_normalized_std, torch.Tensor):
            source_normalized_std = np.array(source_normalized_std, dtype=np.float32)
        if isinstance(source_normalized_std, np.ndarray):
            source_normalized_std = torch.from_numpy(source_normalized_std)
        source_normalized_std = source_normalized_std.to(source.device)
    else:
        source_normalized_mean = None
        source_normalized_std = None

    if source_dim_order == DimOrder.BHWC:
        source = source.permute(0, 3, 1, 2)
    elif source_dim_order == DimOrder.HWC:
        source = source.unsqueeze(0).permute(0, 3, 1, 2)
    elif source_dim_order == DimOrder.CHW:
        source = source.unsqueeze(0)

    return (source, DimOrder.BCHW, source_color_order,
            source_normalized, source_normalized_mean, source_normalized_std)


def parse_target_tensor_normalized(target_normalized: bool = None,
                                   target_normalized_mean: Union[
                                       list[float], tuple[float], np.ndarray, torch.Tensor] = None,
                                   target_normalized_std: Union[
                                       list[float], tuple[float], np.ndarray, torch.Tensor] = None,
                                   target_device: Union[torch.device, str] = None):
    if target_normalized is not False and target_normalized_mean is not None and target_normalized_std is not None:
        target_normalized = True
    elif target_normalized is None:
        target_normalized = True

    if target_normalized and target_normalized_mean is not None and target_normalized_std is not None:
        if isinstance(target_normalized_mean, (list, tuple)):
            target_normalized_mean = np.array(target_normalized_mean, dtype=np.float32)
        if isinstance(target_normalized_mean, np.ndarray):
            target_normalized_mean = torch.from_numpy(target_normalized_mean).to(target_device)

        if isinstance(target_normalized_std, (list, tuple)):
            target_normalized_std = np.array(target_normalized_std, dtype=np.float32)
        if isinstance(target_normalized_std, np.ndarray):
            target_normalized_std = torch.from_numpy(target_normalized_std).to(target_device)
    else:
        target_normalized_mean = None
        target_normalized_std = None

    return target_normalized, target_normalized_mean, target_normalized_std


def parse_target_numpy_normalized(target_normalized: bool = None,
                                  target_normalized_mean: Union[list[float], tuple[float], np.ndarray] = None,
                                  target_normalized_std: Union[list[float], tuple[float], np.ndarray] = None):
    if target_normalized is not False and target_normalized_mean is not None and target_normalized_std is not None:
        target_normalized = True
    elif target_normalized is None:
        target_normalized = False

    if target_normalized and target_normalized_mean is not None and target_normalized_std is not None:
        target_normalized_mean = np.array(target_normalized_mean, dtype=np.float32)
        target_normalized_std = np.array(target_normalized_std, dtype=np.float32)
    else:
        target_normalized_mean = None
        target_normalized_std = None

    return target_normalized, target_normalized_mean, target_normalized_std


def tensor_bchw_transform_source_by_color_order(source: torch.Tensor,
                                                source_normalized: bool, source_normalized_mean, source_normalized_std,
                                                source_color_order: ColorOrder, target_color_order: ColorOrder):
    """
    将tensor bchw 维度顺序的图片根据颜色排序 生成新的图片和对应的归一化参数
    ⚠️不做归一化操作
    """
    if source_normalized_mean is not None and source_normalized_std is not None:
        mean_std = True
    else:
        mean_std = False

    if source_color_order == ColorOrder.BGR:
        if target_color_order == ColorOrder.RGB:
            source = source[:, [2, 1, 0], :, :]
            if mean_std:
                source_normalized_mean = source_normalized_mean[[2, 1, 0]]
                source_normalized_std = source_normalized_std[[2, 1, 0]]
        elif target_color_order == ColorOrder.BGR:
            pass
        elif target_color_order == ColorOrder.RGBA:
            alpha = torch.ones_like(source[:, 0:1, :, :])
            if not source_normalized:
                alpha = alpha * 255
            source = torch.cat([source[:, [2, 1, 0], :, :], alpha], dim=1)
            if mean_std:
                source_normalized_mean = source_normalized_mean[[2, 1, 0]]
                source_normalized_mean = torch.cat([source_normalized_mean, source_normalized_mean.new_tensor([1.0])])
                source_normalized_std = source_normalized_std[[2, 1, 0]]
                source_normalized_std = torch.cat([source_normalized_std, source_normalized_std.new_tensor([1e-9])])
        elif target_color_order == ColorOrder.BGRA:
            alpha = torch.ones_like(source[:, 0:1, :, :])
            if not source_normalized:
                alpha = alpha * 255
            source = torch.cat([source, alpha], dim=1)
            if mean_std:
                source_normalized_mean = torch.cat([source_normalized_mean, source_normalized_mean.new_tensor([1.0])])
                source_normalized_std = torch.cat([source_normalized_std, source_normalized_std.new_tensor([1e-9])])
        elif target_color_order == ColorOrder.GRAY:
            source = source[:, [2, 1, 0], :, :]
            if source.dtype == torch.uint8:
                source = source.float()
            if mean_std:
                source = gray_transform((source * source_normalized_std[[2, 1, 0]].reshape(1, -1, 1, 1) +
                                         source_normalized_mean[[2, 1, 0]].reshape(1, -1, 1, 1)))
                source_normalized_mean = None
                source_normalized_std = None
            else:
                source = gray_transform(source)
    elif source_color_order == ColorOrder.RGB:
        if target_color_order == ColorOrder.RGB:
            pass
        elif target_color_order == ColorOrder.BGR:
            source = source[:, [2, 1, 0], :, :]
            if mean_std:
                source_normalized_mean = source_normalized_mean[[2, 1, 0]]
                source_normalized_std = source_normalized_std[[2, 1, 0]]
        elif target_color_order == ColorOrder.RGBA:
            alpha = torch.ones_like(source[:, 0:1, :, :])
            if not source_normalized:
                alpha = alpha * 255
            source = torch.cat([source, alpha], dim=1)
            if mean_std:
                source_normalized_mean = torch.cat([source_normalized_mean, source_normalized_mean.new_tensor([1.0])])
                source_normalized_std = torch.cat([source_normalized_std, source_normalized_std.new_tensor([1e-9])])
        elif target_color_order == ColorOrder.BGRA:
            alpha = torch.ones_like(source[:, 0:1, :, :])
            if not source_normalized:
                alpha = alpha * 255
            source = torch.cat([source[:, [2, 1, 0], :, :], alpha], dim=1)
            if mean_std:
                source_normalized_mean = source_normalized_mean[[2, 1, 0]]
                source_normalized_mean = torch.cat([source_normalized_mean, source_normalized_mean.new_tensor([1.0])])
                source_normalized_std = source_normalized_std[[2, 1, 0]]
                source_normalized_std = torch.cat([source_normalized_std, source_normalized_std.new_tensor([1e-9])])
        elif target_color_order == ColorOrder.GRAY:
            if source.dtype == torch.uint8:
                source = source.float()
            if mean_std:
                source = gray_transform(source * source_normalized_std.reshape(1, -1, 1, 1) +
                                        source_normalized_mean.reshape(1, -1, 1, 1))
                source_normalized_mean = None
                source_normalized_std = None
            else:
                source = gray_transform(source)
    elif source_color_order == ColorOrder.BGRA:
        if target_color_order == ColorOrder.RGB:
            bgr = source[:, :3, :, :]
            alpha = source[:, 3:4, :, :]
            if source_normalized:
                if mean_std:
                    source_normalized_mean_alpha = source_normalized_mean[3:]
                    source_normalized_std_alpha = source_normalized_std[3:]
                    alpha = (alpha * source_normalized_std_alpha.reshape(1, -1, 1, 1) +
                             source_normalized_mean_alpha.reshape(1, -1, 1, 1))
                background = torch.ones_like(bgr)
                source = bgr * alpha + background * (1 - alpha)
            else:
                alpha = source[:, 3:4, :, :] / 255.0
                background = torch.ones_like(bgr) * 255
                source = bgr * alpha + background * (1 - alpha)
            source = source[:, [2, 1, 0], :, :]
            if mean_std:
                source_normalized_mean = source_normalized_mean[:3][[2, 1, 0]]
                source_normalized_std = source_normalized_std[:3][[2, 1, 0]]
        elif target_color_order == ColorOrder.BGR:
            bgr = source[:, :3, :, :]
            alpha = source[:, 3:4, :, :]
            if source_normalized:
                if mean_std:
                    source_normalized_mean_alpha = source_normalized_mean[3:]
                    source_normalized_std_alpha = source_normalized_std[3:]
                    alpha = (alpha * source_normalized_std_alpha.reshape(1, -1, 1, 1) +
                             source_normalized_mean_alpha.reshape(1, -1, 1, 1))
                background = torch.ones_like(bgr)
                source = bgr * alpha + background * (1 - alpha)
            else:
                alpha = source[:, 3:4, :, :] / 255.0
                background = torch.ones_like(bgr) * 255
                source = bgr * alpha + background * (1 - alpha)
            if mean_std:
                source_normalized_mean = source_normalized_mean[:3]
                source_normalized_std = source_normalized_std[:3]
        elif target_color_order == ColorOrder.RGBA:
            source = source[:, [2, 1, 0, 3], :, :]
            if mean_std:
                source_normalized_mean = source_normalized_mean[[2, 1, 0, 3]]
                source_normalized_std = source_normalized_std[[2, 1, 0, 3]]
        elif target_color_order == ColorOrder.BGRA:
            pass
        elif target_color_order == ColorOrder.GRAY:
            bgr = source[:, :3, :, :]
            alpha = source[:, 3:4, :, :]
            if source_normalized:
                if mean_std:
                    source_normalized_mean_alpha = source_normalized_mean[3:]
                    source_normalized_std_alpha = source_normalized_std[3:]
                    alpha = (alpha * source_normalized_std_alpha.reshape(1, -1, 1, 1) +
                             source_normalized_mean_alpha.reshape(1, -1, 1, 1))
                background = torch.ones_like(bgr)
                source = bgr * alpha + background * (1 - alpha)
            else:
                alpha = source[:, 3:4, :, :] / 255.0
                background = torch.ones_like(bgr) * 255
                source = bgr * alpha + background * (1 - alpha)
            source = source[:, [2, 1, 0], :, :]
            if source.dtype == torch.uint8:
                source = source.float()
            if mean_std:
                source = gray_transform(source * source_normalized_std[:3][[2, 1, 0]].reshape(1, -1, 1, 1) +
                                        source_normalized_mean[:3][[2, 1, 0]].reshape(1, -1, 1, 1))
                source_normalized_mean = None
                source_normalized_std = None
            else:
                source = gray_transform(source)
    elif source_color_order == ColorOrder.RGBA:
        if target_color_order == ColorOrder.RGB:
            rgb = source[:, :3, :, :]
            alpha = source[:, 3:4, :, :]
            if source_normalized:
                if mean_std:
                    source_normalized_mean_alpha = source_normalized_mean[3:]
                    source_normalized_std_alpha = source_normalized_std[3:]
                    alpha = (alpha * source_normalized_std_alpha.reshape(1, -1, 1, 1) +
                             source_normalized_mean_alpha.reshape(1, -1, 1, 1))
                background = torch.ones_like(rgb)
                source = rgb * alpha + background * (1 - alpha)
            else:
                alpha = source[:, 3:4, :, :] / 255.0
                background = torch.ones_like(rgb) * 255
                source = rgb * alpha + background * (1 - alpha)
            if mean_std:
                source_normalized_mean = source_normalized_mean[:3]
                source_normalized_std = source_normalized_std[:3]
        elif target_color_order == ColorOrder.BGR:
            rgb = source[:, :3, :, :]
            alpha = source[:, 3:4, :, :]
            if source_normalized:
                if mean_std:
                    source_normalized_mean_alpha = source_normalized_mean[3:]
                    source_normalized_std_alpha = source_normalized_std[3:]
                    alpha = (alpha * source_normalized_std_alpha.reshape(1, -1, 1, 1) +
                             source_normalized_mean_alpha.reshape(1, -1, 1, 1))
                background = torch.ones_like(rgb)
                source = rgb * alpha + background * (1 - alpha)
            else:
                alpha = source[:, 3:4, :, :] / 255.0
                background = torch.ones_like(rgb) * 255
                source = rgb * alpha + background * (1 - alpha)
            source = source[:, [2, 1, 0], :, :]
            if mean_std:
                source_normalized_mean = source_normalized_mean[:3][[2, 1, 0]]
                source_normalized_std = source_normalized_std[:3][[2, 1, 0]]
        elif target_color_order == ColorOrder.RGBA:
            pass
        elif target_color_order == ColorOrder.BGRA:
            source = source[:, [2, 1, 0, 3], :, :]
            if mean_std:
                source_normalized_mean = source_normalized_mean[[2, 1, 0, 3]]
                source_normalized_std = source_normalized_std[[2, 1, 0, 3]]
        elif target_color_order == ColorOrder.GRAY:

            rgb = source[:, :3, :, :]
            alpha = source[:, 3:4, :, :]
            if source_normalized:
                if mean_std:
                    source_normalized_mean_alpha = source_normalized_mean[3:]
                    source_normalized_std_alpha = source_normalized_std[3:]
                    alpha = (alpha * source_normalized_std_alpha.reshape(1, -1, 1, 1) +
                             source_normalized_mean_alpha.reshape(1, -1, 1, 1))
                background = torch.ones_like(rgb)
                source = rgb * alpha + background * (1 - alpha)
            else:
                alpha = source[:, 3:4, :, :] / 255.0
                background = torch.ones_like(rgb) * 255
                source = rgb * alpha + background * (1 - alpha)

            if source.dtype == torch.uint8:
                source = source.float()

            if mean_std:
                source = gray_transform(source * source_normalized_std[:3].reshape(1, -1, 1, 1) +
                                        source_normalized_mean[:3].reshape(1, -1, 1, 1))
                source_normalized_mean = None
                source_normalized_std = None
            else:
                source = gray_transform(source)
    elif source_color_order == ColorOrder.GRAY:
        if target_color_order == ColorOrder.RGB or target_color_order == ColorOrder.BGR:
            source = source.repeat(1, 3, 1, 1)
            if mean_std:
                source_normalized_mean = source_normalized_mean.repeat(3)
                source_normalized_std = source_normalized_std.repeat(3)
        elif target_color_order == ColorOrder.RGBA or target_color_order == ColorOrder.BGRA:
            alpha = torch.ones_like(source)
            source = source.repeat(1, 3, 1, 1)
            if not source_normalized:
                alpha = alpha * 255
            source = torch.cat([source, alpha], dim=1)
            if mean_std:
                source_normalized_mean = source_normalized_mean.repeat(3)
                source_normalized_std = source_normalized_std.repeat(3)
                source_normalized_mean = torch.cat([source_normalized_mean, source_normalized_mean.new_tensor([1.0])])
                source_normalized_std = torch.cat([source_normalized_std, source_normalized_std.new_tensor([1e-9])])
    return source, source_normalized_mean, source_normalized_std


def numpy_bhwc_transform_source_by_color_order(source: np.ndarray,
                                               source_normalized: bool, source_normalized_mean, source_normalized_std,
                                               source_color_order: ColorOrder, target_color_order: ColorOrder):
    """
    将tensor bchw 维度顺序的图片根据颜色排序 生成新的图片和对应的归一化参数
    ⚠️不做归一化操作
    """
    if source_normalized_mean is not None and source_normalized_std is not None:
        mean_std = True
    else:
        mean_std = False

    if source_color_order == ColorOrder.BGR:
        if target_color_order == ColorOrder.RGB:
            source = source[:, :, :, ::-1]
            if mean_std:
                source_normalized_mean = source_normalized_mean[::-1]
                source_normalized_std = source_normalized_std[::-1]
        elif target_color_order == ColorOrder.BGR:
            pass
        elif target_color_order == ColorOrder.RGBA:
            alpha = np.ones_like(source[:, :, :, 0:1])
            if not source_normalized:
                alpha = alpha * 255
            source = np.concatenate([source[:, :, :, ::-1], alpha], axis=-1)
            if mean_std:
                source_normalized_mean = source_normalized_mean[::-1]
                source_normalized_std = source_normalized_std[::-1]
                source_normalized_mean = np.append(source_normalized_mean, 1.0)
                source_normalized_std = np.append(source_normalized_std, 1e-9)
        elif target_color_order == ColorOrder.BGRA:
            alpha = np.ones_like(source[:, :, :, 0:1])
            if not source_normalized:
                alpha = alpha * 255
            source = np.concatenate([source, alpha], axis=-1)
            if mean_std:
                source_normalized_mean = np.append(source_normalized_mean, 1.0)
                source_normalized_std = np.append(source_normalized_std, 1e-9)
        elif target_color_order == ColorOrder.GRAY:
            source = source[:, :, :, ::-1]
            if source.dtype == np.uint8:
                source = source.astype(np.float32)
            if mean_std:
                source = np_gray_transform(source * source_normalized_std[::-1].reshape(1, 1, -1) +
                                           source_normalized_mean[::-1].reshape(1, 1, -1))
                source_normalized_mean = None
                source_normalized_std = None
            else:
                source = np_gray_transform(source)
    elif source_color_order == ColorOrder.RGB:
        if target_color_order == ColorOrder.RGB:
            pass
        elif target_color_order == ColorOrder.BGR:
            source = source[:, :, :, ::-1]
            if mean_std:
                source_normalized_mean = source_normalized_mean[::-1]
                source_normalized_std = source_normalized_std[::-1]
        elif target_color_order == ColorOrder.RGBA:
            alpha = np.ones_like(source[:, :, :, 0:1])
            if not source_normalized:
                alpha = alpha * 255
            source = np.concatenate([source, alpha], axis=-1)
            if mean_std:
                source_normalized_mean = np.append(source_normalized_mean, 1.0)
                source_normalized_std = np.append(source_normalized_std, 1e-9)
        elif target_color_order == ColorOrder.BGRA:
            alpha = np.ones_like(source[:, :, :, 0:1])
            if not source_normalized:
                alpha = alpha * 255
            source = np.concatenate([source[:, :, :, ::-1], alpha], axis=-1)
            if mean_std:
                source_normalized_mean = source_normalized_mean[::-1]
                source_normalized_std = source_normalized_std[::-1]
                source_normalized_mean = np.append(source_normalized_mean, 1.0)
                source_normalized_std = np.append(source_normalized_std, 1e-9)
        elif target_color_order == ColorOrder.GRAY:
            if source.dtype == np.uint8:
                source = source.astype(np.float32)
            if mean_std:
                source = np_gray_transform(source * source_normalized_std.reshape(1, 1, -1) +
                                           source_normalized_mean.reshape(1, 1, -1))
                source_normalized_mean = None
                source_normalized_std = None
            else:
                source = np_gray_transform(source)
    elif source_color_order == ColorOrder.BGRA:
        if target_color_order == ColorOrder.RGB:
            bgr = source[:, :, :, :3]
            alpha = source[:, :, :, 3:4]
            if source_normalized:
                if mean_std:
                    source_normalized_mean_alpha = source_normalized_mean[3:]
                    source_normalized_std_alpha = source_normalized_std[3:]
                    alpha = (alpha * source_normalized_std_alpha.reshape(1, 1, 1, -1) +
                             source_normalized_mean_alpha.reshape(1, 1, 1, -1))
                background = np.ones_like(bgr)
                source = bgr * alpha + background * (1 - alpha)
            else:
                alpha = alpha / 255.0
                background = np.ones_like(bgr) * 255
                source = bgr * alpha + background * (1 - alpha)
            source = source[:, :, :, [2, 1, 0]]
            if mean_std:
                source_normalized_mean = source_normalized_mean[:3][::-1]
                source_normalized_std = source_normalized_std[:3][::-1]
        elif target_color_order == ColorOrder.BGR:
            bgr = source[:, :, :, :3]
            alpha = source[:, :, :, 3:4]
            if source_normalized:
                if mean_std:
                    source_normalized_mean_alpha = source_normalized_mean[3:]
                    source_normalized_std_alpha = source_normalized_std[3:]
                    alpha = (alpha * source_normalized_std_alpha.reshape(1, 1, 1, -1) +
                             source_normalized_mean_alpha.reshape(1, 1, 1, -1))
                background = np.ones_like(bgr)
                source = bgr * alpha + background * (1 - alpha)
            else:
                alpha = alpha / 255.0
                background = np.ones_like(bgr) * 255
                source = bgr * alpha + background * (1 - alpha)
            if mean_std:
                source_normalized_mean = source_normalized_mean[:3]
                source_normalized_std = source_normalized_std[:3]
        elif target_color_order == ColorOrder.RGBA:
            source = source[:, :, :, [2, 1, 0, 3]]
            if mean_std:
                source_normalized_mean = source_normalized_mean[[2, 1, 0, 3]]
                source_normalized_std = source_normalized_std[[2, 1, 0, 3]]
        elif target_color_order == ColorOrder.BGRA:
            pass
        elif target_color_order == ColorOrder.GRAY:
            bgr = source[:, :, :, :3]
            alpha = source[:, :, :, 3:4]
            if source_normalized:
                if mean_std:
                    source_normalized_mean_alpha = source_normalized_mean[3:]
                    source_normalized_std_alpha = source_normalized_std[3:]
                    alpha = (alpha * source_normalized_std_alpha.reshape(1, 1, 1, -1) +
                             source_normalized_mean_alpha.reshape(1, 1, 1, -1))
                background = np.ones_like(bgr)
                source = bgr * alpha + background * (1 - alpha)
            else:
                alpha = alpha / 255.0
                background = np.ones_like(bgr) * 255
                source = bgr * alpha + background * (1 - alpha)
            source = source[:, :, :, [2, 1, 0]]
            if mean_std:
                source = np_gray_transform(source * source_normalized_std[:3][::-1].reshape(1, 1, -1) +
                                           source_normalized_mean[:3][::-1].reshape(1, 1, -1))
                source_normalized_mean = None
                source_normalized_std = None
            else:
                source = np_gray_transform(source)
    elif source_color_order == ColorOrder.RGBA:
        if target_color_order == ColorOrder.RGB:
            rgb = source[:, :, :, :3]
            alpha = source[:, :, :, 3:4]
            if source_normalized:
                if mean_std:
                    source_normalized_mean_alpha = source_normalized_mean[3:]
                    source_normalized_std_alpha = source_normalized_std[3:]
                    alpha = (alpha * source_normalized_std_alpha.reshape(1, 1, 1, -1) +
                             source_normalized_mean_alpha.reshape(1, 1, 1, -1))
                background = np.ones_like(rgb)
                source = rgb * alpha + background * (1 - alpha)
            else:
                alpha = alpha.astype(np.float32) / 255.0
                background = np.ones_like(rgb) * 255
                source = rgb * alpha + background * (1 - alpha)
            if mean_std:
                source_normalized_mean = source_normalized_mean[:3]
                source_normalized_std = source_normalized_std[:3]
        elif target_color_order == ColorOrder.BGR:
            rgb = source[:, :, :, :3]
            alpha = source[:, :, :, 3:4]
            if source_normalized:
                if mean_std:
                    source_normalized_mean_alpha = source_normalized_mean[3:]
                    source_normalized_std_alpha = source_normalized_std[3:]
                    alpha = (alpha * source_normalized_std_alpha.reshape(1, 1, 1, -1) +
                             source_normalized_mean_alpha.reshape(1, 1, 1, -1))
                background = np.ones_like(rgb)
                source = rgb * alpha + background * (1 - alpha)
            else:
                alpha = alpha / 255.0
                background = np.ones_like(rgb) * 255
                source = rgb * alpha + background * (1 - alpha)
            source = source[:, :, :, [2, 1, 0]]
            if mean_std:
                source_normalized_mean = source_normalized_mean[:3][::-1]
                source_normalized_std = source_normalized_std[:3][::-1]
        elif target_color_order == ColorOrder.RGBA:
            pass
        elif target_color_order == ColorOrder.BGRA:
            source = source[:, :, :, [2, 1, 0, 3]]
            if mean_std:
                source_normalized_mean = source_normalized_mean[[2, 1, 0, 3]]
                source_normalized_std = source_normalized_std[[2, 1, 0, 3]]
        elif target_color_order == ColorOrder.GRAY:
            rgb = source[:, :, :, :3]
            alpha = source[:, :, :, 3:4]
            if source_normalized:
                if mean_std:
                    source_normalized_mean_alpha = source_normalized_mean[3:]
                    source_normalized_std_alpha = source_normalized_std[3:]
                    alpha = (alpha * source_normalized_std_alpha.reshape(1, 1, 1, -1) +
                             source_normalized_mean_alpha.reshape(1, 1, 1, -1))
                background = np.ones_like(rgb)
                source = rgb * alpha + background * (1 - alpha)
            else:
                alpha = source[:, :, :, 3:4] / 255.0
                background = np.ones_like(rgb) * 255
                source = rgb * alpha + background * (1 - alpha)

            if mean_std:
                source = np_gray_transform(source * source_normalized_std[:3].reshape(1, 1, -1) +
                                           source_normalized_mean[:3].reshape(1, 1, -1))
                source_normalized_mean = None
                source_normalized_std = None
            else:
                source = np_gray_transform(source)
    elif source_color_order == ColorOrder.GRAY:
        if target_color_order == ColorOrder.RGB or target_color_order == ColorOrder.BGR:
            source = np.repeat(source, repeats=3, axis=-1)
            if mean_std:
                source_normalized_mean = np.repeat(source_normalized_mean, repeats=3, axis=0)
                source_normalized_std = np.repeat(source_normalized_std, repeats=3, axis=0)
        elif target_color_order == ColorOrder.RGBA or target_color_order == ColorOrder.BGRA:
            alpha = np.ones_like(source)
            source = np.repeat(source, repeats=3, axis=-1)
            if not source_normalized:
                alpha = alpha * 255
            source = np.concatenate([source, alpha], axis=-1)

            if mean_std:
                source_normalized_mean = np.repeat(source_normalized_mean, repeats=3, axis=0)
                source_normalized_std = np.repeat(source_normalized_std, repeats=3, axis=0)
                source_normalized_mean = np.append(source_normalized_mean, 1.0)
                source_normalized_std = np.append(source_normalized_std, 1e-9)
    return source, source_normalized_mean, source_normalized_std


def bytes2bytes(source: Union[bytes, list[bytes]], target_image_format: Union[ImageFormat, str] = None):
    if target_image_format is None:
        return source
    if isinstance(target_image_format, str):
        target_image_format = ImageFormat(target_image_format)
    pils = bytes2pil(source)

    test_pils = pils
    if not isinstance(pils, list):
        test_pils = [test_pils]
    if all([eq_image_format(pil.format, target_image_format) for pil in test_pils]):
        return source
    else:
        return pil2bytes(pils, target_image_format)


def pil2file(source: Union[Image.Image, list[Image.Image]], target_file: str, **kwargs):
    if isinstance(source, list):
        base_path, ext = target_file.rsplit('.', 1)
        file_paths = [f"{base_path}.{i}.{ext}" for i in range(len(source))]
        for i, img in enumerate(source):
            img.save(file_paths[i])
    else:
        source.save(target_file)


def file2pil(source: Union[str, list[str]], target_color_mode: Union[PilColorModel, str] = None, **kwargs):
    if isinstance(source, str):
        if os.path.isdir(source):
            files = path_util.list_files(source, suffixes=['.jpg', '.png', '.jpeg', '.JPG', '.PNG', '.JPEG'])
            target = [file2pil(file, target_color_mode, **kwargs) for file in files]
        else:
            target = Image.open(source)
            if target_color_mode is not None:
                if isinstance(target_color_mode, PilColorModel):
                    target_color_mode = target_color_mode.value
                target = target.convert(target_color_mode)
    else:
        target = []
        for file in source:
            pil = file2pil(file, target_color_mode, **kwargs)
            if isinstance(pil, list):
                target.extend(pil)
            else:
                target.append(pil)
    return target


def pil2bytes(source: Union[Image.Image, list[Image.Image]], target_image_format: Union[ImageFormat, str] = None,
              **kwargs):
    if target_image_format is not None and isinstance(target_image_format, str):
        target_image_format = ImageFormat(target_image_format)
    if target_image_format is None:
        target_image_format = ImageFormat.PNG

    if isinstance(source, list):
        target = [pil2bytes(img, target_image_format, **kwargs) for img in source]
    else:
        byte_io = io.BytesIO()
        source.save(byte_io, format=target_image_format.value)
        target = byte_io.getvalue()
        byte_io.close()
    return target


def bytes2pil(source: Union[bytes, list[bytes]], target_color_mode: Union[PilColorModel, str] = None):
    if target_color_mode is not None and isinstance(target_color_mode, str):
        target_color_mode = PilColorModel(target_color_mode)

    if isinstance(source, list):
        target = [bytes2pil(data, target_color_mode=target_color_mode) for data in source]
    else:
        with io.BytesIO(source) as buffer:
            target = Image.open(buffer)
            target.load()  # 确保加载
        # buffer 自动关闭，img 已独立
        if target_color_mode is not None and target.mode != target_color_mode.value:
            target = target.convert(target_color_mode.value)
        elif target_color_mode is None and target.mode not in ['RGB', 'RGBA', 'L']:
            target = target.convert('RGB')

    return target


def url2bytes(source: Union[str, list[str]], target_image_format: Union[ImageFormat, str] = None):
    if target_image_format is not None and isinstance(target_image_format, str):
        target_image_format = ImageFormat(target_image_format)

    if isinstance(source, list):
        target = [url2bytes(url, target_image_format=target_image_format) for url in source]
    else:

        target = requests.get(source).content
        if target_image_format is not None:
            target = bytes2bytes(target, target_image_format)
    return target


def pil2numpy(source: Union[Image.Image, list[Image.Image]],
              target_dim_order: Union[DimOrder, str] = None,
              target_color_order: Union[ColorOrder, str] = ColorOrder.BGR,
              target_normalized: bool = False,
              target_normalized_mean: Union[list[float], tuple[float], np.ndarray] = None,
              target_normalized_std: Union[list[float], tuple[float], np.ndarray] = None,
              **kwargs):
    if isinstance(source, Image.Image):
        source = [source]

    if target_dim_order is not None and isinstance(target_dim_order, str):
        target_dim_order = DimOrder(target_dim_order)

    if target_color_order is not None and isinstance(target_color_order, str):
        target_color_order = ColorOrder(target_color_order)

    if target_color_order is None:
        target_color_order = ColorOrder.BGR
    if target_dim_order is None:
        if len(source) > 1:
            target_dim_order = DimOrder.BHWC
        else:
            target_dim_order = DimOrder.HWC
    else:
        if len(source) > 1:
            if target_dim_order == DimOrder.CHW:
                target_dim_order = DimOrder.BCHW
            elif target_dim_order == DimOrder.HWC:
                target_dim_order = DimOrder.BHWC

    if target_color_order == ColorOrder.GRAY:
        source = [img.convert('L') for img in source]
    elif target_color_order == ColorOrder.RGB or target_color_order == ColorOrder.BGR:
        source = [img.convert('RGB') for img in source]
    elif target_color_order == ColorOrder.RGBA or target_color_order == ColorOrder.BGRA:
        source = [img.convert('RGBA') for img in source]
    else:
        raise ValueError(f"color_order: {target_color_order.value} not support")

    np_images = [np.array(img) for img in source]
    batch_images = np.stack(np_images, axis=0)

    if target_color_order == ColorOrder.GRAY:
        batch_images = np.expand_dims(batch_images, axis=-1)
    elif target_color_order == ColorOrder.BGR:
        batch_images = batch_images[:, :, :, ::-1]
    elif target_color_order == ColorOrder.BGRA:
        batch_images = batch_images[:, :, :, [2, 1, 0, 3]]

    if target_normalized:
        batch_images = batch_images.astype(np.float32)
        if target_normalized_std is not None and target_normalized_mean is not None:
            target_normalized_mean = np.array(target_normalized_mean).reshape(1, 1, -1)
            target_normalized_std = np.array(target_normalized_std).reshape(1, 1, -1)
            batch_images = (batch_images - target_normalized_mean) / target_normalized_std
        else:
            batch_images = batch_images / 255.0

    target = batch_images_bhwc = batch_images

    if target_dim_order == DimOrder.HWC:
        target = batch_images_bhwc[0]
    elif target_dim_order == DimOrder.BCHW:
        target = np.transpose(batch_images_bhwc, (0, 3, 1, 2))
    elif target_dim_order == DimOrder.CHW:
        target = np.transpose(batch_images_bhwc, (0, 3, 1, 2))[0]
    return target


def numpy2pil(source: np.ndarray,
              source_dim_order: Union[DimOrder, str] = None,
              source_color_order: Union[ColorOrder, str] = ColorOrder.BGR,
              source_normalized_mean: Union[list[float], tuple[float], np.ndarray] = None,
              source_normalized_std: Union[list[float], tuple[float], np.ndarray] = None,
              target_color_mode: Union[PilColorModel, str] = None,
              **kwargs):

    if source.ndim == 3 or source.ndim == 2:
        target_batch = False
    elif source.ndim == 4:
        target_batch = True
    else:
        raise ValueError(f"source.ndim: {source.ndim} not support")

    source, source_dim_order, source_color_order, source_normalized, source_normalized_mean, source_normalized_std = \
        parse_source_numpy_BHWC(source=source,
                                source_dim_order=source_dim_order,
                                source_color_order=source_color_order,
                                source_normalized_mean=source_normalized_mean,
                                source_normalized_std=source_normalized_std)

    if source_normalized:
        if source_normalized_std is None or source_normalized_mean is None:
            source = np.clip(source * 255.0, 0, 255).astype(np.uint8)
        else:
            source = source * source_normalized_std.reshape(1, 1, 1, -1) + source_normalized_mean.reshape(1, 1, 1, -1)
            source = np.clip(source * 255, 0, 255).astype(np.uint8)

    if target_color_mode is not None and isinstance(target_color_mode, str):
        target_color_mode = PilColorModel(target_color_mode)

    if target_color_mode is None:
        if source_color_order == ColorOrder.GRAY or source_color_order == ColorOrder.RGB or source_color_order == ColorOrder.BGR:
            target_color_mode = PilColorModel.RGB
        elif source_color_order == ColorOrder.RGBA or source_color_order == ColorOrder.BGRA:
            target_color_mode = PilColorModel.RGBA
        else:
            raise ValueError(f"color_order: {source_color_order.value} not support")

    target = []
    for img in source:
        if source_color_order == ColorOrder.GRAY:
            img = np.squeeze(img, axis=-1)
            target.append(Image.fromarray(img, mode='L').convert(target_color_mode.value))
        elif source_color_order == ColorOrder.BGR:
            target.append(Image.fromarray(img[:, :, ::-1], mode='RGB').convert(target_color_mode.value))
        elif source_color_order == ColorOrder.RGB:
            target.append(Image.fromarray(img, mode='RGB').convert(target_color_mode.value))
        elif source_color_order == ColorOrder.BGRA:
            target.append(Image.fromarray(img[:, :, [2, 1, 0, 3]], mode='RGBA').convert(target_color_mode.value))
        elif source_color_order == ColorOrder.RGBA:
            target.append(Image.fromarray(img, mode='RGBA').convert(target_color_mode.value))
        else:
            raise ValueError(f"color_order: {source_color_order.value} not support")
    return target if target_batch else target[0]


def tensor2tensor(source: torch.Tensor,
                  source_dim_order: Union[DimOrder, str] = None,
                  source_color_order: Union[ColorOrder, str] = None,
                  source_normalized: bool = None,
                  source_normalized_mean: Union[list[float], tuple[float], np.ndarray, torch.Tensor] = None,
                  source_normalized_std: Union[list[float], tuple[float], np.ndarray, torch.Tensor] = None,

                  target_dim_order: Union[DimOrder, str] = None,
                  target_color_order: Union[ColorOrder, str] = None,
                  target_normalized: bool = None,
                  target_normalized_mean: Union[list[float], tuple[float], np.ndarray, torch.Tensor] = None,
                  target_normalized_std: Union[list[float], tuple[float], np.ndarray, torch.Tensor] = None,
                  target_device: Union[torch.device, str] = None):
    target_device = target_device or source.device
    if target_color_order is not None:
        target_color_order = ColorOrder(target_color_order)
    if target_color_order is None:
        target_color_order = ColorOrder.RGB

    if target_dim_order is not None and isinstance(target_dim_order, str):
        target_dim_order = DimOrder(target_dim_order)

    if target_dim_order is None:
        if source.ndim == 3 or source.ndim == 2:
            target_dim_order = DimOrder.CHW
        elif source.ndim == 4:
            target_dim_order = DimOrder.BCHW
        else:
            raise ValueError(f"source.ndim: {source.ndim} not support")

    # 统一处理为 BCHW 维度分布
    source, source_dim_order, source_color_order, source_normalized, source_normalized_mean, source_normalized_std = \
        parse_source_tensor_BCHW(source=source,
                                 source_dim_order=source_dim_order,
                                 source_color_order=source_color_order,
                                 source_normalized=source_normalized,
                                 source_normalized_mean=source_normalized_mean,
                                 source_normalized_std=source_normalized_std)

    target_normalized, target_normalized_mean, target_normalized_std = \
        parse_target_tensor_normalized(target_normalized=target_normalized,
                                       target_normalized_mean=target_normalized_mean,
                                       target_normalized_std=target_normalized_std,
                                       target_device=target_device)
    if source.device != target_device:
        source = source.to(target_device)

    # 根据源颜色顺序和目标颜色顺序转换
    source, source_normalized_mean, source_normalized_std = \
        tensor_bchw_transform_source_by_color_order(source=source,
                                                    source_normalized=source_normalized,
                                                    source_normalized_mean=source_normalized_mean,
                                                    source_normalized_std=source_normalized_std,
                                                    source_color_order=source_color_order,
                                                    target_color_order=target_color_order)

    source_mean_std = source_normalized_mean is not None and source_normalized_std is not None
    target_mean_std = target_normalized_mean is not None and target_normalized_std is not None
    source_normalized_mean_reshape = source_normalized_mean.reshape(1, -1, 1, 1) if source_mean_std else None
    source_normalized_std_reshape = source_normalized_std.reshape(1, -1, 1, 1) if source_mean_std else None
    target_normalized_mean_reshape = target_normalized_mean.reshape(1, -1, 1, 1) if target_mean_std else None
    target_normalized_std_reshape = target_normalized_std.reshape(1, -1, 1, 1) if target_mean_std else None

    if source_normalized is True and target_normalized is True:
        if source_mean_std and target_mean_std:
            if all(source_normalized_mean == target_normalized_mean) and \
                    all(source_normalized_std == target_normalized_std):
                target = source
            else:
                source = source * source_normalized_std_reshape + source_normalized_mean_reshape
                target = (source - target_normalized_mean_reshape) / target_normalized_std_reshape
        elif source_mean_std and not target_mean_std:
            target = source * source_normalized_std_reshape + source_normalized_mean_reshape
        elif not source_mean_std and target_mean_std:
            target = (source - target_normalized_mean_reshape) / target_normalized_std_reshape
        else:
            target = source
        if not target_mean_std:
            target = torch.clamp(target, 0.0, 1.0)
    elif source_normalized is False and target_normalized is False:
        if source.dtype == torch.uint8:
            target = source
        else:
            target = source.byte()
    elif source_normalized is True and target_normalized is False:
        if source_mean_std:
            source = source * source_normalized_std_reshape + source_normalized_mean_reshape
        target = torch.clamp(source * 255, 0, 255).byte()
    elif source_normalized is False and target_normalized is True:
        target = source.float() / 255.0
        if target_mean_std:
            target = (target - target_normalized_mean_reshape) / target_normalized_std_reshape
        else:
            target = torch.clamp(target, 0.0, 1.0)
    else:
        raise ValueError(f"source_normalized: {source_normalized} target_normalized: {target_normalized} not support")

    if target_dim_order == DimOrder.BHWC:
        target = target.permute(0, 2, 3, 1)
    elif target_dim_order == DimOrder.HWC:
        if target.shape[0] == 1:
            target = target.squeeze(0).permute(1, 2, 0)
        else:
            target = target.permute(0, 2, 3, 1)
    elif target_dim_order == DimOrder.CHW:
        if target.shape[0] == 1:
            target = target.squeeze(0)
        else:
            pass

    return target


def numpy2numpy(source: np.ndarray,
                source_dim_order: Union[DimOrder, str] = None,
                source_color_order: Union[ColorOrder, str] = None,
                source_normalized: bool = None,
                source_normalized_mean: Union[list[float], tuple[float], np.ndarray, torch.Tensor] = None,
                source_normalized_std: Union[list[float], tuple[float], np.ndarray, torch.Tensor] = None,

                target_dim_order: Union[DimOrder, str] = None,
                target_color_order: Union[ColorOrder, str] = None,
                target_normalized: bool = None,
                target_normalized_mean: Union[list[float], tuple[float], np.ndarray, torch.Tensor] = None,
                target_normalized_std: Union[list[float], tuple[float], np.ndarray, torch.Tensor] = None):
    if target_color_order is not None and isinstance(target_color_order, str):
        target_color_order = ColorOrder(target_color_order)
    if target_color_order is None:
        target_color_order = ColorOrder.BGR

    if target_dim_order is not None and isinstance(target_dim_order, str):
        target_dim_order = DimOrder(target_dim_order)

    if target_dim_order is None:
        if source.ndim == 3 or source.ndim == 2:
            target_dim_order = DimOrder.HWC
        elif source.ndim == 4:
            target_dim_order = DimOrder.BHWC
        else:
            raise ValueError(f"source.ndim: {source.ndim} not support")
    # 统一处理numpy 为 BHWC 维度分布
    source, source_dim_order, source_color_order, source_normalized, source_normalized_mean, source_normalized_std = \
        parse_source_numpy_BHWC(source=source,
                                source_dim_order=source_dim_order,
                                source_color_order=source_color_order,
                                source_normalized=source_normalized,
                                source_normalized_mean=source_normalized_mean,
                                source_normalized_std=source_normalized_std)

    target_normalized, target_normalized_mean, target_normalized_std = \
        parse_target_numpy_normalized(target_normalized=target_normalized,
                                      target_normalized_mean=target_normalized_mean,
                                      target_normalized_std=target_normalized_std)

    source, source_normalized_mean, source_normalized_std = \
        numpy_bhwc_transform_source_by_color_order(source=source,
                                                   source_normalized=source_normalized,
                                                   source_normalized_mean=source_normalized_mean,
                                                   source_normalized_std=source_normalized_std,
                                                   source_color_order=source_color_order,
                                                   target_color_order=target_color_order)

    source_mean_std = source_normalized_mean is not None and source_normalized_std is not None
    target_mean_std = target_normalized_mean is not None and target_normalized_std is not None
    source_normalized_mean_reshape = source_normalized_mean.reshape(1, 1, 1, -1) if source_mean_std else None
    source_normalized_std_reshape = source_normalized_std.reshape(1, 1, 1, -1) if source_mean_std else None
    target_normalized_mean_reshape = target_normalized_mean.reshape(1, 1, 1, -1) if target_mean_std else None
    target_normalized_std_reshape = target_normalized_std.reshape(1, 1, 1, -1) if target_mean_std else None

    if source_normalized is True and target_normalized is True:
        if source_mean_std and target_mean_std:
            if all(source_normalized_mean == target_normalized_mean) and \
                    all(source_normalized_std == target_normalized_std):
                target = source
            else:
                source = source * source_normalized_std_reshape + source_normalized_mean_reshape
                target = (source - target_normalized_mean_reshape) / target_normalized_std_reshape
        elif source_mean_std and not target_mean_std:
            target = source * source_normalized_std_reshape + source_normalized_mean_reshape
        elif not source_mean_std and target_mean_std:
            target = (source - target_normalized_mean_reshape) / target_normalized_std_reshape
        else:
            target = source
        if not target_mean_std:
            target = np.clip(target, 0.0, 1.0)
    elif source_normalized is False and target_normalized is False:
        if source.dtype == np.uint8:
            target = source
        else:
            target = source.astype(np.uint8)
    elif source_normalized is True and target_normalized is False:
        if source_mean_std:
            source = source * source_normalized_std_reshape + source_normalized_mean_reshape
        target = np.clip(source * 255, 0, 255).astype(np.uint8)
    elif source_normalized is False and target_normalized is True:
        if source.dtype != np.float32:
            source = source.astype(np.float32)
        target = source / 255.0
        if target_mean_std:
            target = (target - target_normalized_mean_reshape) / target_normalized_std_reshape
        else:
            target = np.clip(target, 0.0, 1.0)
    else:
        raise ValueError(f"source_normalized: {source_normalized} target_normalized: {target_normalized} not support")

    if target_dim_order == DimOrder.BCHW:
        target = np.transpose(target, (0, 3, 1, 2))
    elif target_dim_order == DimOrder.HWC:
        if target.shape[0] == 1:
            target = np.squeeze(target, axis=0)
        else:
            pass
    elif target_dim_order == DimOrder.CHW:
        if target.shape[0] == 1:
            target = np.transpose(np.squeeze(target, axis=0), (2, 0, 1))
        else:
            target = np.transpose((0, 3, 1, 2))

    return target


def numpy2tensor(source: np.ndarray,
                 source_dim_order: Union[DimOrder, str] = None,
                 source_color_order: Union[ColorOrder, str] = None,
                 source_normalized: bool = None,
                 source_normalized_mean: Union[list[float], tuple[float], np.ndarray, torch.Tensor] = None,
                 source_normalized_std: Union[list[float], tuple[float], np.ndarray, torch.Tensor] = None,
                 target_dim_order: Union[DimOrder, str] = None,
                 target_color_order: Union[ColorOrder, str] = None,
                 target_normalized: bool = None,
                 target_normalized_mean: Union[list[float], tuple[float], np.ndarray, torch.Tensor] = None,
                 target_normalized_std: Union[list[float], tuple[float], np.ndarray, torch.Tensor] = None,
                 target_device: Union[torch.device, str] = None,
                 **kwargs):
    target_device = target_device or def_torch_device

    # 统一处理numpy 为 BHWC 维度分布
    source, source_dim_order, source_color_order, source_normalized, source_normalized_mean, source_normalized_std = \
        parse_source_numpy_BHWC(source=source,
                                source_dim_order=source_dim_order,
                                source_color_order=source_color_order,
                                source_normalized=source_normalized,
                                source_normalized_mean=source_normalized_mean,
                                source_normalized_std=source_normalized_std)

    source_normalized_std = torch.from_numpy(source_normalized_std).to(
        target_device) if source_normalized_std is not None else None
    source_normalized_mean = torch.from_numpy(source_normalized_mean).to(
        target_device) if source_normalized_mean is not None else None
    try:
        source = torch.from_numpy(source).to(target_device)
    except ValueError:
        source = torch.from_numpy(source.copy()).to(target_device)
    # BHWC to BCHW
    source = source.permute(0, 3, 1, 2)
    return tensor2tensor(source=source,
                         source_dim_order=DimOrder.BCHW,
                         source_color_order=source_color_order,
                         source_normalized=source_normalized,
                         source_normalized_mean=source_normalized_mean,
                         source_normalized_std=source_normalized_std,

                         target_dim_order=target_dim_order,
                         target_color_order=target_color_order,
                         target_normalized=target_normalized,
                         target_normalized_mean=target_normalized_mean,
                         target_normalized_std=target_normalized_std,
                         target_device=target_device)


def tensor2numpy(source: torch.Tensor,
                 source_dim_order: Union[DimOrder, str] = None,
                 source_color_order: Union[ColorOrder, str] = None,
                 source_normalized: bool = None,
                 source_normalized_mean: Union[list[float], tuple[float], np.ndarray, torch.Tensor] = None,
                 source_normalized_std: Union[list[float], tuple[float], np.ndarray, torch.Tensor] = None,
                 target_dim_order: Union[DimOrder, str] = None,
                 target_color_order: Union[ColorOrder, str] = None,
                 target_normalized: bool = None,
                 target_normalized_mean: Union[list[float], tuple[float], np.ndarray, torch.Tensor] = None,
                 target_normalized_std: Union[list[float], tuple[float], np.ndarray, torch.Tensor] = None,
                 **kwargs):
    if target_color_order is not None and isinstance(target_color_order, str):
        target_color_order = ColorOrder(target_color_order)
    if target_color_order is None:
        target_color_order = ColorOrder.BGR

    if target_dim_order is not None and isinstance(target_dim_order, str):
        target_dim_order = DimOrder(target_dim_order)

    if target_dim_order is None:
        if source.ndim == 3 or source.ndim == 2:
            target_dim_order = DimOrder.HWC
        elif source.ndim == 4:
            target_dim_order = DimOrder.BHWC
        else:
            raise ValueError(f"source.ndim: {source.ndim} not support")

    if target_normalized is not True and target_normalized_mean is None or target_normalized_std is None:
        target_normalized = False
    # 统一处理numpy 为 BHWC 维度分布
    source, source_dim_order, source_color_order, source_normalized, source_normalized_mean, source_normalized_std = \
        parse_source_tensor_BCHW(source=source,
                                 source_dim_order=source_dim_order,
                                 source_color_order=source_color_order,
                                 source_normalized=source_normalized,
                                 source_normalized_mean=source_normalized_mean,
                                 source_normalized_std=source_normalized_std)

    target = tensor2tensor(source=source,
                           source_dim_order=DimOrder.BCHW,
                           source_color_order=source_color_order,
                           source_normalized=source_normalized,
                           source_normalized_mean=source_normalized_mean,
                           source_normalized_std=source_normalized_std,

                           target_dim_order=target_dim_order,
                           target_color_order=target_color_order,
                           target_normalized=target_normalized,
                           target_normalized_mean=target_normalized_mean,
                           target_normalized_std=target_normalized_std)
    return target.cpu().numpy()


def pil2tensor(source: Union[Image.Image, list[Image.Image]],
               target_dim_order: Union[DimOrder, str] = None,
               target_color_order: Union[ColorOrder, str] = None,
               target_normalized: bool = None,
               target_normalized_mean: Union[list[float], tuple[float], np.ndarray, torch.Tensor] = None,
               target_normalized_std: Union[list[float], tuple[float], np.ndarray, torch.Tensor] = None,
               target_device: Union[torch.device, str] = None,
               **kwargs):
    if isinstance(source, Image.Image):
        source = [source]

    if target_dim_order is None:
        if len(source) > 1:
            target_dim_order = DimOrder.BCHW
        else:
            target_dim_order = DimOrder.CHW
    # if target_color_order is None:
    #     target_color_order = ColorOrder.RGB
    # if target_device is None:
    #     target_device = def_torch_device
    # if target_normalized is not False and target_normalized_mean is not None and target_normalized_std is not None:
    #     if isinstance(target_normalized_mean, (list, tuple)):
    #         target_normalized_mean = np.array(target_normalized_mean)
    #     if isinstance(target_normalized_std, np.ndarray):
    #         target_normalized_std = torch.from_numpy(target_normalized_std).to(target_device)
    #     if isinstance(target_normalized_std, (list, tuple)):
    #         target_normalized_std = np.array(target_normalized_std)
    #     if isinstance(target_normalized_mean, np.ndarray):
    #         target_normalized_mean = torch.from_numpy(target_normalized_mean).to(target_device)
    # elif target_normalized is None:
    #     target_normalized = True

    numpy_images = pil2numpy(source, target_dim_order=DimOrder.BCHW, target_color_order=ColorOrder.RGB,
                             target_normalized=False)

    return numpy2tensor(numpy_images,
                        source_dim_order=DimOrder.BCHW,
                        source_color_order=ColorOrder.RGB,
                        source_normalized=False,
                        target_dim_order=target_dim_order,
                        target_color_order=target_color_order,
                        target_normalized=target_normalized,
                        target_normalized_mean=target_normalized_mean,
                        target_normalized_std=target_normalized_std,
                        target_device=target_device
                        )


def tensor2pil(source: Union[torch.Tensor, list[torch.Tensor]],
               source_dim_order: Union[DimOrder, str] = None,
               source_color_order: Union[ColorOrder, str] = None,
               source_normalized: bool = None,
               source_normalized_mean: Union[list[float], tuple[float], np.ndarray, torch.Tensor] = None,
               source_normalized_std: Union[list[float], tuple[float], np.ndarray, torch.Tensor] = None,
               target_color_mode: Union[PilColorModel, str] = None,
               **kwargs):
    numpy_image = tensor2numpy(source,
                               source_dim_order,
                               source_color_order,
                               source_normalized,
                               source_normalized_mean,
                               source_normalized_std,
                               target_normalized=False,
                               target_color_order=ColorOrder.BGR)
    return numpy2pil(numpy_image,
                     source_color_order=ColorOrder.BGR,
                     source_normalized=False,
                     target_color_mode=target_color_mode)


def numpy2bytes(source: np.ndarray,
                source_dim_order: Union[DimOrder, str] = None,
                source_color_order: Union[ColorOrder, str] = None,
                source_normalized: bool = None,
                source_normalized_mean: Union[list[float], tuple[float], np.ndarray] = None,
                source_normalized_std: Union[list[float], tuple[float], np.ndarray] = None,
                target_image_format: Union[ImageFormat, str] = None):
    if target_image_format is not None and isinstance(target_image_format, ImageFormat):
        target_image_format = ImageFormat(target_image_format)

    if target_image_format == ImageFormat.PNG or target_image_format == ImageFormat.JPG:
        bgr_image = numpy2numpy(source,
                                source_dim_order=source_dim_order,
                                source_color_order=source_color_order,
                                source_normalized=source_normalized,
                                source_normalized_mean=source_normalized_mean,
                                source_normalized_std=source_normalized_std,
                                target_color_order=ColorOrder.BGRA if target_image_format == ImageFormat.PNG else ColorOrder.BGR,
                                target_normalized=False
                                )

        if bgr_image.ndim == 3:
            success, encoded_image = cv2.imencode(f'.{target_image_format.value.lower()}', bgr_image)
            if success:
                return encoded_image.tobytes()
        elif bgr_image.ndim == 4:
            bytes_list = []
            for bgr_img in bgr_image:
                success, encoded_image = cv2.imencode(f'.{target_image_format.value.lower()}', bgr_img)
                if success:
                    bytes_list.append(encoded_image.tobytes())
            return bytes_list
    else:
        pil_image = numpy2pil(source,
                              source_dim_order=source_dim_order,
                              source_color_order=source_color_order,
                              source_normalized=source_normalized,
                              source_normalized_mean=source_normalized_mean,
                              source_normalized_std=source_normalized_std)
        return pil2bytes(pil_image, target_image_format=target_image_format)


def bytes2numpy(source: Union[bytes, list[bytes]],
                target_dim_order: Union[DimOrder, str] = None,
                target_color_order: Union[ColorOrder, str] = None,
                target_normalized: bool = None,
                target_normalized_mean: Union[list[float], tuple[float], np.ndarray] = None,
                target_normalized_std: Union[list[float], tuple[float], np.ndarray] = None,
                ):
    pil_image = bytes2pil(source)
    return pil2numpy(pil_image,
                     target_dim_order=target_dim_order,
                     target_color_order=target_color_order,
                     target_normalized=target_normalized,
                     target_normalized_mean=target_normalized_mean,
                     target_normalized_std=target_normalized_std)


def bytes2base64(source: Union[bytes, list[bytes]],
                 target_image_format: Union[ImageFormat, str] = None, target_data_url: bool = False):
    if target_data_url is None:
        target_data_url = False
    if target_image_format is not None:
        source = bytes2bytes(source, target_image_format=target_image_format)

    if isinstance(source, list):
        return [bytes2base64(i, target_image_format=target_image_format, target_data_url=target_data_url) for i
                in source]
    else:
        if target_data_url:
            image_format = bytes2pil(source).format
            data_url_header = f'data:image/{image_format.lower()};base64,'
            return data_url_header + base64.b64encode(source).decode('utf-8')
        else:
            return base64.b64encode(source).decode('utf-8')


def base642bytes(source: Union[str, list[str]], target_image_format: Union[ImageFormat, str] = None):
    if isinstance(source, list):
        return [base642bytes(s, target_image_format) for s in source]
    else:
        target = base64.b64decode(source)
        if target_image_format is not None:
            target = bytes2bytes(target, target_image_format=target_image_format)
        return target


def pil2base64(source: Union[Image.Image, list[Image.Image]],
               target_image_format: Union[ImageFormat, str] = None, target_data_url: bool = False):
    return bytes2base64(pil2bytes(source, target_image_format=target_image_format), target_data_url=target_data_url)


def base642pil(source: Union[str, list[str]], target_image_format: Union[ImageFormat, str] = None,
               target_color_mode: Union[PilColorModel, str] = None):
    return bytes2pil(base642bytes(source, target_image_format=target_image_format), target_color_mode=target_color_mode)


def url2pil(source: Union[str, list[str]], target_color_mode: Union[PilColorModel, str] = None):
    return bytes2pil(url2bytes(source), target_color_mode=target_color_mode)


def base642numpy(source: Union[str, list[str]],
                 target_dim_order: Union[DimOrder, str] = None,
                 target_color_order: Union[ColorOrder, str] = None,
                 target_normalized: bool = None,
                 target_normalized_mean: Union[list[float], tuple[float], np.ndarray] = None,
                 target_normalized_std: Union[list[float], tuple[float], np.ndarray] = None,
                 ):
    return bytes2numpy(base642bytes(source),
                       target_dim_order=target_dim_order,
                       target_color_order=target_color_order,
                       target_normalized=target_normalized,
                       target_normalized_mean=target_normalized_mean,
                       target_normalized_std=target_normalized_std)


def numpy2base64(source: np.ndarray,
                 source_dim_order: Union[DimOrder, str] = None,
                 source_color_order: Union[ColorOrder, str] = None,
                 source_normalized: bool = None,
                 source_normalized_mean: Union[list[float], tuple[float], np.ndarray] = None,
                 source_normalized_std: Union[list[float], tuple[float], np.ndarray] = None,
                 target_image_format: Union[ImageFormat, str] = None, target_data_url: bool = False):
    return bytes2base64(numpy2bytes(source,
                                    source_dim_order=source_dim_order,
                                    source_color_order=source_color_order,
                                    source_normalized=source_normalized,
                                    source_normalized_mean=source_normalized_mean,
                                    source_normalized_std=source_normalized_std,
                                    target_image_format=target_image_format), target_data_url=target_data_url)


# numpy <-> file: numpy <-> pil <-> file

def numpy2file(source: np.ndarray,
               source_dim_order: Union[DimOrder, str] = None,
               source_color_order: Union[ColorOrder, str] = None,
               source_normalized: bool = None,
               source_normalized_mean: Union[list[float], tuple[float], np.ndarray] = None,
               source_normalized_std: Union[list[float], tuple[float], np.ndarray] = None,
               target_file: str = None):
    pil2file(numpy2pil(source,
                       source_dim_order=source_dim_order,
                       source_color_order=source_color_order,
                       source_normalized=source_normalized,
                       source_normalized_mean=source_normalized_mean,
                       source_normalized_std=source_normalized_std,
                       ),
             target_file=target_file)


def file2numpy(source: str,
               target_dim_order: Union[DimOrder, str] = None,
               target_color_order: Union[ColorOrder, str] = None,
               target_normalized: bool = None,
               target_normalized_mean: Union[list[float], tuple[float], np.ndarray] = None,
               target_normalized_std: Union[list[float], tuple[float], np.ndarray] = None,
               ):
    return pil2numpy(file2pil(source),
                     target_dim_order=target_dim_order,
                     target_color_order=target_color_order,
                     target_normalized=target_normalized,
                     target_normalized_mean=target_normalized_mean,
                     target_normalized_std=target_normalized_std)


def url2numpy(source: Union[str, list[str]],
              target_dim_order: Union[DimOrder, str] = None,
              target_color_order: Union[ColorOrder, str] = None,
              target_normalized: bool = None,
              target_normalized_mean: Union[list[float], tuple[float], np.ndarray] = None,
              target_normalized_std: Union[list[float], tuple[float], np.ndarray] = None,
              ):
    return bytes2numpy(url2bytes(source),
                       target_dim_order=target_dim_order,
                       target_color_order=target_color_order,
                       target_normalized=target_normalized,
                       target_normalized_mean=target_normalized_mean,
                       target_normalized_std=target_normalized_std)


def tensor2base64(source: torch.Tensor,
                  source_dim_order: Union[DimOrder, str] = None,
                  source_color_order: Union[ColorOrder, str] = None,
                  source_normalized: bool = None,
                  source_normalized_mean: Union[list[float], tuple[float], np.ndarray] = None,
                  source_normalized_std: Union[list[float], tuple[float], np.ndarray] = None,
                  target_image_format: Union[ImageFormat, str] = None,
                  target_data_url: bool = False
                  ):
    return pil2base64(tensor2pil(source,
                                 source_dim_order=source_dim_order,
                                 source_color_order=source_color_order,
                                 source_normalized=source_normalized,
                                 source_normalized_mean=source_normalized_mean,
                                 source_normalized_std=source_normalized_std),
                      target_image_format=target_image_format,
                      target_data_url=target_data_url)


def base642tensor(source: Union[str, list[str]],
                  target_dim_order: Union[DimOrder, str] = None,
                  target_color_order: Union[ColorOrder, str] = None,
                  target_normalized: bool = None,
                  target_normalized_mean: Union[list[float], tuple[float], np.ndarray] = None,
                  target_normalized_std: Union[list[float], tuple[float], np.ndarray] = None,
                  target_device: Union[str, torch.device] = None
                  ):
    return pil2tensor(base642pil(source,
                                 target_color_mode=target_color_order),
                      target_dim_order=target_dim_order,
                      target_color_order=target_color_order,
                      target_normalized=target_normalized,
                      target_normalized_mean=target_normalized_mean,
                      target_normalized_std=target_normalized_std,
                      target_device=target_device)


def tensor2file(source: torch.Tensor, target_file: Union[str, list[str]]):
    return pil2file(tensor2pil(source=source), target_file=target_file)


def file2tensor(source: Union[str, list[str]],
                target_dim_order: Union[DimOrder, str] = None,
                target_color_order: Union[ColorOrder, str] = None,
                target_normalized: bool = None,
                target_normalized_mean: Union[list[float], tuple[float], np.ndarray] = None,
                target_normalized_std: Union[list[float], tuple[float], np.ndarray] = None,
                target_device: Union[str, torch.device] = None
                ):
    return pil2tensor(source=file2pil(source=source),
                      target_dim_order=target_dim_order,
                      target_color_order=target_color_order,
                      target_normalized=target_normalized,
                      target_normalized_mean=target_normalized_mean,
                      target_normalized_std=target_normalized_std,
                      target_device=target_device)


def tensor2bytes(source: torch.Tensor,
                 source_dim_order: Union[DimOrder, str] = None,
                 source_color_order: Union[ColorOrder, str] = None,
                 source_normalized: bool = None,
                 source_normalized_mean: Union[list[float], tuple[float], np.ndarray, torch.Tensor] = None,
                 source_normalized_std: Union[list[float], tuple[float], np.ndarray, torch.Tensor] = None,
                 target_image_format: Union[ImageFormat, str] = None,
                 ):
    return numpy2bytes(source=tensor2numpy(source,
                                           source_dim_order=source_dim_order,
                                           source_color_order=source_color_order,
                                           source_normalized=source_normalized,
                                           source_normalized_mean=source_normalized_mean,
                                           source_normalized_std=source_normalized_std),
                       target_image_format=target_image_format)


def bytes2tensor(source: Union[bytes, list[bytes]],
                 target_dim_order: Union[DimOrder, str] = None,
                 target_color_order: Union[ColorOrder, str] = None,
                 target_normalized: bool = None,
                 target_normalized_mean: Union[list[float], tuple[float], np.ndarray] = None,
                 target_normalized_std: Union[list[float], tuple[float], np.ndarray] = None,
                 target_device: Union[str, torch.device] = None
                 ):
    return numpy2tensor(source=bytes2numpy(source),
                        target_dim_order=target_dim_order,
                        target_color_order=target_color_order,
                        target_normalized=target_normalized,
                        target_normalized_mean=target_normalized_mean,
                        target_normalized_std=target_normalized_std,
                        target_device=target_device)


def url2tensor(source: Union[str, list[str]],
               target_dim_order: Union[DimOrder, str] = None,
               target_color_order: Union[ColorOrder, str] = None,
               target_normalized: bool = None,
               target_normalized_mean: Union[list[float], tuple[float], np.ndarray] = None,
               target_normalized_std: Union[list[float], tuple[float], np.ndarray] = None,
               target_device: Union[str, torch.device] = None
               ):
    return pil2tensor(source=url2pil(source=source),
                      target_dim_order=target_dim_order,
                      target_color_order=target_color_order,
                      target_normalized=target_normalized,
                      target_normalized_mean=target_normalized_mean,
                      target_normalized_std=target_normalized_std,
                      target_device=target_device)


def base642file(source: Union[str, list[str]], target_file: Union[str, list[str]]):
    return pil2file(base642pil(source), target_file=target_file)


def file2base64(source: Union[str, list[str]], target_image_format: Union[ImageFormat, str] = None,
                target_data_url: bool = False):
    return pil2base64(file2pil(source), target_image_format=target_image_format, target_data_url=target_data_url)


def url2base64(source: Union[str, list[str]], target_image_format: Union[ImageFormat, str] = None,
               target_data_url: bool = False):
    return bytes2base64(url2bytes(source), target_image_format=target_image_format, target_data_url=target_data_url)


def url2file(source: Union[str, list[str]], target_file: Union[str, list[str]]):
    return pil2file(url2pil(source), target_file=target_file)


def check_str_type(source: str):
    # 大于1024字节的优先考虑base64编码
    if len(source) > 1024:
        return 'base64'
    else:
        if source.startswith('http') or source.startswith('https'):
            return 'url'
        elif "." in source or "_" in source or "-" in source:
            return 'file'
        elif source.startswith('data:image'):
            return 'base64'
        elif len(source) % 4 == 0:
            try:
                base642bytes(source)
                return 'base64'
            except:
                return 'file'
        else:
            return 'file'


def check_source_type(source):
    if isinstance(source, torch.Tensor):
        return 'tensor'
    elif isinstance(source, np.ndarray):
        return 'numpy'
    elif isinstance(source, bytes):
        return 'bytes'
    elif isinstance(source, str):
        return check_str_type(source)
    elif isinstance(source, Image.Image):
        return 'pil'
    elif isinstance(source, list):
        return check_source_type(source[0])


def to_file(source, target_file: Union[str, list[str]]):
    source_type = check_source_type(source)
    func_name = f"{source_type}2file"

    # 从当前模块中获取函数
    current_module = sys.modules[__name__]
    handler = getattr(current_module, func_name, None)
    if handler is None:
        raise NotImplementedError(f"No handler found for source type: {source_type}")
    return handler(source=source, target_file=target_file)


def to_base64(source, target_image_format: Union[ImageFormat, str] = None, target_data_url: bool = False):
    source_type = check_source_type(source)
    func_name = f"{source_type}2base64"

    # 从当前模块中获取函数
    current_module = sys.modules[__name__]
    handler = getattr(current_module, func_name, None)
    if handler is None:
        raise NotImplementedError(f"No handler found for source type: {source_type}")
    return handler(source=source, target_image_format=target_image_format, target_data_url=target_data_url)


def to_bytes(source, target_image_format: Union[ImageFormat, str] = None):
    source_type = check_source_type(source)
    func_name = f"{source_type}2bytes"

    # 从当前模块中获取函数
    current_module = sys.modules[__name__]
    handler = getattr(current_module, func_name, None)
    if handler is None:
        raise NotImplementedError(f"No handler found for source type: {source_type}")
    return handler(source=source, target_image_format=target_image_format)


def to_pil(source, target_color_mode: Union[ColorOrder, str] = None):
    source_type = check_source_type(source)
    func_name = f"{source_type}2pil"

    # 从当前模块中获取函数
    current_module = sys.modules[__name__]
    handler = getattr(current_module, func_name, None)
    if handler is None:
        raise NotImplementedError(f"No handler found for source type: {source_type}")
    return handler(source=source, target_color_mode=target_color_mode)


def to_numpy(source,
             target_dim_order: Union[DimOrder, str] = None,
             target_color_order: Union[ColorOrder, str] = None,
             target_normalized: bool = None,
             target_normalized_mean: Union[list[float], tuple[float], np.ndarray] = None,
             target_normalized_std: Union[list[float], tuple[float], np.ndarray] = None):
    source_type = check_source_type(source)
    func_name = f"{source_type}2numpy"

    # 从当前模块中获取函数
    current_module = sys.modules[__name__]
    handler = getattr(current_module, func_name, None)
    if handler is None:
        raise NotImplementedError(f"No handler found for source type: {source_type}")
    return handler(source=source, target_dim_order=target_dim_order, target_color_order=target_color_order,
                   target_normalized=target_normalized, target_normalized_mean=target_normalized_mean,
                   target_normalized_std=target_normalized_std)


def to_tensor(source,
              target_dim_order: Union[DimOrder, str] = None,
              target_color_order: Union[ColorOrder, str] = None,
              target_normalized: bool = None,
              target_normalized_mean: Union[list[float], tuple[float], np.ndarray, torch.Tensor] = None,
              target_normalized_std: Union[list[float], tuple[float], np.ndarray, torch.Tensor] = None,
              target_device: Union[str, torch.device] = None):
    source_type = check_source_type(source)
    func_name = f"{source_type}2tensor"

    # 从当前模块中获取函数
    current_module = sys.modules[__name__]
    handler = getattr(current_module, func_name, None)
    if handler is None:
        raise NotImplementedError(f"No handler found for source type: {source_type}")
    return handler(source=source, target_dim_order=target_dim_order, target_color_order=target_color_order,
                   target_normalized=target_normalized, target_normalized_mean=target_normalized_mean,
                   target_normalized_std=target_normalized_std, target_device=target_device)


def _test_tensor2tensor(image_kw_pairs, gray=False):
    import logging

    # 可选：配置 logging（如果尚未配置）
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    for source_dict, target_dict in image_kw_pairs:
        source_kws = {
            "source": source_dict["image"],
            'source_dim_order': source_dict["dim_order"],
            'source_color_order': source_dict["color_order"],
            'source_normalized': source_dict["normalized"],
            'source_normalized_mean': source_dict["normalized_mean"],
            'source_normalized_std': source_dict["normalized_std"]
        }
        target_kws = {
            'target_dim_order': target_dict["dim_order"],
            'target_color_order': target_dict["color_order"],
            'target_normalized': target_dict["normalized"],
            'target_normalized_mean': target_dict["normalized_mean"],
            'target_normalized_std': target_dict["normalized_std"]
        }

        if not gray:
            if source_dict["color_order"] == 'gray' and target_dict["color_order"] != 'gray':
                continue
            if source_dict["color_order"] == 'gray' and target_dict["color_order"] == 'gray' and target_dict[
                'normalized']:
                continue
            # 执行转换和比较
        result = tensor2tensor(**source_kws, **target_kws)
        if result.dtype == torch.uint8:
            is_equal = all(abs((target_dict['image'] - result).reshape(-1)) <= 1)
        else:
            is_equal = all((target_dict['image'] - result).reshape(-1) < 1e-3)

        args_log_str = (f"{source_dict['dim_order']} {source_dict['color_order']} {source_dict['normalized']} "
                        f"{source_dict['normalized_mean']} {source_dict['normalized_std']} -> "
                        f"{target_dict['dim_order']} {target_dict['color_order']} {target_dict['normalized']} "
                        f"{target_dict['normalized_mean']} {target_dict['normalized_std']}")
        if is_equal:
            logger.info(f"✅ tensor2tensor 转换结果与目标图像一致，验证通过！{args_log_str}")
        else:
            logger.error(f"❌ tensor2tensor 转换结果与目标图像不一致！     {args_log_str}")
            result = tensor2tensor(**source_kws, **target_kws)
        # 仍然保留 assert 用于测试中断
        assert is_equal, "tensor2tensor 输出与预期 target_dict['image'] 不匹配"


def _test_numpy2numpy(image_kw_pairs, gray=False):
    import logging

    # 可选：配置 logging（如果尚未配置）
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    for source_dict, target_dict in image_kw_pairs:
        source_kws = {
            "source": source_dict["image"].numpy(),
            'source_dim_order': source_dict["dim_order"],
            'source_color_order': source_dict["color_order"],
            'source_normalized': source_dict["normalized"],
            'source_normalized_mean': source_dict["normalized_mean"],
            'source_normalized_std': source_dict["normalized_std"]
        }
        target_kws = {
            'target_dim_order': target_dict["dim_order"],
            'target_color_order': target_dict["color_order"],
            'target_normalized': target_dict["normalized"],
            'target_normalized_mean': target_dict["normalized_mean"],
            'target_normalized_std': target_dict["normalized_std"]
        }

        if not gray:
            if source_dict["color_order"] == 'gray' and target_dict["color_order"] != 'gray':
                continue
            if source_dict["color_order"] == 'gray' and target_dict["color_order"] == 'gray' and target_dict[
                'normalized']:
                continue
        # 执行转换和比较
        result = numpy2numpy(**source_kws, **target_kws)
        if result.dtype == np.uint8:
            is_equal = all(abs((target_dict['image'].numpy() - result).reshape(-1)) <= 1)
        else:
            is_equal = all((target_dict['image'].numpy() - result).reshape(-1) < 1e-3)

        args_log_str = (f"{source_dict['dim_order']} {source_dict['color_order']} {source_dict['normalized']} "
                        f"{source_dict['normalized_mean']} {source_dict['normalized_std']} -> "
                        f"{target_dict['dim_order']} {target_dict['color_order']} {target_dict['normalized']} "
                        f"{target_dict['normalized_mean']} {target_dict['normalized_std']}")
        if is_equal:
            logger.info(f"✅ numpy2numpy 转换结果与目标图像一致，验证通过！{args_log_str}")
        else:
            logger.error(f"❌ numpy2numpy 转换结果与目标图像不一致！     {args_log_str}")
            result = numpy2numpy(**source_kws, **target_kws)
        # 仍然保留 assert 用于测试中断
        assert is_equal, "numpy2numpy 输出与预期 target_dict['image'] 不匹配"


def _test_numpy2tensor(image_kw_pairs, gray=False):
    import logging

    # 可选：配置 logging（如果尚未配置）
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    for source_dict, target_dict in image_kw_pairs:
        source_kws = {
            "source": source_dict["image"].numpy(),
            'source_dim_order': source_dict["dim_order"],
            'source_color_order': source_dict["color_order"],
            'source_normalized': source_dict["normalized"],
            'source_normalized_mean': source_dict["normalized_mean"],
            'source_normalized_std': source_dict["normalized_std"]
        }
        target_kws = {
            'target_dim_order': target_dict["dim_order"],
            'target_color_order': target_dict["color_order"],
            'target_normalized': target_dict["normalized"],
            'target_normalized_mean': target_dict["normalized_mean"],
            'target_normalized_std': target_dict["normalized_std"]
        }
        if not gray:
            if source_dict["color_order"] == 'gray' and target_dict["color_order"] != 'gray':
                continue
            if source_dict["color_order"] == 'gray' and target_dict["color_order"] == 'gray' and target_dict[
                'normalized']:
                continue
        # 执行转换和比较
        result = numpy2tensor(**source_kws, **target_kws)
        result = result.cpu().numpy()
        if result.dtype == np.uint8:
            is_equal = all(abs((target_dict['image'] - result).reshape(-1)) <= 1)
        else:
            is_equal = all((target_dict['image'] - result).reshape(-1) < 1e-3)

        args_log_str = (f"{source_dict['dim_order']} {source_dict['color_order']} {source_dict['normalized']} "
                        f"{source_dict['normalized_mean']} {source_dict['normalized_std']} -> "
                        f"{target_dict['dim_order']} {target_dict['color_order']} {target_dict['normalized']} "
                        f"{target_dict['normalized_mean']} {target_dict['normalized_std']}")
        if is_equal:
            logger.info(f"✅ numpy2tensor 转换结果与目标图像一致，验证通过！{args_log_str}")
        else:
            logger.error(f"❌ numpy2tensor 转换结果与目标图像不一致！     {args_log_str}")
            result = numpy2tensor(**source_kws, **target_kws)
        # 仍然保留 assert 用于测试中断
        assert is_equal, "numpy2tensor 输出与预期 target_dict['image'] 不匹配"


def _test_tensor2numpy(image_kw_pairs, gray=False):
    import logging

    # 可选：配置 logging（如果尚未配置）
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    for source_dict, target_dict in image_kw_pairs:
        source_kws = {
            "source": source_dict["image"],
            'source_dim_order': source_dict["dim_order"],
            'source_color_order': source_dict["color_order"],
            'source_normalized': source_dict["normalized"],
            'source_normalized_mean': source_dict["normalized_mean"],
            'source_normalized_std': source_dict["normalized_std"]
        }
        target_kws = {
            'target_dim_order': target_dict["dim_order"],
            'target_color_order': target_dict["color_order"],
            'target_normalized': target_dict["normalized"],
            'target_normalized_mean': target_dict["normalized_mean"],
            'target_normalized_std': target_dict["normalized_std"]
        }
        if not gray:
            if source_dict["color_order"] == 'gray' and target_dict["color_order"] != 'gray':
                continue
            if source_dict["color_order"] == 'gray' and target_dict["color_order"] == 'gray' and target_dict[
                'normalized']:
                continue
        # 执行转换和比较
        result = tensor2numpy(**source_kws, **target_kws)
        if result.dtype == np.uint8:
            is_equal = all(abs((target_dict['image'].numpy() - result).reshape(-1)) <= 1)
        else:
            is_equal = all((target_dict['image'].numpy() - result).reshape(-1) < 1e-3)

        args_log_str = (f"{source_dict['dim_order']} {source_dict['color_order']} {source_dict['normalized']} "
                        f"{source_dict['normalized_mean']} {source_dict['normalized_std']} -> "
                        f"{target_dict['dim_order']} {target_dict['color_order']} {target_dict['normalized']} "
                        f"{target_dict['normalized_mean']} {target_dict['normalized_std']}")
        if is_equal:
            logger.info(f"✅ tensor2numpy 转换结果与目标图像一致，验证通过！{args_log_str}")
        else:
            logger.error(f"❌ tensor2numpy 转换结果与目标图像不一致！     {args_log_str}")
            result = tensor2numpy(**source_kws, **target_kws)
        # 仍然保留 assert 用于测试中断
        assert is_equal, "tensor2numpy 输出与预期 target_dict['image'] 不匹配"


def _get_tensor_data(gray=False):
    aaaaa_mean_rgb = mean_rgb = torch.tensor([0, 0.5, 1])
    aaaaa_std_rgb = std_rgb = torch.tensor([0.1, 0.2, 0.3])
    aaaaa_mean_bgr = mean_bgr = mean_rgb[[2, 1, 0]]
    aaaaa_std_bgr = std_bgr = std_rgb[[2, 1, 0]]
    aaaaa_mean_rgba = mean_rgba = torch.cat([mean_rgb, torch.tensor([1.0], dtype=mean_rgb.dtype)])
    aaaaa_std_rgba = std_rgba = torch.cat([std_rgb, torch.tensor([1e-9], dtype=std_rgb.dtype)])
    aaaaa_mean_bgra = mean_bgra = torch.cat([mean_bgr, torch.tensor([1.0], dtype=mean_rgb.dtype)])
    aaaaa_std_bgra = std_bgra = torch.cat([std_bgr, torch.tensor([1e-9], dtype=std_rgb.dtype)])
    aaaaa_mean_gray = mean_gray = gray_transform(mean_rgb.reshape(-1, 1, 1)).reshape(-1)
    aaaaa_std_gray = std_gray = gray_transform(std_rgb.reshape(-1, 1, 1)).reshape(-1)

    mean_std_dict = {key.replace('aaaaa_', ''): value for key, value in locals().items() if key.startswith('aaaaa_')}

    cacle_mean_std_dict = {}

    for key, value in mean_std_dict.items():
        cacle_mean_std_dict[f"{key}_chw"] = value.reshape(-1, 1, 1)
        cacle_mean_std_dict[f"{key}_hwc"] = value.reshape(1, 1, -1)
        cacle_mean_std_dict[f"{key}_bchw"] = value.reshape(1, -1, 1, 1)
        cacle_mean_std_dict[f"{key}_bhwc"] = value.reshape(1, 1, 1, -1)

    if gray:

        bbbbb_rgb = torch.tensor([[[16, 76, 16, 76],
                                   [136, 196, 136, 196]],

                                  [[16, 76, 16, 76],
                                   [136, 196, 136, 196]],

                                  [[16, 76, 16, 76],
                                   [136, 196, 136, 196]]]).float()
    else:
        bbbbb_rgb = torch.tensor([[[0, 0, 0, 0],
                                   [125, 125, 125, 125]],

                                  [[0, 0, 0, 0],
                                   [11, 11, 11, 11]],

                                  [[16, 76, 16, 76],
                                   [136, 196, 136, 196]]]).float()
    bbbbb_rgba = torch.cat([bbbbb_rgb, torch.full_like(bbbbb_rgb[:1], 255, dtype=bbbbb_rgb.dtype)],
                           dim=0)
    bbbbb_bgr = bbbbb_rgb[[2, 1, 0], :, :]
    bbbbb_bgra = bbbbb_rgba[[2, 1, 0, 3], :, :]
    bbbbb_gray = gray_transform(bbbbb_rgb)

    image_dict = {}
    for key, value in locals().items():
        if key.startswith('bbbbb_'):
            key = key.replace('bbbbb_', '')
            image_dict[f"{key}_chw_n0_nz0"] = value
            image_dict[f"{key}_bchw_n0_nz0"] = value.unsqueeze(0)
            image_dict[f"{key}_hwc_n0_nz0"] = value.permute(1, 2, 0)
            image_dict[f"{key}_bhwc_n0_nz0"] = value.permute(1, 2, 0).unsqueeze(0)

    for key, value in list(image_dict.items()):
        color_order, dim_order, n, nz = key.split('_')
        image_dict[f"{color_order}_{dim_order}_n1_nz0"] = value.float() / 255
        image_dict[f"{color_order}_{dim_order}_n1_nz1"] = \
            (value.float() / 255 - cacle_mean_std_dict[f"mean_{color_order}_{dim_order}"]) / \
            cacle_mean_std_dict[f"std_{color_order}_{dim_order}"]

    for key, value in list(image_dict.items()):
        color, dim, n, nz = key.split('_')
        if n == "n0":
            image_dict[key] = value.round().byte()

    image_kwargs = []
    image_search_dict = {}
    for key, value in list(image_dict.items()):
        color_order, dim_order, n, nz = key_names = key.split('_')
        color_order, dim_order = key_names[0], key_names[1]

        normalized = n == "n1"
        normalized_mean = None
        normalized_std = None
        if nz == "nz1":
            normalized_mean = mean_std_dict[f"mean_{color_order}"].numpy()
            normalized_std = mean_std_dict[f"std_{color_order}"].numpy()
        image_kwargs.append({
            'image': value,
            'dim_order': dim_order,
            'color_order': color_order,
            'normalized': normalized,
            'normalized_mean': normalized_mean,
            'normalized_std': normalized_std
        })
        image_search_dict[f"{dim_order}_{color_order}_{str(normalized)}_{str(normalized_mean != None)}"] = value
    from itertools import permutations
    pairs = list(permutations(image_kwargs, 2))
    return pairs, gray


def _test_numpy_pil():
    image = numpy.asarray([[[0, 0, 0, 0],
                            [125, 125, 125, 125]],

                           [[0, 0, 0, 0],
                            [11, 11, 11, 11]],

                           [[16, 76, 16, 76],
                            [136, 196, 136, 196]]]).astype(np.uint8)
    image = np.transpose(image, (1, 2, 0))

    image_outs = []
    for color in ['rgb', 'bgr', 'rgba', 'bgra', 'gray']:
        mean = std = None
        if color == 'rgb':
            mean = np.array([0, 0.5, 1])
            std = np.array([0.1, 0.2, 0.3])
        if color == 'bgr':
            mean = np.array([1, 0.5, 0])
            std = np.array([0.3, 0.2, 0.1])
        if color == 'rgba':
            mean = np.array([0, 0.5, 1, 1])
            std = np.array([0.1, 0.2, 0.3, 1e-9])
        if color == 'bgra':
            mean = np.array([1, 0.5, 0, 1])
            std = np.array([0.3, 0.2, 0.1, 1e-9])
        if color in ['gray']:
            mean = np.array([0.5])
            std = np.array([0.1])
        for dim in ['chw', 'hwc', 'bchw', 'bhwc']:
            for n, nz in [('n0', 'nz0'), ('n1', 'nz0'), ('n1', 'nz1')]:
                for pil_color_model in ['rgb', 'rgba']:
                    key = f"{dim}_{color}_{n}_{nz}_{pil_color_model}"
                    source = numpy2numpy(image,
                                         target_dim_order=dim,
                                         target_color_order=color,
                                         target_normalized=n == 'n1',
                                         target_normalized_mean=None if nz == 'nz0' else mean,
                                         target_normalized_std=None if nz == 'nz0' else std,
                                         )
                    pil_img = numpy2pil(source=source,
                                        source_color_order=color,
                                        source_dim_order=dim,
                                        source_normalized=n == 'n1',
                                        source_normalized_mean=None if nz == 'nz0' else mean,
                                        source_normalized_std=None if nz == 'nz0' else std,
                                        target_color_mode=pil_color_model)
                    image_outs.append((f"{dim}_{color}_{n}_{nz}_{pil_color_model}", pil2numpy(pil_img)))
                    pil2file(pil_img, f"imgs/{color}_{dim}_{n}_{nz}_{pil_color_model}.png")
    print(image_outs)


def _test_tensor_pil():
    image = torch.tensor([[[0, 0, 0, 0],
                           [125, 125, 125, 125]],

                          [[0, 0, 0, 0],
                           [11, 11, 11, 11]],

                          [[16, 76, 16, 76],
                           [136, 196, 136, 196]]]).byte()
    image = image[[2, 1, 0], :, :]
    # image = np.transpose(image, (1, 2, 0))

    image_outs = []
    for color in ['rgb', 'bgr', 'rgba', 'bgra', 'gray']:
        mean = std = None
        if color == 'rgb':
            mean = np.array([0, 0.5, 1])
            std = np.array([0.1, 0.2, 0.3])
        if color == 'bgr':
            mean = np.array([1, 0.5, 0])
            std = np.array([0.3, 0.2, 0.1])
        if color == 'rgba':
            mean = np.array([0, 0.5, 1, 1])
            std = np.array([0.1, 0.2, 0.3, 1e-9])
        if color == 'bgra':
            mean = np.array([1, 0.5, 0, 1])
            std = np.array([0.3, 0.2, 0.1, 1e-9])
        if color in ['gray']:
            mean = np.array([0.5])
            std = np.array([0.1])
        for dim in ['chw', 'hwc', 'bchw', 'bhwc']:
            for n, nz in [('n0', 'nz0'), ('n1', 'nz0'), ('n1', 'nz1')]:
                for pil_color_model in ['rgb', 'rgba']:
                    key = f"{dim}_{color}_{n}_{nz}_{pil_color_model}"
                    source = tensor2tensor(image,
                                           target_dim_order=dim,
                                           target_color_order=color,
                                           target_normalized=n == 'n1',
                                           target_normalized_mean=None if nz == 'nz0' else mean,
                                           target_normalized_std=None if nz == 'nz0' else std,
                                           )
                    pil_img = tensor2pil(source=source,
                                         source_color_order=color,
                                         source_dim_order=dim,
                                         source_normalized=n == 'n1',
                                         source_normalized_mean=None if nz == 'nz0' else mean,
                                         source_normalized_std=None if nz == 'nz0' else std,
                                         target_color_mode=pil_color_model)
                    image_outs.append((f"{dim}_{color}_{n}_{nz}_{pil_color_model}", pil2tensor(pil_img)))
                    pil2file(pil_img, f"imgs/{color}_{dim}_{n}_{nz}_{pil_color_model}.png")
    print(image_outs)


def _base_test():
    tensor_image = file2tensor(r'C:\Users\Administrator\Desktop\1.jpg',
                               target_normalized_mean=ImageNet_mean, target_normalized_std=ImageNet_std)
    numpy_image = tensor2numpy(tensor_image, source_normalized_mean=ImageNet_mean, source_normalized_std=ImageNet_std)
    cv2.imwrite(r'1.jpg', numpy_image)
    print(numpy_image)


if __name__ == '__main__':
    # _test_tensor2tensor(*_get_tensor_data(gray=False))
    # _test_tensor2tensor(*_get_tensor_data(gray=True))
    #
    # _test_numpy2numpy(*_get_tensor_data(gray=False))
    # _test_numpy2numpy(*_get_tensor_data(gray=True))
    #
    # _test_numpy2tensor(*_get_tensor_data(gray=False))
    # _test_numpy2tensor(*_get_tensor_data(gray=True))
    #
    # _test_tensor2numpy(*_get_tensor_data(gray=False))
    # _test_tensor2numpy(*_get_tensor_data(gray=True))

    # _test_numpy_pil()
    # _test_tensor_pil()
    _base_test()
