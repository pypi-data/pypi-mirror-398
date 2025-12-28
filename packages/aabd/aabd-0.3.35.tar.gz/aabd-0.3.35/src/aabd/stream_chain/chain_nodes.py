import logging
import queue
from abc import ABC, abstractmethod
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from dataclasses import dataclass
from typing import TypeVar, Generic
import re
import time
from typing import Any

def_logger = logging.getLogger('chain_nodes')

T = TypeVar('T')


@dataclass
class Message(Generic[T]):
    seq: int
    timestamp: datetime
    type: str
    header: dict
    payload: T


class MessageMaker:
    def __init__(self):
        self.seq = 0

    def data_message(self, header=None, payload=None):
        if header is None:
            header = {}
        if payload is None:
            payload = {}
        message = Message(seq=self.seq, timestamp=datetime.now(), header=header, type='data', payload=payload)
        self.seq += 1
        return message

    def stop_message(self):
        message = Message(seq=self.seq, timestamp=datetime.now(), type='stop', header={}, payload=None)
        self.seq += 1
        return message


def time_decorator(func):
    """装饰器：记录方法执行时间并打印信息"""

    def wrapper(self, messages: Any):
        start_time = time.time()
        try:
            result = func(self, messages)
        finally:
            elapsed = time.time() - start_time
            # 打印 self.name、from_node.name 和耗时
            self.logger.debug(f"NODE_USE_TIME {self.name} use time: {elapsed:.4f}s")
        return result

    return wrapper


class NodeMeta(type(ABC)):
    """元类：在子类定义时自动装饰 input 方法"""

    def __new__(cls, name, bases, attrs):
        new_class = super().__new__(cls, name, bases, attrs)
        # 检查子类是否实现了 input 方法
        if 'process' in attrs:
            original_method = attrs['process']
            # 应用装饰器
            decorated_method = time_decorator(original_method)
            setattr(new_class, 'process', decorated_method)
        return new_class


class Node(ABC, metaclass=NodeMeta):

    def __init__(self, context=None, name=None, logger=def_logger, **kwargs):
        self.name = name or self.__class__.__name__
        self.description = self.name
        self.output_nodes = set()
        self.input_nodes = set()
        self.context = context
        self.logger = logger
        self.exception_callback = lambda key, node, message, e: None
        self.event_bus = None
        super().__init__(**kwargs)

    @abstractmethod
    def input(self, message, from_node: str):
        pass

    def registry_output(self, node):
        node.registry_input(self)
        self.output_nodes.add(node)
        return self

    def registry_input(self, node):
        self.input_nodes.add(node)

    def set_context(self, context):
        self.context = context


class SingleInputNode(Node):
    def __init__(self, context=None, name=None, enable=True, logger=def_logger, **kwargs):
        name = name or self.__class__.__name__
        super().__init__(context, name, logger=logger)
        self.enable = enable

    def input(self, message: Message, from_node: str):
        if self.enable is False:
            for output_node in self.output_nodes:
                output_node.input(message, self.name)
            return
        if message.type == 'stop':
            self.stop()
            for out_node in self.output_nodes:
                self.logger.debug(
                    f'NODE_DATA_STREAM [{self.name}-->{out_node.name}] {message.seq:06d} {message.timestamp}')
                try:
                    out_node.input(message, self.name)
                except Exception as e:
                    self.exception_callback(f'NODE_{self.name}', self, message, e)
                    self.logger.exception(f'{self.name} process error')
        else:
            try:
                self.process([message])
            except Exception as e:
                self.exception_callback(f'NODE_{self.name}', self, message, e)
                self.logger.exception(f'{self.name} process error')
            for out_node in self.output_nodes:
                self.logger.debug(
                    f'NODE_DATA_STREAM [{self.name}-->{out_node.name}] {message.seq:06d} {message.timestamp}')
                try:
                    out_node.input(message, self.name)
                except Exception as e:
                    self.exception_callback(f'NODE_{self.name}', self, message, e)
                    self.logger.exception(f'{self.name} process error')
                self.logger.debug(
                    f'NODE_DATA_STREAM END [{self.name}-->{out_node.name}] {message.seq:06d} {message.timestamp}')
    @abstractmethod
    def process(self, messages: list[Message]):
        pass

    def stop(self):
        pass


