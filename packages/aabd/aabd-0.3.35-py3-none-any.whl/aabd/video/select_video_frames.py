import os
import time

import cv2
import random
from tqdm import tqdm
import numpy as np

from aabd.video.cv_tools import video_info

import os
from pathlib import Path
from typing import List, Union, Set


def get_video_paths(paths: Union[str, List[str]]) -> List[str]:
    """
    将paths转为视频路径集合
    1. 如果paths 是str则为一个路径，如果是list说明是路径集合
    2. 如果路径是文件夹则获取文件夹内的视频文件
    3. 如果路径为视频文件则作为返回的一个
    4. 如果路径为txt则读取每行数据，每行数据也是一个路径，再参照1、2、3、4处理
    :param paths: 路径（字符串或字符串列表）
    :return: 视频路径集合（去重后的绝对路径集合）
    """
    video_extensions = {
        '.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv',
        '.webm', '.m4v', '.mpg', '.mpeg', '.3gp', '.rmvb'
    }

    def is_video_file(path: Path) -> bool:
        return path.is_file() and path.suffix.lower() in video_extensions

    def process_path(path_str: str, seen_txt: set) -> Set[str]:
        path = Path(path_str).resolve()
        result = set()

        # 防止txt文件循环引用
        if path.suffix.lower() == '.txt':
            if path in seen_txt:
                return result
            seen_txt.add(path)

            if path.exists():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):  # 忽略空行和#开头的注释行
                                result.update(process_path(line, seen_txt.copy()))
                except Exception as e:
                    print(f"Warning: Could not read txt file {path}: {e}")
            return result

        if path.is_dir():
            for item in path.rglob('*'):
                if is_video_file(item):
                    result.add(str(item))
        elif is_video_file(path):
            result.add(str(path))

        return result

    # 处理输入
    if isinstance(paths, str):
        paths = [paths]
    elif not isinstance(paths, (list, tuple)):
        raise TypeError("paths must be a string or a list of strings")

    all_paths = set()
    seen_txt_files = set()  # 用于跟踪已处理的txt文件，防止无限递归

    for p in paths:
        if isinstance(p, str):
            all_paths.update(process_path(p, seen_txt_files.copy()))
        else:
            raise TypeError(f"Path must be a string, got {type(p)}")

    return list(all_paths)


def dense_even_gap_frames(video_urls, output_root='images', gap=50, sub_folder=True):
    """
    从视频中稠密的均匀的抽取视频帧，指定间隔帧（稠密抽取：使用连续读取方式）
    :param video_urls: 视频的地址或http链接,如果是str就是单个视频路径,如果是list就是多个路径
    :param output_root: 输出的根路径,输出的文件名格式{视频名称}_{帧号}.png
    :param gap: 间隔多久抽一帧
    :param sub_folder: 是否将一个视频的图片放到一个文件夹内
    """
    video_urls = get_video_paths(video_urls)

    for video_path in tqdm(video_urls, desc="Processing videos", unit="video"):
        try:
            w, h, fps, frame_count = video_info(video_path)
            if frame_count <= 0:
                print(f"Warning: Video {video_path} has no frames, skipped.")
                continue
        except Exception as e:
            print(f"Error processing video {video_path}: {e}")
            continue

        video_name = os.path.splitext(os.path.basename(video_path))[0]
        if sub_folder:
            output_dir = os.path.join(output_root, video_name)
        else:
            output_dir = output_root
        os.makedirs(output_dir, exist_ok=True)

        # 计算要抽取的帧号列表 (0, gap, 2*gap, ...)
        frames_to_extract = set(range(0, frame_count, gap))

        # 使用连续读取方式（稠密抽取）
        cap = cv2.VideoCapture(video_path)
        frame_index = 0
        for ret, frame in tqdm(iter(cap.read, (False, None)), total=frame_count,
                               desc=f"Extracting frames for {video_name}", unit="frame"):
            if not ret:
                break
            if frame_index in frames_to_extract:
                output_path = os.path.join(output_dir, f"{video_name}_{frame_index}.png")
                cv2.imwrite(output_path, frame)
            frame_index += 1
        cap.release()


