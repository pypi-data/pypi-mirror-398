import io
import json
import math
import queue
import time
from abc import abstractmethod
import logging
from threading import Thread
import cv2
import numpy
import os
from PIL import Image
from aabd.image import conv_img

def_logger = logging.getLogger(__name__)
video_keywords = ('.mp4', '.avi', '.mkv', '.mov', '.flv')

try:
    import torch
    import torch.nn.functional as F

except ImportError:
    print('PyTorch not found.')


def tensor2numpy_bgr(img_tensor):
    img = (img_tensor * 255.0).cpu().numpy()
    img = img.astype(numpy.uint8)
    if len(img.shape) == 3 and img.shape[0] == 3:  # 对于RGB图像
        img = numpy.transpose(img, (1, 2, 0))  # 更改维度顺序
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)  # OpenCV使用BGR格式
        return img


def video_info(video_path, timeout=5000):
    data = []

    def func():
        cap = cv2.VideoCapture(video_path)
        w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        cap.release()
        data.append((int(w), int(h), fps, int(frame_count)))

    Thread(target=func).start()
    start_time = time.time()
    while time.time() - start_time < timeout / 1000:
        if len(data) > 0:
            return data[0]
        else:
            time.sleep(0.01)
    raise Exception("read video timeout")


class VideoFrameRateConverter:
    def __init__(self, fps, target_fps):
        self.fps = fps
        self.target_fps = target_fps
        self.ori_frame_count = 0
        self.target_frame_count = 0
        self.change_frame_pointer_time = 0

    def update(self, utc=0):
        take_enable = False
        if utc is not None and utc > 0:
            if self.ori_frame_count == 0:
                self.change_frame_pointer_time = utc
            current_time_point = utc
            next_time_point = self.change_frame_pointer_time
        else:
            next_time_point = self.target_frame_count * 1000 / self.target_fps
            current_time_point = int(self.ori_frame_count * 1000 / self.fps)
        if current_time_point >= next_time_point:
            take_enable = True
            ori_frame_count, target_frame_count = self.ori_frame_count, self.target_frame_count
            # 使用utc时间时,如果出现丢帧则将节拍追上
            while True:
                self.change_frame_pointer_time += 1000 / self.target_fps
                if self.change_frame_pointer_time > current_time_point:
                    break
            self.target_frame_count += 1
        else:
            ori_frame_count, target_frame_count = self.ori_frame_count, self.target_frame_count
        self.ori_frame_count += 1

        return take_enable, ori_frame_count, target_frame_count, current_time_point