class WithHistoryMessageNode(Node):
    def __init__(self, context=None, name=None, history_len=1, enable=True, logger=def_logger, **kwargs):
        name = name or self.__class__.__name__
        super().__init__(context, name, logger=logger)
        self.history_len = history_len
        self.history_queue = deque(maxlen=history_len)
        self.enable = enable

    def input(self, message: Message, from_node: str):
        if self.enable is False:
            for output_node in self.output_nodes:
                output_node.input(message, self.name)
            return
        if message.type == 'stop':
            self.stop()
            self.history_queue.clear()
            for out_node in self.output_nodes:
                self.logger.debug(
                    f'NODE_DATA_STREAM [{self.name}-->{out_node.name}] {message.seq:06d} {message.timestamp}')
                try:
                    out_node.input(message, self.name)
                except Exception as e:
                    self.exception_callback(f'NODE_{self.name}', self, message, e)
                    self.logger.exception(f'{self.name} process error')
        else:
            self.process([message])
            self.history_queue.append(message)
            for out_node in self.output_nodes:
                self.logger.debug(
                    f'NODE_DATA_STREAM [{self.name}-->{out_node.name}] {message.seq:06d} {message.timestamp}')
                try:
                    out_node.input(message, self.name)
                except Exception as e:
                    self.exception_callback(f'NODE_{self.name}', self, message, e)
                    self.logger.exception(f'{self.name} process error')

    @abstractmethod
    def process(self, messages: list[Message]):
        pass

    @property
    def history_messages(self):
        return list(self.history_queue)

    def stop(self):
        pass

class BoundedThreadPool:
    def __init__(self, max_workers: int, max_queue_size: int):
        import threading
        self.task_queue = queue.Queue(maxsize=max_queue_size)
        self.threads = []
        self._shutdown = False

        for _ in range(max_workers):
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()
            self.threads.append(t)

    def _worker(self):
        while True:
            try:
                task = self.task_queue.get(timeout=0.5)  # 避免永久阻塞，便于 shutdown
                if task is None:
                    break
                func, args, kwargs, future = task
                try:
                    result = func(*args, **kwargs)
                    future.set_result(result)
                except Exception as e:
                    future.set_exception(e)
                finally:
                    self.task_queue.task_done()
            except queue.Empty:
                continue

    def submit(self, fn, *args, **kwargs):
        from concurrent.futures import Future
        if self._shutdown:
            raise RuntimeError("Cannot submit after shutdown")
        future = Future()
        # 这里会阻塞，直到队列有空位！
        self.task_queue.put((fn, args, kwargs, future))
        return future

    def shutdown(self, wait=True):
        self._shutdown = True
        if wait:
            for _ in self.threads:
                self.task_queue.put(None)  # poison pill
            for t in self.threads:
                t.join()
