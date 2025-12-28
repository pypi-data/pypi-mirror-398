import torch
import json
import numpy as np
from typing import Union
from dataclasses import dataclass, field
from aabd.base.enhance_dict import EnhanceDict, value_or_default
from aabd.base.time_util import vms2str_auto
from .chain_nodes import MermaidNodesChain, Message, SingleInputNode
from .chain_executor import VideoFrameQueueDataStream, ChainExecutor, VideoFrameDataStream
import logging

logger = logging.getLogger(__name__)
try:
    from pydub import AudioSegment
except:
    logger.warning('pydub not found')


class InputNode(SingleInputNode):

    def process(self, messages: list[Message]):
        pass


@dataclass
class VideoInfo:
    fps: float = field(default=None)
    weight: int = field(default=None)
    height: int = field(default=None)
    offset_idx: int = field(default=None)
    offset_time: int = field(default=None)
    src_fps: float = field(default=None)
    audio_sample_rate: int = field(default=None)
    audio_channel_count: int = field(default=None)

    def __getitem__(self, key):
        return getattr(self, key)

    def get(self, key, default=None):
        return getattr(self, key, default)


@dataclass
class FrameInfo:
    time: int = field(default=None)
    time_str: str = field(default=None)
    time_str2: str = field(default=None)
    utc_time: int = field(default=None)
    video_time: int = field(default=None)
    video_idx: int = field(default=None)
    src_video_idx: int = field(default=None)
    audio_sample_rate: int = field(default=None)
    audio_channel_count: int = field(default=None)
    audio_start_time: int = field(default=None)
    side_data: dict = field(default_factory=lambda: {})
    info: dict = field(default_factory=lambda: {})

    @property
    def sei(self):
        return self.side_data

    def __getitem__(self, key):
        return getattr(self, key)

    def get(self, key, default=None):
        return getattr(self, key, default)


@dataclass
class HeaderInfoPack:
    video_info: VideoInfo = field(default_factory=lambda: VideoInfo())
    frame_info: FrameInfo = field(default_factory=lambda: FrameInfo())

    def __getitem__(self, key):
        return getattr(self, key)

    def get(self, key, default=None):
        return getattr(self, key, default)

    @property
    def frame_index_info(self):
        return self.frame_info


@dataclass
class FrameInfoPack:
    image: Union[np.ndarray, torch.Tensor] = field(default_factory=lambda: None)
    audio: Union[np.ndarray, "AudioSegment"] = field(default_factory=lambda: None)
    video_info: VideoInfo = field(default_factory=lambda: VideoInfo())
    frame_info: FrameInfo = field(default_factory=lambda: FrameInfo())

    def __getitem__(self, key):
        return getattr(self, key)

    def get(self, key, default=None):
        return getattr(self, key, default)