class StreamDecoder:
    def __init__(self, video_path, start=0, end=None, max_fps=500, out_path=None, logger=def_logger,
                 tqdm_enable=True, control_type='frame', is_live=None, frame_type='numpy_rgb', fps_force_25_50=False,
                 fps_force_unstable_to_25=False, **kwargs):

        if fps_force_unstable_to_25:
            fps_force_25_50 = True
        # numpy_rgb,numpy_bgr,pillow,tensor
        self.frame_type = frame_type or 'numpy_rgb'

        if logger is None:
            self.logger = def_logger
        else:
            self.logger = logger
        self.video_path = video_path

        if kwargs.get('mock_enable', False):
            self.is_live = is_live or False
            self.width = kwargs.get('image_width', 1920)
            self.height = kwargs.get('image_height', 1080)
            self.read_fps = kwargs.get('read_fps', max_fps)
            frame_count = kwargs.get('frame_count', 999999999)
            self.sample_rate = kwargs.get('sample_rate', 44100)
            self.sample_channel_count = kwargs.get('sample_channel_count', 2)
        else:
            if is_live is None:
                if (video_path.startswith('rtmp') or video_path.startswith('rtsp') or video_path.endswith('.m3u8')
                        or video_path.startswith('queue')):
                    self.is_live = True
                elif video_path.endswith(video_keywords):
                    self.is_live = False
                else:
                    raise ValueError('live is null')
            else:
                self.is_live = is_live
            if self.is_live and start > 0:
                raise Exception('start must be 0 for live stream')
            self.width, self.height, self.read_fps, frame_count = video_info(video_path,
                                                                             timeout=kwargs.get('open_video_timeout',
                                                                                                5000))

        if abs(self.read_fps - 25) < 0.2:
            self.correct_fps = 25.
        elif abs(self.read_fps - 30) < 0.2:
            self.correct_fps = 30.
        elif abs(self.read_fps - 50) < 0.2:
            self.correct_fps = 50.
        else:
            self.correct_fps = self.read_fps

        if fps_force_25_50:
            if self.correct_fps <= 30:
                self.force_correct_fps = 25.
            else:
                self.force_correct_fps = 50.
        else:
            self.force_correct_fps = self.correct_fps

        self.fps = self.force_correct_fps
        # self.ori_start = start
        # self.ori_end = end
        # self.ori_max_fps = max_fps or self.fps
        # self.target_fps = min(self.ori_max_fps, self.fps)
        self.target_fps = min(max_fps, self.fps)
        # calc_target_fps目的是兼容如果遇到不稳定的帧率时,将帧率强制改为25或50
        if fps_force_unstable_to_25:
            self.target_fps = 25
            self.calc_target_fps = 25 if self.fps > 30 else 30
        else:
            self.calc_target_fps = self.target_fps

        self.total_frame = None
        if not self.is_live and control_type == 'frame':
            self.start_frame = start
            self.start_time = start / self.fps * 1000
            self.end_frame = end if end is not None and end <= frame_count else frame_count
            self.end_time = self.end_frame / self.fps * 1000
            self.total_frame = self.end_frame - self.start_frame
        elif not self.is_live and control_type == 'time':
            self.start_frame = int(start / 1000 * self.fps)
            self.start_time = start
            self.end_frame = int(end / 1000 * self.fps) if end is not None else frame_count
            self.end_frame = min(self.end_frame, frame_count)
            self.end_time = self.end_frame / self.fps * 1000
            self.total_frame = self.end_frame - self.start_frame
        elif self.is_live and control_type == 'frame':
            # self.start_frame = start
            self.start_frame = 0
            self.start_time = 0
            self.end_frame = end
            if end is not None:
                self.end_time = end / self.fps * 1000
                self.total_frame = self.end_frame - self.start_frame
        elif self.is_live and control_type == 'time':
            self.start_frame = int(start / 1000 * self.fps)
            self.start_time = start
            self.start_frame = 0
            self.end_frame = None if end is None else int(end / 1000 * self.fps)
            if end is not None:
                self.end_time = end
                self.total_frame = self.end_frame - self.start_frame

        if tqdm_enable and self.total_frame is not None:
            from tqdm import tqdm
            self.tqdm_c = tqdm(total=self.__len__(), unit='frame', desc=f'{os.path.basename(video_path)}')
        else:
            self.tqdm_c = None

        self.out_writer = self.__make_video_writer__(out_path) if out_path is not None else None

        self.kwargs = kwargs

        self.stop_flag = False

        self.fram_iter = self.decode_iter()

        self.tqdm_count = 0

        self.sei_enable = self.kwargs.get('sei_enable', True)
        self.sei_utc_enable = self.kwargs.get('sei_utc_enable', True)
        self.sei_key = self.kwargs.get('sei_key', None)

        if kwargs.get('time_log_enable', False):
            self.time_log_delay_threshold = kwargs.get('time_log_delay_threshold', -1000)
            from aabd.base.log_setting import get_set_once_logger
            lm = kwargs.get('task_id', None) or f'dm{str(int(time.time()))}'
            self.tmp_logger = get_set_once_logger(f"dtl_{lm}", log_type="single_file", sub_dir='decoder_time_log',
                                                  propagate=True)
        else:
            self.tmp_logger = None
        self.sample_rate = 0
        self.sample_channel_count = 0

        if not self.is_live:
            self.playback_speed = kwargs.get('file_playback_speed', -1)
            self.playback_speed_enable = self.playback_speed > 0
            self.last_yield_data_time = 0
            self.every_yield_time = 1 / self.calc_target_fps / self.playback_speed if self.playback_speed > 0 else -1
        else:
            self.playback_speed_enable = False

        self.logger.info(f'stream_decoder_info -> path:{self.video_path}, '
                         f'src_fps:[{self.read_fps},{self.correct_fps},{self.force_correct_fps}],'
                         f'target_fps:[{self.target_fps},{self.calc_target_fps}]')

    @abstractmethod
    def decode_iter(self):
        pass

    def __make_video_writer__(self, output_video_path):
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        return cv2.VideoWriter(output_video_path, fourcc, self.fps, (self.width, self.height))

    def __enter__(self):
        if self.out_writer is not None:
            return self, self.out_writer
        else:
            return self, None

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def stop(self):
        try:
            # 尝试发送停止信号，适用于协程或生成器
            self.stop_flag = True
            if self.out_writer is not None:
                self.out_writer.release()
        except Exception:
            pass

    def __next__(self):
        data = next(self.fram_iter)
        if self.tqdm_c is not None:
            # update_data = data['src_frame_idx'] - self.tqdm_count
            self.tqdm_c.update(1)
            # self.tqdm_count = data['src_frame_idx']
        return data

    def __iter__(self):
        return self

    def __len__(self):
        if self.total_frame:
            return math.ceil(self.total_frame / self.fps * self.target_fps)
        else:
            return 0

    def _yield_data(self, frame_image, src_frame_idx, src_frame_time, target_frame_idx, sei_msg=None,
                    skip_frame_infos=None, extra_data=None, audio_data=None, audio_start_time=0):
        if skip_frame_infos is None:
            skip_frame_infos = []
        if self.playback_speed_enable:
            yield_duration = time.time() - self.last_yield_data_time
            if yield_duration < self.every_yield_time:
                time.sleep(self.every_yield_time - yield_duration)
            self.last_yield_data_time = time.time()
        # self.logger.info(f'yield_data {int(time.time() * 1000)}')
        yield {
            'src_fps': self.fps,
            'fps': self.target_fps,
            'offset_idx': self.start_frame,
            'offset_time': self.start_time,
            'src_frame_idx': src_frame_idx,
            'src_frame_time': src_frame_time,
            'target_frame_idx': target_frame_idx,
            'frame': frame_image,
            'weight': self.width,
            'height': self.height,
            "audio": {
                "data": audio_data,
                "sample_rate": self.sample_rate,
                "channel_count": self.sample_channel_count,
                "start_time": audio_start_time
            } if audio_data is not None else None,
            # 'target_frame_time': target_frame_count * 1000 / target_fps,
            'sei': sei_msg,
            'skip_frame_infos': skip_frame_infos,
            'decoder_timestamp': int(time.time() * 1000),
            'extra_data': extra_data,
        }

    def _sei2utc(self, sei_msg):
        utc = 0
        if self.sei_utc_enable:
            try:
                if sei_msg is None or sei_msg == '':
                    return 0
                elif isinstance(sei_msg, dict):
                    utc = sei_msg.get('utc', 0)
                elif isinstance(sei_msg, str):
                    utc = 0 if len(sei_msg) <= 1 else int(json.loads(sei_msg)['utc'])
            except:
                self.logger.exception('sei2utc error')
                utc = 0
        return utc

    def process_sei(self, sei):
        if sei is None or sei == '':
            return None
        if isinstance(sei, str):
            sei = json.loads(sei)
        utc = sei.get('utc', 0)
        uuid = sei.get('uuid', None)
        if utc > 1e15:
            sei = {'utc': int(utc / 1000), 'utc_us': utc}
        else:
            sei = {'utc': utc, 'utc_us': int(utc * 1000)}
        if uuid is not None:
            sei['stream_id'] = uuid
        return sei