class ThreadSingleInputNode(Node):
    def __init__(self, context=None, name=None, pool_size=5, max_workers=5, logger=def_logger, **kwargs):
        name = name or self.__class__.__name__
        super().__init__(context, name, logger=logger)
        self.thread_pool = BoundedThreadPool(max_workers=max_workers, max_queue_size=pool_size)
        # self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        # self._work_queue = queue.Queue(maxsize=pool_size)
        # self.thread_pool._work_queue = self._work_queue
        self.last_future = None

    def input(self, message: Message, from_node: str):
        if message.type == 'stop':
            self.thread_pool.shutdown(wait=True)
            for out_node in self.output_nodes:
                self.logger.debug(
                    f'NODE_DATA_STREAM [{self.name}-->{out_node.name}] {message.seq:06d} {message.timestamp}')
                try:
                    out_node.input(message, self.name)
                except Exception as e:
                    self.exception_callback(f'NODE_{self.name}', self, message, e)
                    self.logger.exception(f'{self.name} process error')
                self.logger.debug(
                    f'NODE_DATA_STREAM END [{self.name}-->{out_node.name}] {message.seq:06d} {message.timestamp}')
        else:
            def post_process():
                for out_node in self.output_nodes:
                    self.logger.debug(
                        f'NODE_DATA_STREAM [{self.name}-->{out_node.name}] {message.seq:06d} {message.timestamp}')
                    try:
                        out_node.input(message, self.name)
                    except Exception as e:
                        self.exception_callback(f'NODE_{self.name}', self, message, e)
                        self.logger.exception(f'{self.name} process error')
                    self.logger.debug(
                        f'NODE_DATA_STREAM END [{self.name}-->{out_node.name}] {message.seq:06d} {message.timestamp}')

            self.last_future = self.thread_pool.submit(self.thread_process, message, self.last_future, post_process)

    def thread_process(self, message: Message, future, func):
        try:
            self.process([message])
        except Exception as e:
            self.exception_callback(f'NODE_{self.name}', self, message, e)
            self.logger.exception('')
        if future is not None:
            future.result()
        func()
    @abstractmethod
    def process(self, messages: list[Message]):
        pass


class MultipleInputNode(Node):

    def __init__(self, context=None, name=None, logger=def_logger, **kwargs):
        name = name or self.__class__.__name__
        super().__init__(context, name, logger=logger)
        self.inputs_seqs_map = {}
        self.current_seq = 0
        self.messages_map = {}

    def input(self, message: Message, from_node: str):
        self.inputs_seqs_map[from_node].add(message.seq)
        self.messages_map[message.seq] = message
        if all(self.current_seq in input_seqs for input_seqs in self.inputs_seqs_map.values()):
            message_out = self.messages_map.pop(self.current_seq)
            try:
                self.process([message_out])
            except Exception as e:
                self.exception_callback(f'NODE_{self.name}', self, message, e)
                self.logger.exception(f'{self.name} process error')
            for out_node in self.output_nodes:
                self.logger.debug(
                    f'NODE_DATA_STREAM [{self.name}-->{out_node.name}] {message_out.seq:06d} {message_out.timestamp}')
                try:
                    out_node.input(message_out, self.name)
                except Exception as e:
                    self.exception_callback(f'NODE_{self.name}', self, message, e)
                    self.logger.exception(f'{self.name} process error')
            for input_seqs in self.inputs_seqs_map.values():
                input_seqs.remove(self.current_seq)
            self.current_seq += 1

    def registry_input(self, node):
        self.inputs_seqs_map[node.name] = set()
        super().registry_input(node)

    def process(self, messages: list[Message]):
        pass


