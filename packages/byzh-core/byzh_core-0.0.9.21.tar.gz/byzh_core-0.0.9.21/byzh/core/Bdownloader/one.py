import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import math
import threading
from ..Btqdm import B_Tqdm  # 保留你原来的进度条

DEFAULT_CHUNK = 2048

def _get_head_info(url: str, headers: dict):
    ''' HEAD 请求获取大小和是否支持 Range '''
    r = requests.head(url, headers=headers, allow_redirects=True) # allow_redirects: 允许重定向
    r.raise_for_status()
    total = r.headers.get('content-length')
    total = int(total) if total is not None else None
    accept_ranges = r.headers.get('accept-ranges', '').lower()  # 'bytes' 表示支持分段
    return total, ('bytes' in accept_ranges)

def _single_thread_download(url: str, save_path: Path, headers: dict, chunk_size: int, total_size: int | None):
    ''' 退回到单线程的原始实现（stream） '''
    with requests.get(url, stream=True, headers=headers) as r:
        r.raise_for_status()
        # 进度条
        my_tqdm = B_Tqdm(range=total_size, type='MB', prefix=f'Downloading {save_path.name}')
        with open(save_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    my_tqdm.update(len(chunk))
    print(f"文件已保存到: {save_path}")

def _download_range_to_part(url: str, start: int, end: int, part_path: Path,
                            headers: dict, chunk_size: int, progress_updater):
    ''' 下载指定字节范围到单个 part 文件 '''
    range_header = {'Range': f'bytes={start}-{end}'}
    local_headers = headers.copy()
    local_headers.update(range_header)
    with requests.get(url, stream=True, headers=local_headers) as r:
        # Some servers reply 206 Partial Content; others might ignore Range
        if r.status_code not in (200, 206):
            r.raise_for_status()
        with open(part_path, 'wb') as pf:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    pf.write(chunk)
                    progress_updater(len(chunk))

def b_download_file(
        url: str,
        save_path: str = None,
        num_threads: int = 8,
        chunk_size: int = DEFAULT_CHUNK
):
    """
    多线程分段下载函数。
    - url: 下载链接
    - save_path: 保存路径，None 则使用 URL 名称
    - num_threads: 并发线程数（建议 4-8，根据带宽调整）
    - chunk_size: 每次读取大小（字节）
    """
    if save_path is None:
        save_path = Path(url).name
    save_path = Path(save_path)

    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/117.0.0.0 Safari/537.36")
    }

    # 1) 先 HEAD 检查 content-length 和 accept-ranges
    try:
        total_size, accept_ranges = _get_head_info(url, headers)
    except Exception:
        # HEAD 可能有些服务器不允许，尝试用 GET 获取头部信息
        with requests.get(url, stream=True, headers=headers) as r:
            r.raise_for_status()
            total = r.headers.get('content-length')
            total_size = int(total) if total else None
            accept_ranges = 'bytes' in r.headers.get('accept-ranges', '').lower()

    # 如果没有 content-length 或者不支持 Range，则退回单线程
    if (total_size is None) or (not accept_ranges):
        print("服务器不支持分段下载或未返回 content-length，使用单线程下载。")
        _single_thread_download(url, save_path, headers, chunk_size, total_size)
        return

    # 2) 计算每个 part 的范围
    part_size = math.ceil(total_size / num_threads)
    ranges = []
    for i in range(num_threads):
        start = i * part_size
        end = min(start + part_size - 1, total_size - 1)
        if start <= end:
            ranges.append((start, end))

    # 3) 创建进度条和线程安全的更新函数
    prog = B_Tqdm(range=total_size, type='MB', prefix=f'[{num_threads} thread] Downloading {save_path.name}')
    prog_lock = threading.Lock()
    def progress_updater(n_bytes):
        # B_Tqdm 假设 update 可以直接传字节数
        with prog_lock:
            prog.update(n_bytes)

    # 4) 并发下载每个 part 到临时文件
    temp_part_dir = Path(save_path.parent) / f"downloading_{save_path.name}"
    temp_part_dir.mkdir(parents=True, exist_ok=True)
    part_paths = []
    with ThreadPoolExecutor(max_workers=min(num_threads, len(ranges))) as exe:
        futures = []
        for idx, (start, end) in enumerate(ranges):
            part_path = temp_part_dir / f"{save_path.name}.part{idx}"
            part_paths.append(part_path)
            futures.append(
                exe.submit(_download_range_to_part, url, start, end, part_path, headers, chunk_size, progress_updater)
            )
        # 等待所有完成（并会抛出异常）
        for fut in as_completed(futures):
            fut.result()

    # 5) 合并 parts
    with open(save_path, 'wb') as out_f:
        for part_path in part_paths:
            with open(part_path, 'rb') as pf:
                while True:
                    chunk = pf.read(DEFAULT_CHUNK)
                    if not chunk:
                        break
                    out_f.write(chunk)
            os.remove(part_path)
        os.remove(temp_part_dir)

    print(f"多线程下载完成: {save_path} (size: {total_size} bytes)")

if __name__ == '__main__':
    # 示例
    b_download_file('https://github.com/FFmpeg/FFmpeg/archive/refs/tags/n7.1.2.zip',
                          save_path='n7.1.2.zip', num_threads=6)