class SDKStreamDecoder(StreamDecoder):
    def __init__(self, video_path, start=0, end=None, max_fps=500, out_path=None, logger=def_logger, tqdm_enable=True,
                 control_type='frame', is_live=None, frame_type='numpy_rgb', **kwargs):
        super().__init__(video_path, start, end, max_fps, out_path, logger, tqdm_enable, control_type, is_live,
                         frame_type, **kwargs)

    def decode_iter(self):
        if self.stop_flag:
            return
        import xvdecoder
        ret = xvdecoder.start_decoder(self.video_path, self.sei_key or '', 10, "xvdecoder.log")

        ori_frame_count = 0
        seek_idx = 0

        frame_rate_converter = VideoFrameRateConverter(self.fps, self.calc_target_fps)

        try:
            skip_frame_infos = []
            while True:
                time_log1 = int(time.time() * 1000)
                if self.stop_flag:
                    break

                # 如果帧数够了停止
                if self.total_frame is not None and ori_frame_count >= self.total_frame:
                    break
                tensor = xvdecoder.decode_frame_to_tensor()
                if tensor is None or tensor.numel() == 0:
                    # 检查内部c++任务是否已经结束
                    is_finished = xvdecoder.check_finished()

                    if is_finished > 0:
                        print("is_finished ", is_finished)
                        break
                    else:
                        time.sleep(0.1)
                        continue
                if seek_idx < self.start_frame:
                    seek_idx += 1
                    continue
                sei_msg = xvdecoder.get_curr_sei_msg()
                sei_msg = self.process_sei(sei_msg)
                utc = 0
                if self.sei_enable:
                    if self.sei_utc_enable:
                        utc = self._sei2utc(sei_msg)
                else:
                    sei_msg = None
                frame_enable, ori_frame_count, target_frame_count, current_time_point = frame_rate_converter.update(utc)
                time_log2 = time_log3 = time_log1
                if frame_enable:
                    if self.frame_type == 'numpy_bgr':
                        image_data = tensor.cpu().numpy()[:, :, ::-1]
                    elif self.frame_type == 'numpy_rgb':
                        image_data = tensor.cpu().numpy()
                    elif self.frame_type == 'tensor':
                        image_data = tensor.float() / 255.0
                        image_data = torch.clamp(image_data, 0.0, 1.0)
                        image_data = image_data.permute(2, 0, 1)
                        # image_data = image_data[[2, 1, 0], :, :]
                    else:
                        image_data = None

                    time_log2 = int(time.time() * 1000)
                    yield from self._yield_data(frame_image=image_data,
                                                src_frame_idx=ori_frame_count,
                                                src_frame_time=round(current_time_point),
                                                target_frame_idx=target_frame_count,
                                                sei_msg=sei_msg,
                                                skip_frame_infos=skip_frame_infos)
                    time_log3 = int(time.time() * 1000)
                    skip_frame_infos = []
                else:
                    skip_frame_infos.append({
                        'src_frame_idx': ori_frame_count,
                        'src_frame_time': current_time_point,
                        'target_frame_idx': target_frame_count,
                        'sei': sei_msg,
                    })
                if self.tmp_logger:
                    log_mark = "OKK" if time_log3 - utc < self.time_log_delay_threshold else "BAD"
                    self.tmp_logger.info(
                        f'SDTLOG|{frame_enable}|{log_mark}|sei:{sei_msg}|ofidx:{ori_frame_count}|tfidx:{target_frame_count}|time1:{time_log1}|time2:{time_log2}|time3:{time_log3}|decoder:{time_log2 - time_log1}|model:{time_log3 - time_log2}|delay:{time_log3 - utc}')

        except:
            self.logger.exception("xvdecoder error")
        finally:
            xvdecoder.stop_decoder()


