import torch
import torchvision.transforms.functional as F


def preprocess_image_with_mapping_static(tensor, max_size, fill_value):
    _, _, h, w = tensor.shape
    original_max_side = max(h, w)
    ratio = max_size / original_max_side

    # 根据长边决定缩放后的尺寸
    if w >= h:  # 宽为长边
        new_w = max_size
        new_h = int(round(h * ratio))
    else:  # 高为长边
        new_h = max_size
        new_w = int(round(w * ratio))

    # 缩放图像
    resized_tensor = F.resize(tensor, [new_h, new_w])

    # 计算填充量以居中
    pad_h = (max_size - new_h) // 2
    pad_w = (max_size - new_w) // 2

    # 构建填充后的图像张量
    padded_tensor = torch.full(
        (1, 3, max_size, max_size),
        fill_value=fill_value,
        dtype=tensor.dtype,
        device=tensor.device
    )
    padded_tensor[:, :, pad_h:pad_h + new_h, pad_w:pad_w + new_w] = resized_tensor

    # 定义坐标映射函数，用于将检测框坐标还原到原始图像
    def map_coordinates_batch(tensor_data):
        result_tensor = tensor_data.clone()
        points = result_tensor.reshape(-1, 2)
        points[:, 0] = torch.clamp((points[:, 0] - pad_w) / ratio, 0, w)
        points[:, 1] = torch.clamp((points[:, 1] - pad_h) / ratio, 0, h)
        return result_tensor.reshape(tensor_data.shape)

    return padded_tensor, map_coordinates_batch


def preprocess_image_with_mapping_dynamic(tensor, max_size, fill_value=0.0, stride=32):
    _, _, h, w = tensor.shape
    original_max_side = max(h, w)
    ratio = max_size / original_max_side

    # 计算长边缩放后的尺寸（确保是32的倍数且不超过max_size）
    new_max_side = (max_size // stride) * stride  # 向下取整到最近的32的倍数
    new_max_side = max(new_max_side, stride)  # 确保最小为32

    # 确定长边方向并计算新的宽高
    if w >= h:  # 宽是长边
        new_w = new_max_side
        new_h = int(round(h * ratio))
    else:  # 高是长边
        new_h = new_max_side
        new_w = int(round(w * ratio))

    # 确保缩放后的尺寸不超过max_size（可能因round导致轻微超过？）
    # 但new_max_side已确保不超过max_size，因此无需额外处理

    resized_tensor = F.resize(tensor, [new_h, new_w])

    # 填充到32的倍数
    padded_h = ((new_h + stride - 1) // stride) * stride
    padded_w = ((new_w + stride - 1) // stride) * stride

    pad_h = (padded_h - new_h) // 2
    pad_w = (padded_w - new_w) // 2

    padded_tensor = torch.full(
        (1, 3, padded_h, padded_w),
        fill_value=fill_value,
        dtype=tensor.dtype,
        device=tensor.device
    )
    padded_tensor[:, :, pad_h:pad_h + new_h, pad_w:pad_w + new_w] = resized_tensor

    # 定义坐标映射函数，用于将检测框坐标还原到原始图像
    def map_coordinates_batch(tensor_data):
        result_tensor = tensor_data.clone()
        points = result_tensor.reshape(-1, 2)
        points[:, 0] = torch.clamp((points[:, 0] - pad_w) / ratio, 0, w)
        points[:, 1] = torch.clamp((points[:, 1] - pad_h) / ratio, 0, h)
        return result_tensor.reshape(tensor_data.shape)

    return padded_tensor, map_coordinates_batch


if __name__ == '__main__':
    white_img = torch.ones(1, 3, 20, 60, dtype=torch.float32)
    p = torch.tensor([[[16, 16], [32, 32]], [[16, 32], [32, 32]], [[8, 8], [8, 8]]], dtype=torch.float32)
    p = torch.tensor([[16, 16, 32, 32], [16, 32, 32, 32], [5, 5, 8, 8]], dtype=torch.float32)
    padded_tensor, map_coordinates_batch = preprocess_image_with_mapping_dynamic(white_img, 64, 0)
    print(padded_tensor.shape)
    print(map_coordinates_batch(p))
