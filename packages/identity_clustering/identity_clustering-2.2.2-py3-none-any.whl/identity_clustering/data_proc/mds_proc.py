import os
import sys
import time
from identity_clustering.cluster import detect_faces
from identity_clustering.utils import extract_crops, _get_frames, _get_crop
from streaming import MDSWriter
from typing import Dict, List, Literal, Optional
import multiprocessing as mp
import subprocess
import tempfile
import tqdm
import numpy as np
import shutil
import argparse


def get_max_h_and_w(crops: List[np.ndarray]) -> tuple[int, int]:
    """
    Compute the maximum height and width across a list of image crops.

    Args:
        crops (List[np.ndarray]): List of image crops with shape (H, W, C).

    Returns:
        tuple[int, int]: Maximum height and maximum width.
    """
    max_h, max_w = -1, -1
    for i in crops:
        max_h = max(max_h, i.shape[0])
        max_w = max(max_w, i.shape[1])
    return max_h, max_w


def pad_crops_to_max_dims(
    crops: List[np.ndarray],
) -> tuple[List[np.ndarray], np.ndarray, int, int]:
    """
    Pad all crops to the maximum height and width among them.

    Args:
        crops (List[np.ndarray]): List of image crops.

    Returns:
        Tuple containing:
            - List[np.ndarray]: Padded crops
            - np.ndarray: Original (H, W) for each crop
            - int: Maximum height
            - int: Maximum width
    """
    max_h, max_w = get_max_h_and_w(crops)
    new_crops = []
    actual_h_w = []
    for crop in crops:
        new_crop = np.zeros((max_h, max_w, crop.shape[-1]), dtype=crop.dtype)
        h_, w_ = crop.shape[0], crop.shape[1]
        new_crop[:h_, :w_, :] = crop
        new_crops.append(new_crop)
        actual_h_w.append(np.array([h_, w_]))
    actual_h_w = np.vstack(actual_h_w)
    return new_crops, actual_h_w, max_h, max_w


def upload_to_s3(
    s3_uri: str,
    local_dir: str | os.PathLike,
    upload_interval: int,
    log_dir: Optional[str | os.PathLike],
    stop_event: mp.Event
) -> None:
    """
    Periodically sync local shard directory to S3 until stop signal is received.

    Args:
        s3_uri (str): Destination S3 URI.
        local_dir (str | os.PathLike): Local shard directory.
        upload_interval (int): Interval between syncs in seconds.
        log_dir (Optional[str | os.PathLike]): Directory to store uploader logs.
        stop_event (mp.Event): Event signaling uploader termination.
    """
    if log_dir is None:
        stderr = subprocess.DEVNULL
    else:
        os.makedirs(log_dir, exist_ok=True)
        stderr = open(os.path.join(log_dir, "s3_upload_err_logs.log"), "ab")

    while not stop_event.is_set():
        subprocess.run(
            [
                "aws",
                "s3",
                "sync",
                f"{local_dir}",
                f"{s3_uri}",
                "--exclude",
                "*.temp",
                "--exclude",
                "*.lock",
                "--exclude",
                "index.json",
                "--exclude",
                "*.tmp",
                "--exclude",
                "*.log",
            ],
            stdout=subprocess.DEVNULL,
            stderr=stderr,
            check=False,
        )
        time.sleep(upload_interval)

    subprocess.run(
        [
            "aws",
            "s3",
            "sync",
            f"{local_dir}",
            f"{s3_uri}",
            "--exclude",
            "*.temp",
            "--exclude",
            "*.lock",
            "--exclude",
            "*.tmp",
            "--exclude",
            "*.log",
        ],
        stdout=subprocess.DEVNULL,
        stderr=stderr,
        check=False,
    )

    if log_dir is not None:
        stderr.close()

def is_stable(path, wait=2):
    s1 = os.stat(path).st_size
    time.sleep(wait)
    s2 = os.stat(path).st_size
    return s1 == s2
    