class AV0StreamDecoder(StreamDecoder):
    def __init__(self, video_path, start=0, end=None, max_fps=500, out_path=None, logger=def_logger, tqdm_enable=True,
                 control_type='frame', is_live=None, to_device='cpu', frame_type='numpy_rgb', gpu_decoder=False,
                 **kwargs):
        self.to_device = to_device
        self.gpu_decoder = gpu_decoder
        self.decode_image_enable = kwargs.get('decode_image_enable', True),
        self.decode_audio_enable = kwargs.get('decode_audio_enable', False)
        super().__init__(video_path, start, end, max_fps, out_path, logger, tqdm_enable, control_type, is_live,
                         frame_type, **kwargs)

    def yuv420p_to_rgb_gpu(self, y, u, v):
        y = torch.tensor(y, dtype=torch.float32, device=self.to_device)
        u = torch.tensor(u, dtype=torch.float32, device=self.to_device)
        v = torch.tensor(v, dtype=torch.float32, device=self.to_device)

        # 上采样 U 和 V 到 Y 的分辨率
        u_upsampled = u.repeat_interleave(2, dim=0).repeat_interleave(2, dim=1)
        v_upsampled = v.repeat_interleave(2, dim=0).repeat_interleave(2, dim=1)

        # YUV 转 RGB 公式（BT.601）
        r = y + 1.402 * (v_upsampled - 128)
        g = y - 0.34414 * (u_upsampled - 128) - 0.71414 * (v_upsampled - 128)
        b = y + 1.772 * (u_upsampled - 128)

        # 合并通道并裁剪到 [0, 255]
        rgb = torch.stack([r, g, b], dim=0).clamp(0, 255)

        # 归一化到 [0, 1]
        rgb_normalized = rgb / 255.0

        return rgb_normalized  # 返回 float32 类型，范围 [0, 1]

    def _get_sei_msg(self, frame):
        return ''

    def decode_iter(self):

        if self.stop_flag:
            return
        import av

        if self.kwargs.get('ffmpeg_path', None):
            ffmpeg_path = self.kwargs.get('ffmpeg_path', None)
            try:
                av.utils.ffmpeg_path = ffmpeg_path
            except:
                self.logger.exception('ffmpeg path set error')

        container = None
        if self.gpu_decoder:
            try:
                from av.codec.hwaccel import HWAccel, hwdevices_available
                if 'cuda' in hwdevices_available():
                    hwaccel = HWAccel(device_type='cuda', allow_software_fallback=False)
                    container = av.open(self.video_path, hwaccel=hwaccel, timeout=5)
            except:
                self.logger.exception('gpu ffmpeg error')

        if container is None:
            container = av.open(self.video_path, timeout=5)
        if self.stop_flag:
            return
        with container:
            video_stream = None
            audio_stream = None
            for stream in container.streams:
                if stream.type == 'video' and video_stream is None:
                    video_stream = stream
                elif self.decode_audio_enable and stream.type == 'audio' and audio_stream is None:
                    audio_stream = stream

            if not audio_stream:
                self.sample_rate = None
                self.sample_channel_count = None
                has_audio = False
                audio_buffer = None
            else:
                self.sample_rate = audio_stream.sample_rate
                self.sample_channel_count = audio_stream.channels
                has_audio = True
                from pydub import AudioSegment
                audio_buffer = AudioSegment(bytes(), sample_width=2, frame_rate=self.sample_rate,
                                            channels=self.sample_channel_count)

            time_base = video_stream.time_base
            if self.start_time is not None and self.start_time > 0:
                container.seek(
                    int(self.start_time / 1000 / time_base),
                    stream=video_stream
                )

            if self.frame_type == "tensor":
                from torchvision import transforms
                to_tensor = transforms.ToTensor()

            # 需要seek
            seek_tag = self.start_time is not None and self.start_time > 0

            ori_frame_count = 0

            frame_rate_converter = VideoFrameRateConverter(self.fps, self.calc_target_fps)
            skip_frame_infos = []

            audio_start_time = 0
            for packet in container.demux(video_stream, audio_stream if has_audio else ()):
                for frame in packet.decode():
                    if packet.stream.type == 'audio':
                        audio_array = frame.to_ndarray()
                        dtype = audio_array.dtype

                        if dtype == numpy.float32:
                            audio_array = audio_array
                        elif dtype == numpy.float64:
                            audio_array = audio_array.astype(numpy.float32)
                        elif dtype == numpy.int16:
                            audio_array = audio_array.astype(numpy.float32) / 32768.0
                        elif dtype == numpy.int32:
                            audio_array = audio_array.astype(numpy.float32) / 2147483648.0
                        elif dtype == numpy.uint8:
                            audio_array = (audio_array.astype(numpy.float32) - 128.0) / 128.0
                        else:
                            raise ValueError(f"Unsupported dtype: {dtype}")
                        int16_audio = (audio_array * 32767).clip(-32768, 32767).astype(numpy.int16)
                        raw_bytes = int16_audio.tobytes()
                        audio_buffer += AudioSegment(raw_bytes, sample_width=2,
                                                     channels=self.sample_channel_count,
                                                     frame_rate=self.sample_rate)
                        continue

                    time_log1 = int(time.time() * 1000)
                    # 遇到停止标识停止
                    if self.stop_flag:
                        break

                    # 由于seek只是到关键帧需要继续到指定位置
                    if seek_tag and float(frame.time * 1000) < self.start_time:
                        continue
                    seek_tag = False

                    # 如果帧数够了停止
                    if self.total_frame is not None and ori_frame_count >= self.total_frame:
                        break
                    sei_msg = None
                    utc = 0
                    if self.sei_enable:
                        sei_msg = self._get_sei_msg(frame)
                        sei_msg = self.process_sei(sei_msg)
                        if self.sei_utc_enable:
                            utc = self._sei2utc(sei_msg)
                    frame_enable, ori_frame_count, target_frame_count, current_time_point = frame_rate_converter.update(
                        utc)
                    time_log2 = time_log3 = time_log1

                    if frame_enable:
                        if self.decode_image_enable and frame.format.name == 'nv12' and self.gpu_decoder and self.frame_type == 'tensor':
                            yuv_data = frame.reformat(format='yuv420p')
                            y_plane = yuv_data.planes[0]
                            y_plane_n = numpy.frombuffer(y_plane, dtype=numpy.uint8).reshape(
                                (y_plane.height, y_plane.width))
                            u_plane = yuv_data.planes[1]
                            u_plane_n = numpy.frombuffer(u_plane, dtype=numpy.uint8).reshape(
                                (u_plane.height, u_plane.width))
                            v_plane = yuv_data.planes[2]
                            v_plane_n = numpy.frombuffer(v_plane, dtype=numpy.uint8).reshape(
                                (v_plane.height, v_plane.width))

                            final_frame = self.yuv420p_to_rgb_gpu(y_plane_n, u_plane_n, v_plane_n)
                        elif self.decode_image_enable:
                            if self.frame_type == 'pillow':
                                final_frame = frame.to_image()
                            elif self.frame_type == 'numpy_rgb':
                                final_frame = frame.to_ndarray(format='rgb24')
                            elif self.frame_type == 'numpy_bgr':
                                final_frame = frame.to_ndarray(format='bgr24')
                            elif self.frame_type == 'tensor':
                                if self.to_device.startswith('cuda') and frame.format.name == 'yuv420p':
                                    yuv_data = frame.reformat(format='yuv420p')
                                    y_plane = yuv_data.planes[0]
                                    y_plane_n = numpy.frombuffer(y_plane, dtype=numpy.uint8).reshape(
                                        (y_plane.height, y_plane.width))
                                    u_plane = yuv_data.planes[1]
                                    u_plane_n = numpy.frombuffer(u_plane, dtype=numpy.uint8).reshape(
                                        (u_plane.height, u_plane.width))
                                    v_plane = yuv_data.planes[2]
                                    v_plane_n = numpy.frombuffer(v_plane, dtype=numpy.uint8).reshape(
                                        (v_plane.height, v_plane.width))

                                    final_frame = self.yuv420p_to_rgb_gpu(y_plane_n, u_plane_n, v_plane_n)
                                else:
                                    final_frame = to_tensor(frame.to_ndarray(format='rgb24'))
                        else:
                            final_frame = None
                        time_log2 = int(time.time() * 1000)

                        yield from self._yield_data(frame_image=final_frame,
                                                    src_frame_idx=ori_frame_count,
                                                    src_frame_time=round(current_time_point),
                                                    target_frame_idx=target_frame_count,
                                                    sei_msg=sei_msg,
                                                    skip_frame_infos=skip_frame_infos,
                                                    audio_data=audio_buffer,
                                                    audio_start_time=audio_start_time)
                        if has_audio:
                            audio_start_time += len(audio_buffer)
                            audio_buffer = AudioSegment(bytes(), sample_width=2,
                                                        frame_rate=self.sample_rate,
                                                        channels=self.sample_channel_count)

                        time_log3 = int(time.time() * 1000)
                        skip_frame_infos = []
                    else:
                        skip_frame_infos.append({
                            'src_frame_idx': ori_frame_count,
                            'src_frame_time': current_time_point,
                            'target_frame_idx': target_frame_count,
                            'sei': sei_msg,
                        })
                    if self.tmp_logger:
                        log_mark = "OKK" if time_log3 - utc < self.time_log_delay_threshold else "BAD"
                        self.tmp_logger.info(
                            f'SDTLOG|{frame_enable}|{log_mark}|sei:{sei_msg}|ofidx:{ori_frame_count}|tfidx:{target_frame_count}|time1:{time_log1}|time2:{time_log2}|time3:{time_log3}|decoder:{time_log2 - time_log1}|model:{time_log3 - time_log2}|delay:{time_log3 - utc}')