class Chain(MermaidNodesChain):

    def __init__(self, params):
        if not isinstance(params, EnhanceDict):
            params = EnhanceDict(params)
        self.params = params
        self.chain_name = value_or_default(params.chain_name, 'CHAIN')
        self.chain_mmd_file_path = self.params.chain_mmd_file_path
        self.nodes_builders = self.params.nodes_builders
        self.chain_payload_builder = value_or_default(params.chain_payload_builder, lambda: FrameInfoPack())
        self.chain_header_builder = value_or_default(params.chain_header_builder, lambda: HeaderInfoPack())
        self.nodes_builders = self.params.nodes_builders
        self._set_ex_callback()
        super().__init__(logger=params.logger or None, node_exception_callback=self.node_exception_callback)
        init_chain_context = value_or_default(self.params.init_chain_context, {})
        for key, value in init_chain_context.items():
            self.context[key] = value

    def _set_ex_callback(self):
        if self.params.exception_callback:
            def node_exception_callback(key, this_node, message, e):
                time = message.header.get('frame_info', {}).get('sei', {}).get('time', -1)
                if key.startswith('NODE_'):
                    self.params.exception_callback(f'{self.chain_name.upper()}_ERROR', 'ERROR',
                                                   f'task_id:{self.params.task_id},node:{this_node.name},time:{time},error:{str(e)}')
                else:
                    self.params.exception_callback(f'{self.chain_name.upper()}_{key}',
                                                   f'task_id:{self.params.task_id},node:{this_node.name},time:{time},error:{str(e)}')

            self.node_exception_callback = node_exception_callback
            self.exception_callback = self.params.exception_callback
        else:
            self.node_exception_callback = lambda key, this_node, message, e: None
            self.exception_callback = lambda key, message: None

    def nodes_builder(self) -> (str, map):
        self.nodes_builders['InputNode'] = lambda: InputNode()
        return 'InputNode', self.nodes_builders

    def link_edges(self) -> set[tuple] | str:
        with open(self.chain_mmd_file_path, 'r', encoding='utf-8') as f:
            text = f.read()
            return text

    def input(self, data):

        if not data.get('weight'):
            if data.get('frame'):
                data['weight'] = data['frame'].shape[1] if isinstance(data['frame'], np.ndarray) else \
                    data['frame'].shape[2]
            else:
                data['weight'] = 0
        if not data.get('height'):
            if data.get('frame'):
                data['height'] = data['frame'].shape[0] if isinstance(data['frame'], np.ndarray) else \
                    data['frame'].shape[1]
            else:
                data['height'] = 0

        sei = data.get('sei') or {}
        sei = sei if isinstance(sei, dict) else json.loads(sei)
        sei_utc = sei.get('utc', None)
        sei = {"utc": data['src_frame_time'], "idx": data['src_frame_idx'], **sei}
        sei = {**sei, 'utc_str': vms2str_auto(sei['utc'])}

        if data.get('audio'):
            audio_data = data['audio']['data']
            sample_rate = data['audio']['sample_rate']
            sample_channel_count = data['audio']['channel_count']
            audio_start_time = data['audio']['start_time']
        else:
            audio_data, sample_rate, sample_channel_count, audio_start_time = None, None, None, None
        video_info = VideoInfo(fps=data['fps'],
                               weight=data.get('weight'),
                               height=data.get('height'),
                               offset_idx=data.get('offset_idx'),
                               offset_time=data.get('offset_time'),
                               src_fps=data.get('src_fps'),
                               audio_sample_rate=sample_rate,
                               audio_channel_count=sample_channel_count)
        time_str = vms2str_auto(sei['utc'])
        frame_info = FrameInfo(time=sei['utc'],
                               time_str=time_str,
                               time_str2=time_str.replace(':', '-').replace(' ', '_'),
                               utc_time=sei_utc,
                               video_time=data['src_frame_time'],
                               video_idx=data['target_frame_idx'],
                               src_video_idx=data['src_frame_idx'],
                               audio_sample_rate=sample_rate,
                               audio_channel_count=sample_channel_count,
                               audio_start_time=audio_start_time,
                               side_data=sei,
                               info={**data, 'frame': None, 'audio': None})
        header = self.chain_header_builder()
        header.video_info = video_info
        header.frame_info = frame_info

        image = data['frame']
        if isinstance(image, torch.Tensor) and image.device.type == 'cpu':
            image = image.cuda()
        payload = self.chain_payload_builder()
        payload.image = image
        payload.audio = audio_data
        payload.video_info = video_info
        payload.frame_info = frame_info
        message = self.message_maker.data_message(header=header, payload=payload)
        self.context['newest_message'] = message
        super().input(message)


class Executor(ChainExecutor):
    def __init__(self, video_path, params):
        self.params = params
        if video_path != -1:
            # from aabd.video.cv_tools import video_info
            context = {}
            # w, h, fps, _ = video_info(video_path)

            params['chain_context'] = context
            task_id = params.get("task_id", None)
            data_stream_conf = params.data_stream
            data_stream_conf['task_id'] = task_id

            if params.data_stream.stream_type == 'sync':
                data_stream = VideoFrameDataStream(video_path, context=context, logger=params.logger or None,
                                                   event_callback=params.event_callback or None, **data_stream_conf)
                fps = data_stream.stream_decoder.target_fps
            else:
                data_stream = VideoFrameQueueDataStream(video_path, context=context, logger=params.logger or None,
                                                        event_callback=params.event_callback or None,
                                                        **data_stream_conf)
                fps = data_stream.data_stream.stream_decoder.target_fps
            params['video_fps'] = fps
        else:
            params['video_fps'] = 25
            params['chain_context'] = {}
            params['task_id'] = 'init'
            data_stream = None
        chain = Chain(params)
        super().__init__(data_stream, chain)
