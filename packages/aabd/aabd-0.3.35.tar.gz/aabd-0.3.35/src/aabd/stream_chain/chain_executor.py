import logging
from abc import abstractmethod
from threading import Thread

from .chain_nodes import NodesChain
from queue import Queue, Empty, Full

def_logger = logging.getLogger(__name__)


class ChainDataStream:
    def __init__(self, context=None, logger=def_logger, event_callback=None):
        self.context = context
        self.logger = logger or def_logger
        self.event_callback = event_callback
        if self.event_callback is None:
            self.event_callback = lambda level, key, message: None

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def next(self):
        pass

    def stop(self):
        pass

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def __next__(self):
        return self.next()

    def __iter__(self):
        return self


class ChainQueueDataStreamWrapper(ChainDataStream):
    def __init__(self, data_stream, context=None, logger=def_logger, event_callback=None, **kwargs):
        self.queue = Queue(maxsize=kwargs.get('chain_data_stream_queue_size', 300))
        self.task_stop = False
        self.data_stream = data_stream
        super().__init__(context=context, logger=logger, event_callback=event_callback)

    def start(self):

        def thread_func():
            try:
                with self.data_stream as stream:
                    for message_in in stream:
                        try:
                            self.queue.put(message_in, timeout=0.01, block=True)
                            # self.logger.warning(f'frame queue:{self.queue.qsize()}')
                        except Full:
                            self.event_callback('WARNING', 'FRAME_QUEUE_FULL', 'frame queue full')
                            self.logger.warning('frame queue full!!!')
            except:
                self.event_callback('ERROR', 'DATA_STREAM_ERROR', 'video to frame error')
                self.logger.exception('ChainDataStreamQueueWrapper error')
            finally:
                self.task_stop = True

        Thread(target=thread_func).start()

    def next(self):
        if not self.task_stop or self.queue.qsize() > 0:
            while not self.task_stop or self.queue.qsize() > 0:
                try:
                    data = self.queue.get(timeout=0.1)
                    pre_data = self.pre_process(data)
                    return pre_data
                except Empty:
                    pass
        raise StopIteration

    def stop(self):
        self.data_stream.stop()

    def pre_process(self, message_in):
        return message_in


class VideoFrameDataStream(ChainDataStream):

    def __init__(self, video_path, decoder='av', context=None, logger=def_logger, event_callback=None, **kwargs):
        self.decoder_name = decoder
        self.stream_decoder = None
        self.video_path = video_path
        self.kwargs = kwargs
        super().__init__(context=context, logger=logger or def_logger, event_callback=event_callback)
        self._init_decoder()

    def _init_decoder(self):
        if self.decoder_name == 'av' or self.decoder_name == 'ava':
            from .video2frames import AVAStreamDecoder
            self.stream_decoder = AVAStreamDecoder(self.video_path, **self.kwargs)
        elif self.decoder_name == 'avb':
            from .video2frames import AVBStreamDecoder
            self.stream_decoder = AVBStreamDecoder(self.video_path, **self.kwargs)
        elif self.decoder_name == 'avc':
            from .video2frames import AVCStreamDecoder
            self.stream_decoder = AVCStreamDecoder(self.video_path, **self.kwargs)
        elif self.decoder_name == 'cv':
            from .video2frames import CVStreamDecoder
            self.stream_decoder = CVStreamDecoder(self.video_path, **self.kwargs)
        elif self.decoder_name == 'sdk':
            from .video2frames import SDKStreamDecoder
            self.stream_decoder = SDKStreamDecoder(self.video_path, **self.kwargs)
        elif self.decoder_name == 'mock':
            from .video2frames import MockStreamDecoder
            self.stream_decoder = MockStreamDecoder(self.video_path, **self.kwargs)
        elif self.decoder_name == 'img':
            from .video2frames import ImageDecoder
            self.stream_decoder = ImageDecoder(self.video_path, **self.kwargs)
        elif self.decoder_name == 'audio':
            from .video2frames import AudioDecoder
            self.stream_decoder = AudioDecoder(self.video_path, **self.kwargs)
        elif self.decoder_name == 'qimg':
            from .video2frames import QueueImageDecoder
            self.stream_decoder = QueueImageDecoder(self.video_path, **self.kwargs)
        else:
            raise ValueError()

    def start(self):
        pass

    def next(self):
        return self.pre_process(next(self.stream_decoder))

    def stop(self):
        self.stream_decoder.stop()

    def __len__(self):
        return self.stream_decoder.__len__()

    def pre_process(self, message_in):
        return message_in


class VideoFrameQueueDataStream(ChainQueueDataStreamWrapper):
    def __init__(self, video_path, decoder='av', context=None, logger=def_logger, event_callback=None, **kwargs):
        self.decoder_name = decoder
        self.stream_decoder = None
        self.data_stream = VideoFrameDataStream(video_path, decoder, context, logger or def_logger, event_callback,
                                                **kwargs)
        self.video_path = video_path
        self.kwargs = kwargs
        super().__init__(self.data_stream, context=context, logger=logger or def_logger,
                         event_callback=event_callback, **kwargs)


class ChainExecutor:
    def __init__(self, data_stream: ChainDataStream, chain: NodesChain, logger=def_logger):
        self.data_stream = data_stream
        self.chain = chain
        self.logger = logger or def_logger

    def start(self):
        with self.data_stream as stream:
            for message_in in stream:
                self.chain.input(message_in)
        self.chain.stop()

    def stop(self):
        self.data_stream.stop()
