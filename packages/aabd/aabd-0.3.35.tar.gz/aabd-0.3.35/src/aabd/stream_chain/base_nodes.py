import time
from abc import abstractmethod
from aabd.base.enhance_dict import value_or_default
import cv2
import torch
import numpy as np
import os
import json
from .chain_nodes import SingleInputNode, Message


class InitDrawImageNode(SingleInputNode):

    def __init__(self, params):
        enable = params.chain_debug
        super().__init__(enable=enable)

    def process(self, messages: list[Message]):
        data = messages[0].payload

        image = data.image
        if isinstance(image, torch.Tensor):
            image = image.mul(255).round().byte().permute(1, 2, 0).cpu().numpy()
        # else:
        #     image = image.copy().astype(np.uint8)
        data.image = image
        data.draw_image = image


class ImageShowNode(SingleInputNode):
    def __init__(self, params):
        enable = params.chain_debug
        super().__init__(enable=enable)

    def process(self, messages: list[Message]):
        data = messages[0].payload
        cv2.imshow('video', data.draw_image)
        cv2.waitKey(1)


class Image2VideoNode(SingleInputNode):

    def __init__(self, params):
        self.output_function = params.out_video_writer

        enable = params.chain_debug
        super().__init__(enable=enable)

    def process(self, messages: list[Message]):
        data = messages[0].payload
        self.output_function(data.draw_image)
        # cv2.imshow('tennis', data.image)
        # cv2.waitKey(1)


class RemoveImageNode(SingleInputNode):

    def __init__(self, params):
        enable = not params.chain_debug
        super().__init__(enable=enable)

    def process(self, messages: list[Message]):
        data = messages[0].payload
        data.image = None
        data.draw_image = None


class BaseCacheInferenceNode:
    def __init__(self, cache_name, params=None, **kwargs):
        model_info_cache_enable = value_or_default(params.model_info_cache_enable, False)
        model_info_cache_path = value_or_default(params.model_info_cache_path, None)
        if model_info_cache_enable and model_info_cache_path is not None:
            cache_dir = os.path.join(model_info_cache_path, params.task_id or 'default', cache_name)
        else:
            cache_dir = None

        if cache_dir:
            self.model_info_cache_enable = True
            self.model_info_cache_path = cache_dir
            os.makedirs(self.model_info_cache_path, exist_ok=True)
        else:
            self.model_info_cache_enable = False

        model_vis_file_enable = value_or_default(params.model_vis_file_enable, False)
        model_vis_file_path = value_or_default(params.model_vis_file_path, None)
        if model_vis_file_enable and model_vis_file_path is not None:
            cache_dir = os.path.join(model_vis_file_path, params.task_id or 'default', cache_name)
        else:
            cache_dir = None

        if cache_dir:
            self.model_vis_file_enable = True
            self.model_vis_file_path = cache_dir
            os.makedirs(self.model_vis_file_path, exist_ok=True)
        else:
            self.model_vis_file_enable = False
        super().__init__(**kwargs)

    def predict_with_cache(self, *args, **kwargs):
        cache_name = kwargs.get("cache_name", None)
        kwargs.pop("cache_name", None)
        if self.model_info_cache_enable and cache_name is not None:
            cache_file_json = os.path.join(self.model_info_cache_path, f'{cache_name}.json')
            if os.path.exists(cache_file_json):
                with open(cache_file_json, 'r') as f:
                    infer_data = self.to_predict_data(json.load(f))
            else:
                infer_data = self.predict(*args, **kwargs)
                with open(cache_file_json, 'w') as f:
                    json.dump(self.to_cache_data(infer_data), f, indent=4)
        else:
            infer_data = self.predict(*args, **kwargs)
        return infer_data

    def predict_with_opt(self, *args, **kwargs):
        use_times = {}
        start_time = last_time = time.time()
        cache_name = kwargs.get("cache_name", None)
        kwargs.pop("cache_name", None)

        vis_file_name = kwargs.get("vis_file_name", None)
        kwargs.pop("vis_file_name", None)

        if self.model_info_cache_enable and cache_name is not None:
            cache_file_json = os.path.join(self.model_info_cache_path, f'{cache_name}.json')
            if os.path.exists(cache_file_json):
                with open(cache_file_json, 'r') as f:
                    infer_data = self.to_predict_data(json.load(f))
                now_time = time.time()
                use_times["read_cache"] = now_time - last_time
                last_time = now_time

            else:
                infer_data = self.predict(*args, **kwargs)
                now_time = time.time()
                use_times["infer"] = now_time - last_time
                last_time = now_time
                with open(cache_file_json, 'w') as f:
                    json.dump(self.to_cache_data(infer_data), f, indent=4)
                now_time = time.time()
                use_times["write_cache"] = now_time - last_time
                last_time = now_time
        else:
            infer_data = self.predict(*args, **kwargs)
            now_time = time.time()
            use_times["infer"] = now_time - last_time
            last_time = now_time

        if vis_file_name is not None and self.model_vis_file_enable:

            self.save_vis_file(*args,
                               predict_result=infer_data,
                               save_vis_file_path=os.path.join(self.model_vis_file_path, vis_file_name),
                               **kwargs)
            now_time = time.time()
            use_times["save_vis_file"] = now_time - last_time
            last_time = now_time
        use_times["total"] = last_time - start_time
        return infer_data, use_times

    @abstractmethod
    def predict(self, *args, **kwargs):
        pass

    def to_cache_data(self, data) -> dict:
        return data

    def to_predict_data(self, data: dict):
        return data

    def save_vis_file(self, *args, predict_result, save_vis_file_path, **kwargs):
        pass