class AVAStreamDecoder(AV0StreamDecoder):
    def _get_sei_msg(self, frame):
        sei_message_str = None
        if self.sei_enable:
            sei_message_str = None
            if self.sei_key is not None:
                try:
                    for sd in frame.side_data:
                        sd_str = bytes(sd).decode('utf-8')
                        if sd_str.startswith(self.sei_key):
                            sei_message_str = sd_str[len(self.sei_key):]
                            break
                except:
                    self.logger.exception('解析sei信息错误')
        return sei_message_str


class AVBStreamDecoder(AV0StreamDecoder):
    def _get_sei_msg(self, frame):
        sei_message_str = None
        if self.sei_enable:
            sei_message_str = None
            if self.sei_key is not None:
                try:
                    for sd in frame.side_data:
                        try:
                            sei_message_str = bytes(sd)[16:-1].decode('utf-8')
                            if sei_message_str.startswith("{"):
                                sei_message_str = json.dumps({
                                    "utc": json.loads(sei_message_str)['utc'],
                                    "origin_utc": 0,
                                    "origin_offset": 0
                                })
                                break
                        except:
                            pass
                except:
                    self.logger.exception('解析sei信息错误')
        return sei_message_str


class AVCStreamDecoder(AV0StreamDecoder):
    def _get_sei_msg(self, frame):
        sei_message_str = None
        if self.sei_enable:
            sei_message_str = None
            if self.sei_key is not None:
                try:
                    for sd in frame.side_data:
                        try:
                            sei_message_str = bytes(sd)[16:-1].decode('utf-8')
                            if sei_message_str.startswith("{"):
                                break
                        except:
                            pass
                except:
                    self.logger.exception('解析sei信息错误')
        return sei_message_str


class CVStreamDecoder(StreamDecoder):
    def __init__(self, video_path, start=0, end=None, max_fps=500, out_path=None, logger=def_logger, tqdm_enable=True,
                 control_type='frame', is_live=None, to_device='cpu', frame_type='numpy_rgb', **kwargs):
        self.to_device = to_device
        super().__init__(video_path, start, end, max_fps, out_path, logger, tqdm_enable, control_type, is_live,
                         frame_type, **kwargs)

    def decode_iter(self):
        from PIL import Image
        if self.stop_flag:
            return

        # 使用 OpenCV 的 VideoCapture
        cap = cv2.VideoCapture(self.video_path)
        try:
            if not cap.isOpened():
                self.logger.error("无法打开视频文件")
                return

            self.logger.info(
                f'video info --> video:{self.video_path}, total_frames:{self.total_frame}, fps:{self.fps}, is_hwaccel:False'
            )

            # 设置起始时间跳转
            if self.start_time is not None and self.start_time > 0:
                cap.set(cv2.CAP_PROP_POS_MSEC, self.start_time)

            frame_rate_converter = VideoFrameRateConverter(self.fps, self.calc_target_fps)
            ori_frame_count = 0
            target_frame_count = 0
            # 转换为 tensor 的 transform
            if self.frame_type == "tensor":
                from torchvision import transforms
                to_tensor = transforms.ToTensor()
            else:
                pass  # 其他格式处理
            skip_frame_infos = []
            # 逐帧读取
            while True:
                time_log1 = int(time.time() * 1000)
                # 遇到停止标识停止
                if self.stop_flag:
                    break

                # 如果帧数够了停止
                if self.total_frame is not None and ori_frame_count >= self.total_frame:
                    break

                ret, frame_bgr = cap.read()
                if not ret:
                    break

                sei_msg = None
                utc = 0

                frame_enable, ori_frame_count, target_frame_count, current_time_point = frame_rate_converter.update(utc)
                time_log2 = time_log3 = time_log1

                if frame_enable:
                    # 处理帧格式转换
                    if self.frame_type == 'pillow':
                        final_frame = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
                    elif self.frame_type == 'numpy_rgb':
                        final_frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                    elif self.frame_type == 'numpy_bgr':
                        final_frame = frame_bgr
                    elif self.frame_type == 'tensor':
                        # OpenCV 帧为 BGR HWC，转换为 RGB CHW
                        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                        final_frame = to_tensor(frame_rgb).to(self.to_device)
                    else:
                        final_frame = None  # 默认返回 numpy_bgr

                    time_log2 = int(time.time() * 1000)
                    yield from self._yield_data(frame_image=final_frame,
                                                src_frame_idx=ori_frame_count,
                                                src_frame_time=round(current_time_point),
                                                target_frame_idx=target_frame_count,
                                                sei_msg=sei_msg,
                                                skip_frame_infos=skip_frame_infos)
                    time_log3 = int(time.time() * 1000)
                    skip_frame_infos = []
                else:
                    skip_frame_infos.append({
                        'src_frame_idx': ori_frame_count,
                        'src_frame_time': current_time_point,
                        'target_frame_idx': target_frame_count,
                        'sei': sei_msg,
                    })
                if self.tmp_logger:
                    log_mark = "OKK" if time_log3 - utc < self.time_log_delay_threshold else "BAD"
                    self.tmp_logger.info(
                        f'SDTLOG|{frame_enable}|{log_mark}|sei:{sei_msg}|ofidx:{ori_frame_count}|tfidx:{target_frame_count}|time1:{time_log1}|time2:{time_log2}|time3:{time_log3}|decoder:{time_log2 - time_log1}|model:{time_log3 - time_log2}|delay:{time_log3 - utc}')

        finally:
            cap.release()  # 清理资源