def dense_even_total_frames(video_urls, output_root, total=50, sub_folder=True):
    """
    从视频中稠密的均匀的抽取指定数量的视频帧（稠密抽取：使用连续读取方式）
    :param video_urls: 视频的地址或http链接,如果是str就是单个视频路径,如果是list就是多个路径
    :param output_root: 输出的根路径,输出的文件名格式{视频名称}_{帧号}.png
    :param total: 一共需要多少帧
    :param sub_folder: 是否将一个视频的图片放到一个文件夹内
    """
    video_urls = get_video_paths(video_urls)

    for video_path in tqdm(video_urls, desc="Processing videos", unit="video"):
        try:
            w, h, fps, frame_count = video_info(video_path)
            if frame_count <= 0:
                print(f"Warning: Video {video_path} has no frames, skipped.")
                continue
        except Exception as e:
            print(f"Error processing video {video_path}: {e}")
            continue

        video_name = os.path.splitext(os.path.basename(video_path))[0]
        if sub_folder:
            output_dir = os.path.join(output_root, video_name)
        else:
            output_dir = output_root
        os.makedirs(output_dir, exist_ok=True)

        # 计算均匀分布的帧号
        if total >= frame_count:
            total = frame_count
            frames_to_extract = set(range(frame_count))
        else:
            # 计算均匀间隔
            step = frame_count / total
            frames_to_extract = {int(i * step) for i in range(total)}
            frames_to_extract = {min(f, frame_count - 1) for f in frames_to_extract}

        # 使用连续读取方式（稠密抽取）
        cap = cv2.VideoCapture(video_path)
        frame_index = 0
        for ret, frame in tqdm(iter(cap.read, (False, None)), total=frame_count,
                               desc=f"Extracting frames for {video_name}", unit="frame"):
            if not ret:
                break
            if frame_index in frames_to_extract:
                output_path = os.path.join(output_dir, f"{video_name}_{frame_index}.png")
                cv2.imwrite(output_path, frame)
            frame_index += 1
        cap.release()


def dense_random_frames(video_urls, output_root='images', total=50, sub_folder=True):
    """
    从视频中稠密的随机抽取指定数量的视频帧（稠密抽取：使用连续读取方式）
    :param video_urls: 视频的地址或http链接,如果是str就是单个视频路径,如果是list就是多个路径
    :param output_root: 输出的根路径,输出的文件名格式{视频名称}_{帧号}.png
    :param total: 一共需要多少帧
    :param sub_folder: 是否将一个视频的图片放到一个文件夹内
    """
    video_urls = get_video_paths(video_urls)

    for video_path in tqdm(video_urls, desc="Processing videos", unit="video"):
        try:
            w, h, fps, frame_count = video_info(video_path)
            if frame_count <= 0:
                print(f"Warning: Video {video_path} has no frames, skipped.")
                continue
        except Exception as e:
            print(f"Error processing video {video_path}: {e}")
            continue

        video_name = os.path.splitext(os.path.basename(video_path))[0]
        if sub_folder:
            output_dir = os.path.join(output_root, video_name)
        else:
            output_dir = output_root
        os.makedirs(output_dir, exist_ok=True)

        # 确保total不超过帧数
        if total >= frame_count:
            total = frame_count

        # 生成不重复的随机帧号
        frames_to_extract = set(random.sample(range(frame_count), total))

        # 使用连续读取方式（稠密抽取）
        cap = cv2.VideoCapture(video_path)
        frame_index = 0
        for ret, frame in tqdm(iter(cap.read, (False, None)), total=frame_count,
                               desc=f"Extracting frames for {video_name}", unit="frame"):
            if not ret:
                break
            if frame_index in frames_to_extract:
                output_path = os.path.join(output_dir, f"{video_name}_{frame_index}.png")
                cv2.imwrite(output_path, frame)
            frame_index += 1
        cap.release()