def clean_up_local(
    s3_uri: str,
    local_dir: str | os.PathLike,
    delete_interval: int,
    stop_event: mp.Event,
    upload_done: mp.Event,
    log_dir: Optional[str | os.PathLike] = None
    ):
    if log_dir is None:
        stderr = subprocess.DEVNULL
    else:
        os.makedirs(log_dir, exist_ok=True)
        stderr = open(os.path.join(log_dir, "clean_up_logs.log"), "ab")
    while not stop_event.is_set():
        for file in os.listdir(local_dir):
            if not file.endswith(".zstd"):
                continue

            local_path = os.path.join(local_dir, file)
            try:
                # if not is_stable(local_path):
                #     continue
                res = subprocess.run(["aws", "s3", "ls", f"{s3_uri}{file}"], stdout=subprocess.DEVNULL, stderr=stderr)
                if res.returncode!=0:
                    continue
                os.remove(local_path)
            except FileNotFoundError:
                    # raced with writer or previous cleanup
                    pass
            except Exception as e:
                if log_dir is not None:
                    stderr.write(f"{file}: {str(e)}\n".encode())
        time.sleep(delete_interval)
    while not upload_done.is_set():
        time.sleep(0.5)    
    shutil.rmtree(local_dir, ignore_errors=True)
    if log_dir is not None:
        stderr.close()
    
        
    
def mds_write(
    root_dir: str | os.PathLike,
    shard_path: str | os.PathLike,
    compression: Literal["zstd"],
    logs_dir: Optional[str | os.PathLike],
    # stop_event : mp.Event,
    size_limit: str = "256mb",
    fps: int = 30,
    infer_class_from_path: bool = True,
    cls : Optional[int|Literal["real","fake"]] = None
) -> None:
    """
    Process raw videos and write them into MDS shards.

    Args:
        root_dir (str | os.PathLike): Directory containing raw videos.
        shard_path (str | os.PathLike): Output shard directory.
        compression (Literal["zstd"]): Compression algorithm.
        logs_dir (Optional[str | os.PathLike]): Directory for ffmpeg logs.
        stop_event (mp.Event): Event signaling uploader termination.
        size_limit (str): Maximum shard size.
        fps (int): Frames per second for encoding.
        infer_class_from_path (bool): Infer class from file path.
        cls (Optional[int | Literal['real','fake']]): Label given explicitly
    """
    if logs_dir is None:
        logs_dir = shard_path
    os.makedirs(logs_dir, exist_ok=True)
    ffmpeg_logs = open(os.path.join(logs_dir, "ffmpeg_logs.log"), "ab")

    def infer_class(path: str) -> int:
        if cls is not None and isinstance(cls, int): return cls
        elif cls is not None:
            if cls=='real':
                return 0
            else:
                return 1
        elif infer_class_from_path:
            if "fake" in path or "fakes" in path or "Fake" in path or "Fakes" in path:
                return 1
            else:
                return 0
        return 0

    temp_save_dir = os.path.join(tempfile.tempdir, "mks_save_dir")
    os.makedirs(temp_save_dir, exist_ok=True)

    columns = {
        "video": "bytes",
        "class": "int",
        "pad_inf": "ndarray",
        "actual_path": "str",
    }

    with MDSWriter(
        out=shard_path,
        columns=columns,
        compression=compression,
        size_limit=size_limit,
    ) as out:
        for video_name in tqdm.tqdm(os.listdir(root_dir)):
            try:
                if video_name.endswith((".mp4", ".avi", ".mks")):
                    video_path = os.path.join(root_dir, video_name)
                    cls = infer_class(video_path)
                    faces, fps = detect_faces(video_path, device="cuda")
                    frames = _get_frames(video_path)

                    crops = []
                    for idx in range(frames.shape[0]):
                        crops.append(_get_crop(frames[idx], faces[idx][0]))

                    n_crops, actual_h_w, h, w = pad_crops_to_max_dims(crops)

                    temp_save_path = (
                        str(temp_save_dir)
                        + f"/{video_name.split('.')[0]}.mkv"
                    )

                    proc = subprocess.Popen(
                        [
                            "ffmpeg",
                            "-y",
                            "-f",
                            "rawvideo",
                            "-pix_fmt",
                            "rgb24",
                            "-s",
                            f"{w}x{h}",
                            "-r",
                            str(fps),
                            "-i",
                            "-",
                            "-c:v",
                            "ffv1",
                            f"{temp_save_path}",
                        ],
                        stdin=subprocess.PIPE,
                        stdout=ffmpeg_logs,
                        stderr=ffmpeg_logs,
                    )

                    for frame in n_crops:
                        proc.stdin.write(frame.tobytes())

                    proc.stdin.close()
                    proc.wait()

                    with open(temp_save_path, "rb") as f:
                        video_bytes = f.read()

                    out.write(
                        {
                            "video": video_bytes,
                            "class": cls,
                            "pad_inf": actual_h_w,
                            "actual_path": str(video_path),
                        }
                    )

                    os.remove(temp_save_path)

            except Exception as e:
                with open(
                    os.path.join(logs_dir, f"{video_name}.txt"), "w"
                ) as f:
                    f.write(str(e))
                continue

    ffmpeg_logs.close()