class MockStreamDecoder(StreamDecoder):
    def __init__(self, video_path, start=0, end=None, max_fps=500, out_path=None, logger=def_logger, tqdm_enable=True,
                 control_type='frame', is_live=None, to_device='cpu', frame_type='numpy_rgb', **kwargs):
        self.to_device = to_device
        super().__init__(video_path, start, end, max_fps, out_path, logger, tqdm_enable, control_type, is_live,
                         frame_type, mock_enable=True, **kwargs)

    def decode_iter(self):
        ori_frame_count = 0

        frame_rate_converter = VideoFrameRateConverter(self.fps, self.calc_target_fps)
        skip_frame_infos = []
        for _ in range(self.total_frame):
            time_log1 = int(time.time() * 1000)
            # 遇到停止标识停止
            if self.stop_flag:
                break
            # 如果帧数够了停止
            if self.total_frame is not None and ori_frame_count >= self.total_frame:
                break
            sei_msg = None
            utc = 0

            frame_enable, ori_frame_count, target_frame_count, current_time_point = frame_rate_converter.update(utc)
            time_log2 = time_log3 = time_log1
            if frame_enable:
                time_log2 = int(time.time() * 1000)
                yield from self._yield_data(frame_image=None,
                                            src_frame_idx=ori_frame_count,
                                            src_frame_time=round(current_time_point),
                                            target_frame_idx=target_frame_count,
                                            sei_msg=sei_msg,
                                            skip_frame_infos=skip_frame_infos)
                time_log3 = int(time.time() * 1000)
                skip_frame_infos = []
            else:
                skip_frame_infos.append({
                    'src_frame_idx': ori_frame_count,
                    'src_frame_time': current_time_point,
                    'target_frame_idx': target_frame_count,
                    'sei': sei_msg,
                })
            if self.tmp_logger:
                log_mark = "OKK" if time_log3 - utc < self.time_log_delay_threshold else "BAD"
                self.tmp_logger.info(
                    f'SDTLOG|{frame_enable}|{log_mark}|sei:{sei_msg}|ofidx:{ori_frame_count}|tfidx:{target_frame_count}|time1:{time_log1}|time2:{time_log2}|time3:{time_log3}|decoder:{time_log2 - time_log1}|model:{time_log3 - time_log2}|delay:{time_log3 - utc}')