def sparse_even_total_frames(video_urls, output_root='images', total=50, sub_folder=True):
    """
    从视频中稀疏的均匀的抽取指定数量的视频帧（稀疏抽取：使用跳转方式）
    :param video_urls: 视频的地址或http链接,如果是str就是单个视频路径,如果是list就是多个路径
    :param output_root: 输出的根路径,输出的文件名格式{视频名称}_{帧号}.png
    :param total: 一共需要多少帧
    :param sub_folder: 是否将一个视频的图片放到一个文件夹内
    """
    video_urls = get_video_paths(video_urls)

    for video_path in tqdm(video_urls, desc="Processing videos", unit="video"):
        try:
            w, h, fps, frame_count = video_info(video_path)
            if frame_count <= 0:
                print(f"Warning: Video {video_path} has no frames, skipped.")
                continue
        except Exception as e:
            print(f"Error processing video {video_path}: {e}")
            continue

        video_name = os.path.splitext(os.path.basename(video_path))[0]
        if sub_folder:
            output_dir = os.path.join(output_root, video_name)
        else:
            output_dir = output_root
        os.makedirs(output_dir, exist_ok=True)

        # 确保total不超过帧数
        if total >= frame_count:
            total = frame_count

        # 计算均匀分布的帧号
        frames_to_extract = [int(i * frame_count / total) for i in range(total)]
        frames_to_extract = [min(f, frame_count - 1) for f in frames_to_extract]
        frames_to_extract.sort()  # 按顺序跳转提高效率

        # 使用跳转方式（稀疏抽取）
        cap = cv2.VideoCapture(video_path)
        for idx, frame_index in tqdm(enumerate(frames_to_extract), total=len(frames_to_extract),
                                     desc=f"Extracting frames for {video_name}", unit="frame"):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ret, frame = cap.read()
            if ret:
                output_path = os.path.join(output_dir, f"{video_name}_{frame_index}.png")
                cv2.imwrite(output_path, frame)
            else:
                print(f"Warning: Failed to read frame {frame_index} from {video_path}")
        cap.release()


def sparse_random_frames(video_urls, output_root='images', total=50, sub_folder=True):
    """
    从视频中稀疏的随机抽取某几帧（稀疏抽取：使用跳转方式）
    :param video_urls: 视频的地址或http链接,如果是str就是单个视频路径,如果是list就是多个路径
    :param output_root: 输出的根路径,输出的文件名格式{视频名称}_{帧号}.png
    :param total: 一共需要多少帧
    :param sub_folder: 是否将一个视频的图片放到一个文件夹内
    """
    video_urls = get_video_paths(video_urls)

    for video_path in tqdm(video_urls, desc="Processing videos", unit="video"):
        try:
            w, h, fps, frame_count = video_info(video_path)
            if frame_count <= 0:
                print(f"Warning: Video {video_path} has no frames, skipped.")
                continue
        except Exception as e:
            print(f"Error processing video {video_path}: {e}")
            continue

        video_name = os.path.splitext(os.path.basename(video_path))[0]
        if sub_folder:
            output_dir = os.path.join(output_root, video_name)
        else:
            output_dir = output_root
        os.makedirs(output_dir, exist_ok=True)

        # 确保total不超过帧数
        if total >= frame_count:
            total = frame_count

        # 生成不重复的随机帧号
        frames_to_extract = random.sample(range(frame_count), total)
        frames_to_extract.sort()  # 按顺序跳转提高效率

        # 使用跳转方式（稀疏抽取）
        cap = cv2.VideoCapture(video_path)
        for idx, frame_index in tqdm(enumerate(frames_to_extract), total=len(frames_to_extract),
                                     desc=f"Extracting frames for {video_name}", unit="frame"):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ret, frame = cap.read()
            if ret:
                output_path = os.path.join(output_dir, f"{video_name}_{frame_index}.png")
                cv2.imwrite(output_path, frame)
            else:
                print(f"Warning: Failed to read frame {frame_index} from {video_path}")
        cap.release()


