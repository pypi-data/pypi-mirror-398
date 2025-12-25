import time

import requests

from linker_atom.lib.log import logger


def request(url, method, **kwargs):
    start_time = time.perf_counter()
    if 'timeout' not in kwargs:
        kwargs['timeout'] = 30
    pre_log = dict(
        _prefix='>>>Request Summary',
        url=url,
        method=method
    )
    pre_log.update(**kwargs)
    logger.debug(pre_log)
    response = requests.request(method=method, url=url, **kwargs)
    end_time = time.perf_counter()
    duration = round((end_time - start_time) * 1000, 3)
    post_log = dict(
        _prefix='>>>Response Summary',
        url=url,
        method=method,
    )
    try:
        post_log['response'] = response.json()
    except:
        pass
    post_log['duration'] = f'{duration}ms'
    logger.debug(post_log)
    return response


def get(url, **kwargs):
    return request(url, method='get', **kwargs)


def post(url, **kwargs):
    return request(url, method='post', **kwargs)