class DelayedNode(Node):
    def __init__(self, context=None, name=None, delay_len=10, only_full_process=False, enable=True, logger=def_logger,
                 **kwargs):
        name = name or self.__class__.__name__
        super().__init__(context, name, logger=logger)
        self.delay_len = delay_len
        self.delay_queue = deque(maxlen=delay_len)
        #  首次处理延迟
        self.only_full_process = only_full_process
        self.enable = enable

    def input(self, message: Message, from_node: str):
        if self.enable is False:
            for output_node in self.output_nodes:
                output_node.input(message, self.name)
            return
        if message.type == 'stop':
            try:
                self.stop(list(self.delay_queue))
            except Exception as e:
                self.exception_callback(f'NODE_{self.name}', self, message, e)
                self.logger.exception(f'{self.name} process error')
            while len(self.delay_queue) > 0:
                message_out = self.delay_queue.popleft()
                for output_node in self.output_nodes:
                    self.logger.debug(
                        f'NODE_DATA_STREAM [{self.name}-->{output_node.name}] {message_out.seq:06d} {message_out.timestamp}')
                    try:
                        output_node.input(message_out, self.name)
                    except Exception as e:
                        self.exception_callback(f'NODE_{self.name}', self, message, e)
                        self.logger.exception(f'{self.name} process error')
            # for output_node in self.output_nodes:
            #     try:
            #         output_node.input(message, self.name)
            #     except:
            #         self.logger.exception(f'{self.name} process error')
        else:
            self.delay_queue.append(message)
            try:
                if not self.only_full_process or len(self.delay_queue) == self.delay_len:
                    self.process(list(self.delay_queue))
            except Exception as e:
                self.exception_callback(f'NODE_{self.name}', self, message, e)
                self.logger.exception(f'{self.name} process error')
            if len(self.delay_queue) == self.delay_len:
                message_out = self.delay_queue.popleft()
                for output_node in self.output_nodes:
                    self.logger.debug(
                        f'NODE_DATA_STREAM [{self.name}-->{output_node.name}] {message_out.seq:06d} {message_out.timestamp}')
                    try:
                        output_node.input(message_out, self.name)
                    except Exception as e:
                        self.exception_callback(f'NODE_{self.name}', self, message, e)
                        self.logger.exception(f'{self.name} process error')

    def process(self, messages: list[Message]):
        pass

    def stop(self, messages: list[Message]):
        pass


class BatchNode(Node):

    def __init__(self, context=None, name=None, batch_size=10, logger=def_logger, **kwargs):
        name = name or self.__class__.__name__
        super().__init__(context, name, logger=logger)
        self.batch_size = batch_size
        self.data = []

    def input(self, message, from_node: str):
        if message.type == 'stop':
            if len(self.data) > 0:
                try:
                    self.process(self.data)
                except Exception as e:
                    self.exception_callback(f'NODE_{self.name}', self, message, e)
                    self.logger.exception(f'{self.name} process error')
        else:
            self.data.append(message)
            if len(self.data) == self.batch_size:
                try:
                    self.process(self.data)
                except Exception as e:
                    self.exception_callback(f'NODE_{self.name}', self, message, e)
                    self.logger.exception(f'{self.name} process error')
            else:
                return

        for message_out in self.data:
            for output_node in self.output_nodes:
                self.logger.debug(
                    f'NODE_DATA_STREAM [{self.name}-->{output_node.name}] {message_out.seq:06d} {message_out.timestamp}')
                try:
                    output_node.input(message_out, self.name)
                except Exception as e:
                    self.exception_callback(f'NODE_{self.name}', self, message, e)
                    self.logger.exception(f'{self.name} process error')
        self.data = []

        if message.type == 'stop':
            for output_node in self.output_nodes:
                output_node.input(message, self.name)

    def process(self, messages: list[Message]):
        pass

    def stop(self):
        pass