class ImageDecoder(StreamDecoder):
    def __init__(self, video_path, read_fps=25, start=0, end=None, max_fps=500, out_path=None, logger=def_logger,
                 tqdm_enable=True, control_type='frame', is_live=None, to_device='cpu', frame_type='numpy_rgb',
                 **kwargs):
        from aabd.base import path_util
        if os.path.isdir(video_path):
            self.images = path_util.list_files(video_path, suffixes=['.jpg', '.png', '.jpeg'])
        else:
            self.images = [video_path]
        if len(self.images) == 0:
            raise Exception("no images")
        self.images = sorted(self.images)
        w, h = Image.open(self.images[0]).size

        self.to_device = to_device
        super().__init__(video_path, start, end, max_fps, out_path, logger, tqdm_enable, control_type, is_live,
                         frame_type, mock_enable=True, read_fps=read_fps, image_width=w, image_height=h,
                         frame_count=len(self.images), **kwargs)

        self.image_loader = self.image_loader()

    def image_loader(self):
        test_image = self.images[0]
        if self.frame_type == "tensor":
            from torchvision import transforms
            to_tensor = transforms.ToTensor()

        def read_image_func(x):
            pil_image = Image.open(x)
            if self.frame_type == 'pillow':
                final_frame = pil_image
            elif self.frame_type == 'numpy_rgb':
                final_frame = numpy.asarray(pil_image)
                if final_frame.shape[2] == 4:
                    final_frame = final_frame[:, :, :3]
            elif self.frame_type == 'numpy_bgr':
                final_frame = numpy.asarray(pil_image)
                if final_frame.shape[2] == 4:
                    final_frame = final_frame[:, :, :3]
                final_frame = final_frame[:, :, ::-1]
            elif self.frame_type == 'tensor':
                final_frame = numpy.asarray(pil_image)
                if final_frame.shape[2] == 4:
                    final_frame = final_frame[:, :, :3]
                final_frame = to_tensor(final_frame).to(self.to_device)
            else:
                final_frame = None  # 默认返回 numpy_bgr

            return final_frame

        try:
            cv2.imread(test_image)

            def read_image_func(x):
                frame_bgr = cv2.imread(x)
                if self.frame_type == 'pillow':
                    final_frame = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
                elif self.frame_type == 'numpy_rgb':
                    final_frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                elif self.frame_type == 'numpy_bgr':
                    final_frame = frame_bgr
                elif self.frame_type == 'tensor':
                    # OpenCV 帧为 BGR HWC，转换为 RGB CHW
                    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                    final_frame = to_tensor(frame_rgb).to(self.to_device)
                else:
                    final_frame = None  # 默认返回 numpy_bgr
                return final_frame
        except:
            pass
        return read_image_func

    def decode_iter(self):
        ori_frame_count = 0

        frame_rate_converter = VideoFrameRateConverter(self.fps, self.calc_target_fps)
        skip_frame_infos = []
        for _ in range(self.total_frame):
            time_log1 = int(time.time() * 1000)
            # 遇到停止标识停止
            if self.stop_flag:
                break
            # 如果帧数够了停止
            if self.total_frame is not None and ori_frame_count >= self.total_frame:
                break
            sei_msg = None
            utc = 0

            frame_enable, ori_frame_count, target_frame_count, current_time_point = frame_rate_converter.update(utc)
            time_log2 = time_log3 = time_log1
            if frame_enable:
                time_log2 = int(time.time() * 1000)
                frame_image = self.image_loader(self.images[ori_frame_count])
                yield from self._yield_data(frame_image=frame_image,
                                            src_frame_idx=ori_frame_count,
                                            src_frame_time=round(current_time_point),
                                            target_frame_idx=target_frame_count,
                                            sei_msg=sei_msg,
                                            skip_frame_infos=skip_frame_infos,
                                            extra_data={'frame_path': self.images[ori_frame_count]})
                time_log3 = int(time.time() * 1000)
                skip_frame_infos = []
            else:
                skip_frame_infos.append({
                    'src_frame_idx': ori_frame_count,
                    'src_frame_time': current_time_point,
                    'target_frame_idx': target_frame_count,
                    'sei': sei_msg,
                })
            if self.tmp_logger:
                log_mark = "OKK" if time_log3 - utc < self.time_log_delay_threshold else "BAD"
                self.tmp_logger.info(
                    f'SDTLOG|{frame_enable}|{log_mark}|sei:{sei_msg}|ofidx:{ori_frame_count}|tfidx:{target_frame_count}|time1:{time_log1}|time2:{time_log2}|time3:{time_log3}|decoder:{time_log2 - time_log1}|model:{time_log3 - time_log2}|delay:{time_log3 - utc}')


class AudioDecoder(StreamDecoder):

    def __init__(self, video_path, read_fps=25, start=0, end=None, max_fps=500, out_path=None, logger=def_logger,
                 tqdm_enable=True, control_type='frame', is_live=None, to_device='cpu', frame_type='numpy_rgb',
                 **kwargs):
        from pydub import AudioSegment
        self.decode_audio_enable = kwargs.get('decode_audio_enable', False)
        every_audio_len = int(1 / read_fps * 1000)
        self.audio = AudioSegment.from_file(video_path)
        # self.audio = self.audio.set_sample_width(2)
        if control_type == 'frame':
            start_time = every_audio_len * start
            if end is not None:
                end_time = every_audio_len * end
            else:
                end_time = None
        else:
            start_time = start
            end_time = end
        if end is None:
            self.audio = self.audio[start_time:]
        else:
            self.audio = self.audio[start_time:end_time]

        self.audios = self.split_audio(self.audio, every_audio_len)

        super().__init__(video_path, start, end, max_fps, out_path, logger, tqdm_enable, control_type, is_live,
                         frame_type, mock_enable=True, read_fps=read_fps, image_width=0, image_height=0,
                         frame_count=len(self.audios), **kwargs)
        self.sample_channel_count = self.audio.channels
        self.sample_rate = self.audio.frame_rate

    @staticmethod
    def split_audio(audio_segment, chunk_length_ms):
        """
        将 AudioSegment 对象按每 500ms 分割成多个片段
        返回一个包含所有片段的列表
        """
        chunks = []

        # 获取音频总时长（毫秒）
        total_duration_ms = len(audio_segment)

        # 按 500ms 切分
        for i in range(0, total_duration_ms, chunk_length_ms):
            chunk = audio_segment[i:i + chunk_length_ms]
            chunks.append(chunk)

        return chunks

    def decode_iter(self):
        ori_frame_count = 0

        frame_rate_converter = VideoFrameRateConverter(self.fps, self.calc_target_fps)
        skip_frame_infos = []
        audio_start_time = 0

        from pydub import AudioSegment
        audio_buffer = AudioSegment(bytes(), sample_width=2, frame_rate=self.sample_rate,
                                    channels=self.sample_channel_count)

        for _ in range(self.total_frame):

            time_log1 = int(time.time() * 1000)
            # 遇到停止标识停止
            if self.stop_flag:
                break
            # 如果帧数够了停止
            if self.total_frame is not None and ori_frame_count >= self.total_frame:
                break
            sei_msg = None
            utc = 0

            frame_enable, ori_frame_count, target_frame_count, current_time_point = frame_rate_converter.update(utc)
            audio_buffer += self.audios[ori_frame_count]
            time_log2 = time_log3 = time_log1
            if frame_enable:
                time_log2 = int(time.time() * 1000)
                yield from self._yield_data(frame_image=None,
                                            src_frame_idx=ori_frame_count,
                                            src_frame_time=round(current_time_point),
                                            target_frame_idx=target_frame_count,
                                            sei_msg=sei_msg,
                                            skip_frame_infos=skip_frame_infos,
                                            audio_data=audio_buffer,
                                            audio_start_time=audio_start_time)
                audio_start_time += len(audio_buffer)
                audio_buffer = AudioSegment(bytes(), sample_width=2, frame_rate=self.sample_rate,
                                            channels=self.sample_channel_count)
                time_log3 = int(time.time() * 1000)
                skip_frame_infos = []
            else:
                skip_frame_infos.append({
                    'src_frame_idx': ori_frame_count,
                    'src_frame_time': current_time_point,
                    'target_frame_idx': target_frame_count,
                    'sei': sei_msg,
                })
            if self.tmp_logger:
                log_mark = "OKK" if time_log3 - utc < self.time_log_delay_threshold else "BAD"
                self.tmp_logger.info(
                    f'SDTLOG|{frame_enable}|{log_mark}|sei:{sei_msg}|ofidx:{ori_frame_count}|tfidx:{target_frame_count}|time1:{time_log1}|time2:{time_log2}|time3:{time_log3}|decoder:{time_log2 - time_log1}|model:{time_log3 - time_log2}|delay:{time_log3 - utc}')