def sparse_even_gap_frames(video_urls, output_root='images', gap=50, sub_folder=True):
    """
    从视频中稀疏的随机抽取某几帧,间隔均匀（稀疏抽取：使用跳转方式）
    :param video_urls: 视频的地址或http链接,如果是str就是单个视频路径,如果是list就是多个路径
    :param output_root: 输出的根路径,输出的文件名格式{视频名称}_{帧号}.png
    :param gap: 间隔帧数
    :param sub_folder: 是否将一个视频的图片放到一个文件夹内
    """
    video_urls = get_video_paths(video_urls)

    for video_path in tqdm(video_urls, desc="Processing videos", unit="video"):
        try:
            w, h, fps, frame_count = video_info(video_path)
            if frame_count <= 0:
                print(f"Warning: Video {video_path} has no frames, skipped.")
                continue
        except Exception as e:
            print(f"Error processing video {video_path}: {e}")
            continue

        video_name = os.path.splitext(os.path.basename(video_path))[0]
        if sub_folder:
            output_dir = os.path.join(output_root, video_name)
        else:
            output_dir = output_root
        os.makedirs(output_dir, exist_ok=True)

        # 计算实际抽取的帧数
        frames_to_extract = list(range(0, frame_count, gap))
        frames_to_extract = [min(f, frame_count - 1) for f in frames_to_extract]
        frames_to_extract.sort()  # 按顺序跳转提高效率

        # 使用跳转方式（稀疏抽取）
        cap = cv2.VideoCapture(video_path)
        for idx, frame_index in tqdm(enumerate(frames_to_extract), total=len(frames_to_extract),
                                     desc=f"Extracting frames for {video_name}", unit="frame"):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ret, frame = cap.read()
            if ret:
                output_path = os.path.join(output_dir, f"{video_name}_{frame_index}.png")
                cv2.imwrite(output_path, frame)
            else:
                print(f"Warning: Failed to read frame {frame_index} from {video_path}")
        cap.release()


def select_frames(video_urls, output_root='images', total=None, gap=None, random_frame=False, sub_folder=True):
    """
    自动选择方式抽帧, 通过调用其他函数实现
    :param video_urls: 视频的地址或http链接,如果是str就是单个视频路径,如果是list就是多个路径
    :param output_root: 输出的根路径,输出的文件名格式{视频名称}_{帧号}.png
    :param total: 一共需要多少帧
    :param gap: 间隔帧数
    :param random_frame: 是否采用随机，否则为均匀
    :param sub_folder: 是否将一个视频的图片放到一个文件夹内
    """
    video_urls = get_video_paths(video_urls)

    # 检查参数
    if total is None and gap is None:
        raise ValueError("Either total or gap must be specified")
    if gap is not None and random_frame:
        raise ValueError("When using gap, random must be False")

    for video_path in tqdm(video_urls, desc="Processing videos", unit="video"):
        try:
            w, h, fps, frame_count = video_info(video_path)
            if frame_count <= 0:
                print(f"Warning: Video {video_path} has no frames, skipped.")
                continue
        except Exception as e:
            print(f"Error processing video {video_path}: {e}")
            continue

        # 根据参数选择调用的函数
        if total is not None:
            # 计算实际抽取帧数
            actual_frames = min(total, frame_count)

            # 判断稠密/稀疏
            if actual_frames > frame_count * 0.04:  # 稠密
                if random_frame:
                    dense_random_frames(video_path, output_root, total, sub_folder)
                else:
                    dense_even_total_frames(video_path, output_root, total, sub_folder)
            else:  # 稀疏
                if random_frame:
                    sparse_random_frames(video_path, output_root, total, sub_folder)
                else:
                    sparse_even_total_frames(video_path, output_root, total, sub_folder)
        elif gap is not None:
            # 计算实际抽取帧数
            actual_frames = (frame_count + gap - 1) // gap

            # 判断稠密/稀疏
            if actual_frames > frame_count * 0.04:  # 稠密
                dense_even_gap_frames(video_path, output_root, gap, sub_folder)
            else:  # 稀疏
                sparse_even_gap_frames(video_path, output_root, gap, sub_folder)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Extract frames from videos')
    parser.add_argument('--video_urls', type=str, nargs='+', required=True,
                        help='Video file paths or URLs')
    parser.add_argument('--output_root', type=str, default='images',
                        help='Root directory for output frames')
    parser.add_argument('--total', type=int, default=None,
                        help='Number of frames to extract (used with --random)')
    parser.add_argument('--gap', type=int, default=None,
                        help='Frame gap between extracted frames (used without --random)')
    parser.add_argument('--random', action='store_true',
                        help='Use random frame selection instead of uniform')
    parser.add_argument('--sub_folder', action='store_true',
                        help='Classify video frames using folders')
    args = parser.parse_args()

    # 确保至少指定total或gap
    if args.total is None and args.gap is None:
        parser.error("Either --total or --gap must be specified")

    select_frames(
        video_urls=args.video_urls,
        output_root=args.output_root,
        total=args.total,
        gap=args.gap,
        random_frame=args.random,
    )