class MultiFunctionNode(Node):

    def __init__(self, context=None, name=None, delay_len=1, history_len=1, only_full_process=False,
                 one_by_one_stop=False, enable=True, logger=def_logger, **kwargs):
        name = name or self.__class__.__name__
        super().__init__(context, name, logger=logger)
        self.delay_len = delay_len
        self.delay_queue = deque(maxlen=delay_len)
        self.only_full_process = only_full_process
        self.history_len = history_len
        self.history_queue = deque(maxlen=history_len)
        self.one_by_one_stop = one_by_one_stop
        self.segment_flag = '-1'  # yes no
        self.enable = enable

    def input(self, message, from_node: str):
        if self.enable is False:
            for output_node in self.output_nodes:
                output_node.input(message, self.name)
            return
        if message.type == 'stop':
            try:
                if len(self.delay_queue) > 0:
                    if self.one_by_one_stop:
                        while len(self.delay_queue) > 0:
                            message_out = self.delay_queue.popleft()
                            for output_node in self.output_nodes:
                                self.logger.debug(
                                    f'NODE_DATA_STREAM [{self.name}-->{output_node.name}] {message_out.seq:06d} {message_out.timestamp}')
                                try:
                                    output_node.input(message_out, self.name)
                                    self.history_queue.append(message_out)
                                except Exception as e:
                                    self.exception_callback(f'NODE_{self.name}', self, message, e)
                                    self.logger.exception(f'{self.name} process error')
                    try:
                        self.segment_stop(list(self.delay_queue))
                    except Exception as e:
                        self.exception_callback(f'NODE_{self.name}', self, message, e)
                        self.logger.exception(f'{self.name} process error')
                self.stop(list(self.delay_queue))
                while len(self.delay_queue) > 0:
                    message_out = self.delay_queue.popleft()
                    for output_node in self.output_nodes:
                        self.logger.debug(
                            f'NODE_DATA_STREAM [{self.name}-->{output_node.name}] {message_out.seq:06d} {message_out.timestamp}')
                        try:
                            output_node.input(message_out, self.name)
                        except Exception as e:
                            self.exception_callback(f'NODE_{self.name}', self, message, e)
                            self.logger.exception(f'{self.name} process error')
            except Exception as e:
                self.exception_callback(f'NODE_{self.name}', self, message, e)
                self.logger.exception(f'{self.name} process error')
            while len(self.delay_queue) > 0:
                message_out = self.delay_queue.popleft()
                for output_node in self.output_nodes:
                    self.logger.debug(
                        f'NODE_DATA_STREAM [{self.name}-->{output_node.name}] {message_out.seq:06d} {message_out.timestamp}')
                    try:
                        output_node.input(message_out, self.name)
                        self.history_queue.append(message_out)
                    except Exception as e:
                        self.exception_callback(f'NODE_{self.name}', self, message, e)
                        self.logger.exception(f'{self.name} process error')
            self.history_queue.clear()
            for output_node in self.output_nodes:
                self.logger.debug(
                    f'NODE_DATA_STREAM [{self.name}-->{output_node.name}] {message.seq:06d} {message.timestamp}')
                try:
                    output_node.input(message, self.name)
                    self.history_queue.append(message)
                except Exception as e:
                    self.exception_callback(f'NODE_{self.name}', self, message, e)
                    self.logger.exception(f'{self.name} process error')
        else:
            if self.is_segment_message(message, None if len(self.history_messages) == 0 else self.history_messages[-1]):

                self.delay_queue.append(message)
                try:
                    if not self.only_full_process or len(self.delay_queue) == self.delay_len:
                        if self.segment_flag != 'yes':
                            self.segment_start()
                            self.segment_flag = 'yes'
                        out_number = self.process(list(self.delay_queue))
                        # 如果返回一个数字说明这些需要输出
                        if out_number is not None and out_number > 0:
                            for _ in range(out_number):
                                message_out = self.delay_queue.popleft()
                                for output_node in self.output_nodes:
                                    self.logger.debug(
                                        f'NODE_DATA_STREAM [{self.name}-->{output_node.name}] {message_out.seq:06d} {message_out.timestamp}')
                                    try:
                                        output_node.input(message_out, self.name)
                                        self.history_queue.append(message_out)
                                    except Exception as e:
                                        self.exception_callback(f'NODE_{self.name}', self, message, e)
                                        self.logger.exception(f'{self.name} process error')
                except Exception as e:
                    self.exception_callback(f'NODE_{self.name}', self, message, e)
                    self.logger.exception(f'{self.name} process error after Seq {message.seq} incoming')
                if len(self.delay_queue) == self.delay_len:
                    message_out = self.delay_queue.popleft()
                    for output_node in self.output_nodes:
                        self.logger.debug(
                            f'NODE_DATA_STREAM [{self.name}-->{output_node.name}] {message_out.seq:06d} {message_out.timestamp}')
                        try:
                            output_node.input(message_out, self.name)
                            self.history_queue.append(message_out)
                        except Exception as e:
                            self.exception_callback(f'NODE_{self.name}', self, message, e)
                            self.logger.exception(f'{self.name} process error')
            else:
                # 不符合条件的消息，直接输出
                # 如果有历史数据进行历史数据的处理
                if len(self.delay_queue) > 0:
                    if self.one_by_one_stop:
                        while len(self.delay_queue) > 0:
                            message_out = self.delay_queue.popleft()
                            for output_node in self.output_nodes:
                                self.logger.debug(
                                    f'NODE_DATA_STREAM [{self.name}-->{output_node.name}] {message_out.seq:06d} {message_out.timestamp}')
                                try:
                                    output_node.input(message_out, self.name)
                                    self.history_queue.append(message_out)
                                except Exception as e:
                                    self.exception_callback(f'NODE_{self.name}', self, message, e)
                                    self.logger.exception(f'{self.name} process error')
                    try:
                        self.segment_stop(list(self.delay_queue))
                    except Exception as e:
                        self.exception_callback(f'NODE_{self.name}', self, message, e)
                        self.logger.exception(f'{self.name} process error')
                # 不多余
                while len(self.delay_queue) > 0:
                    message_out = self.delay_queue.popleft()
                    for output_node in self.output_nodes:
                        self.logger.debug(
                            f'NODE_DATA_STREAM [{self.name}-->{output_node.name}] {message_out.seq:06d} {message_out.timestamp}')
                        try:
                            output_node.input(message_out, self.name)
                            self.history_queue.append(message_out)
                        except Exception as e:
                            self.exception_callback(f'NODE_{self.name}', self, message, e)
                            self.logger.exception(f'{self.name} process error')
                self.history_queue.clear()
                self.segment_flag = 'no'
                # 当前的消息直接送出
                for output_node in self.output_nodes:
                    self.logger.debug(
                        f'NODE_DATA_STREAM [{self.name}-->{output_node.name}] {message.seq:06d} {message.timestamp}')
                    try:
                        output_node.input(message, self.name)
                    except Exception as e:
                        self.exception_callback(f'NODE_{self.name}', self, message, e)
                        self.logger.exception(f'{self.name} process error')

    @abstractmethod
    def process(self, messages: list[Message]):
        pass

    def is_segment_message(self, message_new: Message, message_old: Message):
        return True

    def segment_start(self):
        pass

    def segment_stop(self, messages: list[Message]):
        pass

    def stop(self, messages: list[Message]):
        pass

    @property
    def history_messages(self):
        return list(self.history_queue)


