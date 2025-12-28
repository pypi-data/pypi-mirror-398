import queue
import time
import traceback
from abc import ABC, abstractmethod
import os
import threading
import numpy
import torch


class PooledModel(ABC):
    def __init__(self, gpu_id):
        self.gpu_id = gpu_id
        self.model_manager = None
        self.kwargs = {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self.model_manager.back_model(self)

    def __call__(self, *args, **kwargs):
        return self.predict(*args, **kwargs)

    @abstractmethod
    def predict(self, *args, **kwargs):
        return None


class ModelProvider(ABC):

    @abstractmethod
    def create_model(self, gpu_id) -> PooledModel:
        pass

    def destroy_model(self, model):
        pass

    def warm_up(self, model):
        pass


class PooledModelManager:
    def __init__(self, model_provider, deploy_shape=('all', 1)):
        import torch
        self.model_provider = model_provider
        if isinstance(deploy_shape, tuple):
            deploy_shape = [deploy_shape]
        self.deploy_shape = deploy_shape
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
        else:
            raise Exception("No GPU available")

        self.free_models = queue.Queue()
        self.used_models = []

        if any([x[0] == 'all' for x in self.deploy_shape]):
            _, model_number = [s for s in self.deploy_shape if s[0] == 'all'][-1]
            for gpu_id in range(gpu_count):
                pooled_model = self.model_provider.create_model(gpu_id)
                self.model_provider.warm_up(pooled_model)
                pooled_model.model_manager = self
                pooled_model.kwargs['last_thread_id'] = threading.current_thread().ident
                self.free_models.put(pooled_model)
        else:
            for gpu_id, model_number in self.deploy_shape:
                # if int(gpu_id) >= gpu_count:
                #     raise Exception("GPU id out of range")
                # else:
                for _ in range(model_number):
                    pooled_model = self.model_provider.create_model(gpu_id)
                    self.model_provider.warm_up(pooled_model)
                    pooled_model.model_manager = self
                    pooled_model.kwargs['last_thread_id'] = threading.current_thread().ident
                    pooled_model.kwargs['last_use_time'] = time.time()
                    self.free_models.put(pooled_model)

        self.opt_lock = threading.Lock()

    def get_model(self, timeout=30):
        with self.opt_lock:
            try:
                model = self.free_models.get(timeout=timeout)
                self.used_models.append(model)
                model.kwargs['last_thread_id'] = threading.current_thread().ident
                model.kwargs['last_use_time'] = time.time()
                return model
            except queue.Empty:
                raise Exception("Timeout")

    def back_model(self, model):
        self.free_models.put(model)
        self.used_models.remove(model)
        model.kwargs['last_use_time'] = time.time()
