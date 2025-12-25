import asyncio
import base64
import json
from concurrent.futures import as_completed, ThreadPoolExecutor
from functools import partial
from io import BytesIO
from itertools import zip_longest
from typing import Callable, Dict, Iterable, List, Optional, Union

import aiohttp
import cv2
import numpy as np
import requests
from PIL import Image
from PIL import ImageFile

from linker_atom.lib.exception import VqlError
from linker_atom.lib.share_memory import MmapManager

FETCH_TIMEOUT = 15
ImageFile.LOAD_TRUNCATED_IMAGES = True


def local_to_pil(path: str) -> Image.Image:
    return Image.open(path).convert("RGB")


def base64_to_pil(b64_str: str) -> Image.Image:
    b64_bytes = base64.b64decode(b64_str)
    return Image.open(BytesIO(b64_bytes)).convert("RGB")


def url_to_pil(url: str) -> Optional[Image.Image]:
    content = None
    for _ in range(3):
        response = requests.get(url, timeout=FETCH_TIMEOUT)
        content = response.content
        if content:
            break
    if content is None:
        return
    return Image.open(BytesIO(content)).convert("RGB")


def mmap_to_pil(value: Union[str, dict]) -> Image.Image:
    if isinstance(value, str):
        value = json.loads(value)
    path, position, size, height, width = (
        str(value.get("path")),
        int(value.get("position")),
        int(value.get("size")),
        int(value.get("height")),
        int(value.get("width")),
    )
    mm = MmapManager(path)
    buffer = mm.read(position, size)
    return Image.frombytes(mode='RGB', size=(width, height), data=buffer).convert("RGB")


def file_to_base64(path: str, mode="rb") -> bytes:
    with open(path, mode) as f:
        return base64.b64encode(f.read())


def url_to_np(url: str) -> Optional[np.ndarray]:
    content = None
    for _ in range(3):
        response = requests.get(url, timeout=FETCH_TIMEOUT)
        content = response.content
        if content:
            break
    if content is None:
        return
    img = np.asarray(bytearray(content), dtype=np.uint8)
    img = cv2.imdecode(img, cv2.IMREAD_COLOR)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return img


def local_to_np(path: str) -> Optional[np.ndarray]:
    np_data = np.fromfile(path, dtype=np.uint8)
    img = cv2.imdecode(np_data, cv2.IMREAD_COLOR)
    # img = cv2.imread(path, cv2.IMREAD_COLOR)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return img


def base64_to_np(data: str) -> Optional[np.ndarray]:
    img_string = base64.b64decode(data)
    img = np.frombuffer(img_string, np.uint8)
    img = cv2.imdecode(img, cv2.IMREAD_COLOR)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return img


def mmap_to_np(value: Union[str, dict]) -> Optional[np.ndarray]:
    if isinstance(value, str):
        value = json.loads(value)
    path, position, size, height, width = (
        str(value.get("path")),
        int(value.get("position")),
        int(value.get("size")),
        int(value.get("height")),
        int(value.get("width")),
    )
    mm = MmapManager(path)
    buffer = mm.read(position, size)
    np_arr = np.frombuffer(buffer=buffer, dtype=np.uint8)
    img = np_arr.reshape((height, width, 3))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return img


# def codec_to_np(path: str) -> np.ndarray:
#     with av.open(path) as container:
#         for frame in container.decode(video=0):
#             frame = frame.to_ndarray(format='bgr24')
#             break
#     return frame
#
#
# def codec_to_pil(path: str) -> Image.Image:
#     with av.open(path) as container:
#         for frame in container.decode(video=0):
#             frame = frame.to_image()
#             break
#     return frame


def video_to_np(path) -> np.ndarray:
    cap = cv2.VideoCapture(path)
    ret, frame = cap.read()
    cap.release()
    return frame


def chunked(it, n) -> Iterable:
    marker = object()
    for group in (list(g) for g in zip_longest(*[iter(it)] * n, fillvalue=marker)):
        yield filter(lambda x: x is not marker, group)


SRC_TYPE_MAP = {
    "url": url_to_np,
    "local": local_to_np,
    "base64": base64_to_np,
    "mmap": mmap_to_np,
    # "h264": codec_to_np,
    # "h265": codec_to_np,
}


def load_image(src_type: str, data: List, func_map: Dict[str, Callable] = None) -> List:
    if not data or src_type == "stream":
        return []
    if func_map is None:
        func_map = SRC_TYPE_MAP
    
    if len(data) == 1:
        match_func = func_map.get(src_type)
        if not match_func:
            raise VqlError(504)
        result = match_func(data[0])
        return [result]
    
    tasks = dict()
    results = []
    with ThreadPoolExecutor(thread_name_prefix="LoadImage") as e:
        for index, data in enumerate(data):
            match_func = func_map.get(src_type)
            if not match_func:
                raise VqlError(504)
            tasks[e.submit(match_func, data)] = index
    for task in as_completed(tasks):
        result = task.result()
        if result is None:
            raise VqlError(503)
        index = tasks[task]
        results.append(dict(index=index, result=result))
    results.sort(key=lambda x: x["index"])
    return [item["result"] for item in results]


async def async_url_to_pil(data: List) -> List:
    async def read2pil(session: aiohttp.ClientSession, url: str):
        response = await session.get(url, timeout=FETCH_TIMEOUT)
        content = await response.read()
        return Image.open(BytesIO(content)).convert("RGB")
    
    if len(data) == 1:
        async with aiohttp.ClientSession() as session:
            result = await read2pil(session, data[0])
        return [result]
    
    tasks = []
    async with aiohttp.ClientSession() as session:
        for url in data:
            tasks.append(read2pil(session, url))
        result = await asyncio.gather(*tasks)
        return list(result)


async def async_url_to_np(data: List) -> List:
    async def read2np(session: aiohttp.ClientSession, url: str):
        response = await session.get(url, timeout=FETCH_TIMEOUT)
        content = await response.read()
        img = np.asarray(bytearray(content), dtype=np.uint8)
        img = cv2.imdecode(img, cv2.IMREAD_COLOR)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return img
    
    if len(data) == 1:
        async with aiohttp.ClientSession() as session:
            result = await read2np(session, data[0])
        return [result]
    
    tasks = []
    async with aiohttp.ClientSession() as session:
        for url in data:
            tasks.append(read2np(session, url))
        result = await asyncio.gather(*tasks)
        return list(result)


load_np_image = partial(
    load_image,
    func_map={
        "url": url_to_np,
        "local": local_to_np,
        "base64": base64_to_np,
        "mmap": mmap_to_np,
        # "h264": codec_to_np,
        # "h265": codec_to_np,
    }
)

load_pil_image = partial(
    load_image,
    func_map={
        "url": url_to_pil,
        "local": local_to_pil,
        "base64": base64_to_pil,
        "mmap": mmap_to_pil,
        # "h264": codec_to_pil,
        # "h265": codec_to_pil,
    }
)
