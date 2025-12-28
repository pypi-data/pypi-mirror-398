import time
import os
import cv2
import threading
import numpy
from ultralytics import YOLO
try:
    from .pooled_gpu_model import PooledModelManager, PooledModel, ModelProvider
except:
    from pooled_gpu_model import PooledModelManager, PooledModel, ModelProvider

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
    def map_coordinates_batch(xyxy_tensor):
        if xyxy_tensor.ndim != 2 or xyxy_tensor.shape[1] != 4:
            raise ValueError("输入必须是形状为 (N, 4) 的张量，表示 xyxy 边界框。")

        # 反向映射
        x1_original = (xyxy_tensor[:, 0] - pad_w) / ratio
        y1_original = (xyxy_tensor[:, 1] - pad_h) / ratio
        x2_original = (xyxy_tensor[:, 2] - pad_w) / ratio
        y2_original = (xyxy_tensor[:, 3] - pad_h) / ratio

        # 限制在原始图像范围内
        x1_original = torch.clamp(x1_original, 0, w)
        y1_original = torch.clamp(y1_original, 0, h)
        x2_original = torch.clamp(x2_original, 0, w)
        y2_original = torch.clamp(y2_original, 0, h)

        return torch.stack([x1_original, y1_original, x2_original, y2_original], dim=1)

    return padded_tensor, map_coordinates_batch