def shard_upload(
    root_dir: str | os.PathLike,
    shard_dir: str | os.PathLike,
    s3_uri: Optional[str],
    log_dir: Optional[str | os.PathLike],
    compression: Literal["zstd"]="zstd",
    size_limit: str="256mb",
    fps: int=30,
    upload_interval: int=10,
    keep_local: bool = False,
    delete_interval: int = 20,
    infer_class_from_path: bool = True,
    cls : Optional[int|Literal["real","fake"]] = None
) -> None:
    """
    Entry point that coordinates shard writing and background S3 upload.

    Args:
        root_dir (str | os.PathLike): Directory with raw videos.
        shard_dir (str | os.PathLike): Directory for shard output.
        s3_uri (Optional[str]): S3 destination URI.
        compression (Literal["zstd"]): Compression algorithm.
        size_limit (str): Shard size limit.
        fps (int): Frames per second.
        upload_interval (int): S3 sync interval.
        log_dir (Optional[str | os.PathLike]): ffmpeg log directory.
    """
    stop_event = mp.Event()
    upload_done = None
    if s3_uri is not None:
        upload_done = mp.Event()
        uploader = mp.Process(
            target=upload_to_s3,
            args=(s3_uri, shard_dir, upload_interval, log_dir, stop_event),
            daemon=True,
        )
        uploader.start()
        
        if not keep_local:
            clean_up = mp.Process(
            target=clean_up_local,
            args=(s3_uri, shard_dir, delete_interval, stop_event, upload_done, log_dir),
            daemon=True
            )
            clean_up.start()
        else:
            clean_up = None
    else:
        uploader = None
        clean_up = None

    try:
        mds_write(
            root_dir=root_dir,
            shard_path=shard_dir,
            compression=compression,
            size_limit=size_limit,
            fps=fps,
            infer_class_from_path=True,
            logs_dir=log_dir,
            cls = cls
        )
    finally:
        if uploader is not None:
            stop_event.set()
            uploader.join()
            upload_done.set()
            if clean_up is not None:
                clean_up.join()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Write video datasets into MDS shards with optional S3 upload."
    )
    
    
    parser.add_argument("--root_dir", type=str, required=True)
    parser.add_argument("--shard_dir", type=str, required=True)

    parser.add_argument("--s3_uri", type=str, default=None)

    parser.add_argument("--compression", type=str, default="zstd")
    parser.add_argument("--size_limit", type=str, default="256mb")
    parser.add_argument("--fps", type=int, default=25)
    parser.add_argument("--upload_interval", type=int, default=5)
    parser.add_argument("--delete_interval", type=int, default=2)
    parser.add_argument("--keep_local", type=bool, default=False)
    parser.add_argument("--cls", type=str, default=None)
    parser.add_argument(
        "--infer_class_from_path",
        action="store_true",
        default=True
    )
    
    parser.add_argument("--log_dir", type=str, default=None)

    args = parser.parse_args()

    shard_upload(
        root_dir=args.root_dir,
        shard_dir=args.shard_dir,
        s3_uri=args.s3_uri,
        compression=args.compression,
        size_limit=args.size_limit,
        fps=args.fps,
        upload_interval=args.upload_interval,
        keep_local = args.keep_local,
        delete_interval = args.delete_interval,
        log_dir=args.log_dir,
        infer_class_from_path=args.infer_class_from_path,
        cls = args.cls
    )

    