class EventBus:
    def __init__(self):
        self._subscribers = {}  # topic -> [callbacks]

    def subscribe(self, topic, callback):
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(callback)

    def publish(self, topic, *args, **kwargs):
        if topic in self._subscribers:
            for callback in self._subscribers[topic]:
                callback(*args, **kwargs)


class NodesChain:

    def __init__(self, context=None, logger=def_logger, node_exception_callback=None):
        if context is None:
            self.context = {}
        self.message_maker = MessageMaker()
        self.logger = logger or def_logger
        self.root_node = self.build()
        self.node_exception_callback = node_exception_callback
        self.event_bus = EventBus()
        self.__set_context__(self.root_node)

    def build(self) -> Node:
        pass

    def input(self, data):
        start_time = time.time()
        if isinstance(data, Message):
            self.root_node.input(data, 'root')
        else:
            self.root_node.input(self.message_maker.data_message(data), 'root')
        self.logger.debug(f'CHAIN once use time: {time.time() - start_time:.3f}s')

    def stop(self):
        self.root_node.input(self.message_maker.stop_message(), 'root')

    def __set_context__(self, node: Node):
        node.set_context(self.context)
        node.logger = self.logger
        node.event_bus = self.event_bus
        if self.node_exception_callback is not None:
            node.exception_callback = self.node_exception_callback
        for out in node.output_nodes:
            self.__set_context__(out)

    # def __draw_node__(self, node: Node, dot):
    #     dot.node(node.name, node.name)
    #     for out in node.output_nodes:
    #         self.__draw_node__(out, dot)
    #         dot.edge(node.name, out.name)
    # def graph_image(self, file_path):
    #     from graphviz import Digraph
    #     dot = Digraph(comment='chain')
    #     self.__draw_node__(self.root_node, dot)
    #     dot.render(file_path,format=os.path.splitext(file_path)[1][1:], cleanup=True)
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