class QueueImageDecoder(StreamDecoder):
    def __init__(self, video_path, queue, cv_loader=True, image_width=1920, image_height=1080, read_fps=25, start=0,
                 end=None,
                 max_fps=500, out_path=None, logger=def_logger,
                 tqdm_enable=True, control_type='frame', is_live=None, to_device='cpu', frame_type='numpy_rgb',
                 **kwargs):
        self.queue = queue
        self.to_device = to_device
        super().__init__(video_path, start, end, max_fps, out_path, logger, tqdm_enable, control_type, True,
                         frame_type, mock_enable=True, read_fps=read_fps, image_width=image_width,
                         image_height=image_height, **kwargs)

        self.image_loader = self.image_loader()

    def image_loader(self, cv_loader=True):

        if not cv_loader:
            def read_image_func(x):
                if self.frame_type == 'pillow':
                    final_frame = conv_img.to_pil(x)
                elif self.frame_type == 'numpy_rgb':
                    final_frame = conv_img.to_numpy(x, target_color_order='RGB', target_dim_order='HWC',
                                                    target_normalized=False)
                elif self.frame_type == 'numpy_bgr':
                    final_frame = conv_img.to_numpy(x, target_color_order='BGR', target_dim_order='HWC',
                                                    target_normalized=False)
                elif self.frame_type == 'tensor':
                    final_frame = conv_img.to_tensor(x, target_color_order='RGB', target_dim_order='HWC',
                                                     target_normalized=False, target_device=self.to_device)
                else:
                    final_frame = None  # 默认返回 numpy_bgr

                return final_frame

        else:
            if self.frame_type == "tensor":
                from torchvision import transforms
                to_tensor = transforms.ToTensor()

            def read_image_func(x):
                frame_bgr = cv2.imread(x)
                if self.frame_type == 'pillow':
                    final_frame = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
                elif self.frame_type == 'numpy_rgb':
                    final_frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                elif self.frame_type == 'numpy_bgr':
                    final_frame = frame_bgr
                elif self.frame_type == 'tensor':
                    # OpenCV 帧为 BGR HWC，转换为 RGB CHW
                    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                    final_frame = to_tensor(frame_rgb).to(self.to_device)
                else:
                    final_frame = None  # 默认返回 numpy_bgr
                return final_frame
        return read_image_func

    def decode_iter(self):
        ori_frame_count = 0

        frame_rate_converter = VideoFrameRateConverter(self.fps, self.calc_target_fps)
        skip_frame_infos = []

        while True:
            time_log1 = int(time.time() * 1000)
            # 遇到停止标识停止
            if self.stop_flag:
                break
            try:
                queue_data = self.queue.get(timeout=0.5)
                if isinstance(queue_data, str) and queue_data == 'STOP':
                    break
                image, sei_msg = queue_data

                if self.total_frame is not None and ori_frame_count >= self.total_frame:
                    break
                utc = 0

                frame_enable, ori_frame_count, target_frame_count, current_time_point = frame_rate_converter.update(utc)
                time_log2 = time_log3 = time_log1
                if frame_enable:
                    time_log2 = int(time.time() * 1000)
                    frame_image = self.image_loader(image)
                    yield from self._yield_data(frame_image=frame_image,
                                                src_frame_idx=ori_frame_count,
                                                src_frame_time=round(current_time_point),
                                                target_frame_idx=target_frame_count,
                                                sei_msg=sei_msg,
                                                skip_frame_infos=skip_frame_infos,
                                                extra_data={'frame_path': image if str(image) else None})
                    time_log3 = int(time.time() * 1000)
                    skip_frame_infos = []
                else:
                    skip_frame_infos.append({
                        'src_frame_idx': ori_frame_count,
                        'src_frame_time': current_time_point,
                        'target_frame_idx': target_frame_count,
                        'sei': sei_msg,
                    })
                if self.tmp_logger:
                    log_mark = "OKK" if time_log3 - utc < self.time_log_delay_threshold else "BAD"
                    self.tmp_logger.info(
                        f'SDTLOG|{frame_enable}|{log_mark}|sei:{sei_msg}|ofidx:{ori_frame_count}|tfidx:{target_frame_count}|time1:{time_log1}|time2:{time_log2}|time3:{time_log3}|decoder:{time_log2 - time_log1}|model:{time_log3 - time_log2}|delay:{time_log3 - utc}')
            except queue.Empty:
                continue


if __name__ == '__main__':
    from aabd.base.log_setting import get_set_once_logger
    from aabd.base.path_util import to_absolute_path_str
    import os

    os.environ['PROJECT_ROOT'] = os.path.abspath("../")
    logger1 = get_set_once_logger(log_type=['console'])
    with CVStreamDecoder(to_absolute_path_str('files/111.mp4'), start=1000, end=3000, max_fps=30, logger=logger1,
                         frame_type="numpy_bgr", control_type='time') as (
            decoder,
            _):
        for frame in decoder:
            cv2.imwrite(f'images/{frame["src_frame_idx"]}.png', frame['frame'])
            frame['frame'] = None
            logger1.info(frame)