def preprocess_image_with_mapping_dynamic(tensor, max_size, fill_value):
    _, _, h, w = tensor.shape
    original_max_side = max(h, w)
    ratio = max_size / original_max_side

    # 计算长边缩放后的尺寸（确保是32的倍数且不超过max_size）
    new_max_side = (max_size // 32) * 32  # 向下取整到最近的32的倍数
    new_max_side = max(new_max_side, 32)  # 确保最小为32

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
    padded_h = ((new_h + 31) // 32) * 32
    padded_w = ((new_w + 31) // 32) * 32

    pad_h = (padded_h - new_h) // 2
    pad_w = (padded_w - new_w) // 2

    padded_tensor = torch.full(
        (1, 3, padded_h, padded_w),
        fill_value=fill_value,
        dtype=tensor.dtype,
        device=tensor.device
    )
    padded_tensor[:, :, pad_h:pad_h + new_h, pad_w:pad_w + new_w] = resized_tensor

    # 坐标映射函数
    def map_coordinates_batch(xyxy_tensor):
        if xyxy_tensor.ndim != 2 or xyxy_tensor.shape[1] != 4:
            raise ValueError("输入必须是形状为 (N, 4) 的张量，表示 xyxy 边界框。")

        # 坐标转换公式（逆操作）
        x1_original = (xyxy_tensor[:, 0] - pad_w) / ratio
        y1_original = (xyxy_tensor[:, 1] - pad_h) / ratio
        x2_original = (xyxy_tensor[:, 2] - pad_w) / ratio
        y2_original = (xyxy_tensor[:, 3] - pad_h) / ratio

        # 裁剪到原图有效范围
        x1_original = torch.clamp(x1_original, 0, w)
        y1_original = torch.clamp(y1_original, 0, h)
        x2_original = torch.clamp(x2_original, 0, w)
        y2_original = torch.clamp(y2_original, 0, h)

        return torch.stack([x1_original, y1_original, x2_original, y2_original], dim=1)

    return padded_tensor, map_coordinates_batch


from torchvision.transforms import transforms


class YOLOPooledModel(PooledModel):

    def __init__(self, model, gpu_id, image_size, model_dynamic=False):
        super().__init__(gpu_id)
        self.model = model
        self.image_size = image_size
        self.model_type = os.path.splitext(self.model.model_name)[1][1:]
        self.to_tensor = transforms.ToTensor()
        self.classify_crop = transforms.Compose([
            transforms.Resize((image_size, image_size)),
            transforms.CenterCrop(image_size),
            # transforms.Normalize(mean=[0.5], std=[0.229, 0.224, 0.225])
        ])
        self.preprocess_func = preprocess_image_with_mapping_dynamic if model_dynamic else preprocess_image_with_mapping_static
        self.device = torch.device(int(gpu_id) if int(gpu_id) >= 0 else torch.device('cpu'))

    @staticmethod
    def postprocess(data, letterbox):
        ratio = letterbox['ratio']
        left, right = letterbox['left'], letterbox['right']
        top, bottom = letterbox['top'], letterbox['bottom']
        data[:, 0] = data[:, 0] / ratio[1] - left / ratio[1]
        data[:, 1] = data[:, 1] / ratio[0] - top / ratio[0]
        data[:, 2] = data[:, 2] / ratio[1] - left / ratio[1]
        data[:, 3] = data[:, 3] / ratio[0] - top / ratio[0]

        return data

    def tensor_image_pre(self, img_tensor):
        if img_tensor.device != self.device:
            img_tensor = img_tensor.to(self.device)
        return img_tensor - 0.0000003

    def predict(self, image, **kwargs):
        torch.cuda.synchronize(self.device)
        if (self.model_type == 'pt' or self.model_type == 'onnx') and isinstance(image, numpy.ndarray):
            result = self.model.predict(image, **kwargs)
            return result
        elif (self.model_type == 'pt' or self.model_type == 'onnx') and isinstance(image, torch.Tensor):
            if self.model.task == 'detect':
                image_, map_batch = self.preprocess_func(image.unsqueeze(0), max_size=self.image_size,
                                                         fill_value=0.4471)
                result = self.model.predict(self.tensor_image_pre(image_), **kwargs)
                for r in result:
                    new_data = r.boxes.data.clone()
                    new_data[:, :4] = map_batch(new_data[:, :4])
                    r.boxes.data = new_data
            elif self.model.task == 'classify':
                image_ = self.tensor_image_pre(self.classify_crop(image)).unsqueeze(0)
                # result = self.model.predict(image_[:, [2, 1, 0], :, :] - 0.0000003, **kwargs)
                result = self.model.predict(image_, **kwargs)
            else:
                raise NotImplementedError
            return result
        elif self.model_type == 'engine':
            with torch.cuda.stream(torch.cuda.Stream(device=self.device)):
                if isinstance(image, numpy.ndarray):
                    image = self.tensor_image_pre(self.to_tensor(image))[[2, 1, 0], :, :]
                if self.model.task == 'detect':
                    kwargs['imgsz'] = self.image_size
                    if len(image.shape) == 4:
                        result = self.model.predict(self.tensor_image_pre(image), **{**kwargs, 'device': self.device})
                    else:
                        image_, map_batch = self.preprocess_func(image.unsqueeze(0), max_size=self.image_size,
                                                                 fill_value=0.4471)
                        result = self.model.predict(self.tensor_image_pre(image_), **{**kwargs, 'device': self.device})
                        for r in result:
                            new_data = r.boxes.data.clone()
                            new_data[:, :4] = map_batch(new_data[:, :4])
                            r.boxes.data = new_data
                elif self.model.task == 'classify':
                    image_ = self.tensor_image_pre(self.classify_crop(image)).unsqueeze(0)
                    result = self.model.predict(self.tensor_image_pre(image_),
                                                **{**{"imgsz": self.image_size}, **kwargs})
                else:
                    raise NotImplementedError
                torch.cuda.synchronize(self.device)
            return result


class YOLOPooledModelProvider(ModelProvider):
    def __init__(self, model_path, warm_up_image=None, image_size=None, task='detect', model_dynamic=False):
        self.model_path = model_path
        self.image_size = image_size
        self.warm_up_image = warm_up_image
        self.task = task
        self.model_dynamic = model_dynamic

    def create_model(self, gpu_id) -> PooledModel:
        from ultralytics import YOLO
        yolo = YOLO(self.model_path, task=self.task)
        try:
            yolo.to(device=torch.device(f'cuda:{gpu_id}'))
        except:
            pass
        return YOLOPooledModel(yolo, gpu_id=gpu_id, image_size=self.image_size or yolo.overrides.get('imgsz', 640),
                               model_dynamic=self.model_dynamic)

    def warm_up(self, model):
        if self.warm_up_image is None:
            return
        warm_up_data = cv2.imread(self.warm_up_image)
        model.predict(warm_up_data, verbose=False)


def get_gpu_model():
    import subprocess
    result = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'], stdout=subprocess.PIPE)
    return result.stdout.decode('utf-8').strip().split('\n')[0]


def tensorrt_version():
    import tensorrt as trt
    return f'{trt.__version__}'


def yolo_predictor(weight_path, model_name=None, model_image_size=None, task_name=None, devices=None,
                   model_dynamic=True, predict_kwargs=None):
    if devices is None:
        devices = '0' if torch.cuda.is_available() else 'cpu'

    if model_name is None:
        if weight_path.endswith('.pt'):
            model_path_torch = model_path = weight_path
        elif weight_path.endswith('.pth'):
            model_path_torch = model_path = weight_path
        elif weight_path.endswith('.engine'):
            model_path = weight_path
            model_path_torch = None
        else:
            raise Exception('model_name must be set')

    else:
        model_path_pt = os.path.join(weight_path, f"{model_name}.pt")
        model_path_pth = os.path.join(weight_path, f"{model_name}.pth")
        model_path_torch = None

        if os.path.exists(model_path_pt):
            model_path_torch = model_path_pt
        elif os.path.exists(model_path_pth):
            model_path_torch = model_path_pth

        model_path_engine = os.path.join(weight_path, tensorrt_version(), get_gpu_model(), f'{model_name}.engine')

        if os.path.exists(model_path_engine):
            model_path = model_path_engine
        elif model_path_torch:
            model_path = model_path_torch
        else:
            raise Exception(f'{model_name} model not found')
    torch_cpu_model = None
    if model_path_torch:
        torch_cpu_model = YOLO(model_path_torch)
        task_name = torch_cpu_model.overrides.get("task", task_name)
        model_image_size = torch_cpu_model.overrides.get("imgsz", model_image_size)

    if task_name is None or model_image_size is None:
        raise Exception('task_name and model_image_size must be set')

    if predict_kwargs is None:
        predict_kwargs = {}

    devices = devices.split(',')
    warmup_img_path = os.path.join(weight_path, 'warm-up.jpg')
    if not os.path.exists(warmup_img_path):
        warmup_img_path = None

    if 'cpu' in devices:
        model = torch_cpu_model if torch_cpu_model is not None else YOLO(model_path_torch)
        if warmup_img_path:
            _ = model.predict(warmup_img_path, imgsz=model_image_size, save_txt=False, verbose=False)
        return lambda *args, **kwargs: model.predict(*args, **predict_kwargs, **kwargs)
    else:

        model_pool = PooledModelManager(
            model_provider=YOLOPooledModelProvider(model_path=model_path, task=task_name,
                                                   warm_up_image=warmup_img_path,
                                                   image_size=model_image_size,
                                                   model_dynamic=model_dynamic),
            deploy_shape=[(d, 1) for d in devices])

        def predict(*args, **kwargs):
            with model_pool.get_model() as model:
                results = model(*args, **predict_kwargs, **kwargs)
                return results

        return predict


if __name__ == '__main__':
    import cv2

    # model_path_ = '/data/wdxdev/projects/aigc-sportEvent-recognition/live-stream-ai/modules/wtt-highlight/weights/ball241216.pt'
    model_path_ = '/data/wdxdev/projects/aigc-sportEvent-recognition/live-stream-ai/modules/wtt-highlight/weights/10.1.0/Tesla V100-PCIE-32GB/others241213nano.engine'
    image_path = '/data/wdxdev/projects/aigc-sportEvent-recognition/live-stream-ai/test/wtt_test.png'
    warm_up = '/data/wdxdev/projects/aigc-sportEvent-recognition/live-stream-ai/modules/wtt-highlight/weights/warm-up.jpg'
    image = cv2.imread(image_path)

    pool_manger = PooledModelManager(
        model_provider=YOLOPooledModelProvider(model_path=model_path_, warm_up_image=warm_up, image_size=1088),
        deploy_shape=[(1, 1)])


    def trr():
        for _ in range(500):
            with pool_manger.get_model() as pooled_model_:
                pooled_model_(image)


    st = time.time()
    t1 = threading.Thread(target=trr)
    t1.start()

    t2 = threading.Thread(target=trr)
    t2.start()

    t1.join()
    t2.join()

    # t3 = threading.Thread(target=trr)
    # t3.start()
    # t3.join()
    print(f"use time:{time.time() - st}s")