def split_node(s: str):
    match = re.match(r'^(\w+)\[(\S+)]$', s.strip())
    if match:
        prefix, chinese = match.groups()
        return (prefix, chinese)
    else:
        # 没有括号时，第二项使用原字符串不变
        return (s, s)


class MermaidNodesChain(NodesChain):

    def __init__(self, context=None, logger=def_logger, node_exception_callback=None):
        super().__init__(context=context, logger=logger, node_exception_callback=node_exception_callback)

    def build(self) -> Node:
        root_node, nodes_builder = self.nodes_builder()
        # nodes_map = dict({(node.name, node) for node in nodes})

        link_edges = self.link_edges()
        if isinstance(link_edges, str):
            lines = link_edges.strip().split('\n')
            edges = set()
            for line in lines:
                if "-->" not in line or line.strip().startswith('##') or line.strip().startswith('%%'):
                    continue
                nodes = line.strip().split('-->')
                nodes = [node.strip() for node in nodes if not node.strip().startswith("#")]
                # nodes = list(map(lambda x: re.sub(r'\[.*?]', '', x), nodes))
                nodes = list(map(split_node, nodes))
                edges.update([(k, v) for k, v in zip(nodes[:-1], nodes[1:])])
            link_edges = edges

        node_names = {}
        for from_node, to_node in link_edges:
            if isinstance(from_node, str):
                node_names[from_node.strip()] = from_node.strip()
            else:
                node_names[from_node[0]] = from_node[1]
            if isinstance(to_node, str):
                node_names[to_node.strip()] = to_node.strip()
            else:
                node_names[to_node[0]] = to_node[1]

        nodes_map = {}
        for node_name, node_description in node_names.items():
            nodes_map[node_name] = nodes_builder[node_name]()
            nodes_map[node_name].name = node_name
            nodes_map[node_name].description = node_description

        root_node = nodes_map[root_node]

        for from_node, to_node in link_edges:
            if isinstance(from_node, str):
                from_node = from_node.strip()
            else:
                from_node = from_node[0]
            if isinstance(to_node, str):
                to_node = to_node.strip()
            else:
                to_node = to_node[0]
            from_node, to_node = from_node.strip(), to_node.strip()
            from_node, to_node = nodes_map[from_node], nodes_map[to_node]
            from_node.registry_output(to_node)
        return root_node

    def nodes_builder(self):  # -> (str, map)
        pass

    def link_edges(self):  # -> set[tuple] | str
        pass


class NumberAdd(SingleInputNode):

    def __init__(self, context=None, name=None, num=0):
        self.num = num
        super().__init__(context=context, name=name)

    def process(self, message: Message):
        message.payload['data'] = message.payload['data'] + self.num


class PrintNode(SingleInputNode):

    def __init__(self, context=None, name='print'):
        super().__init__(context=context, name=name)

    def process(self, message: Message):
        print(message.payload)


class TestChain(NodesChain):

    def build(self) -> Node:
        add1 = NumberAdd(name='add_1', num=1)
        add5 = NumberAdd(name='add_5', num=5)
        print_str = PrintNode(name='print')

        add1.registry_output(add5)
        add5.registry_output(print_str)

        return add1


if __name__ == '__main__':
    from aabd.base.log_setting import set_logger

    set_logger('chain_nodes', log_level='DEBUG')
    chain = TestChain()
    # chain.graph_image('1.png')
    chain.input({'data': 1})
    chain.stop()
