import importlib


def get_basic_auth(username, password):
    try:
        httpx = importlib.import_module("httpx")
    except ImportError as e:
        raise Exception(f"httpx is not exist,run:pip install httpx==0.24.1")
    return httpx.BasicAuth(username, password)


async def async_common_request(method, url, params=None, data=None, json=None,
                               result_type="json", connect_config=None, **kwargs):
    try:
        httpx = importlib.import_module("httpx")
    except ImportError as e:
        raise Exception(f"httpx is not exist,run:pip install httpx==0.24.1")
    if not connect_config or not isinstance(connect_config, dict):
        connect_config = {"timeout": None}
    with httpx.AsyncClient(**connect_config) as session:
        async with session.request(method.upper(), url=url, params=params, json=json, data=data,
                                   **kwargs) as resp:
            if result_type == "json":
                result = await resp.json()
            elif result_type == "text":
                result = await resp.text
            elif result_type == "origin":
                return resp
            else:
                result = await resp.content
            return result


def sync_common_request(method, url, params=None, data=None, json=None, result_type="json",
                        connect_config=None, **kwargs):
    try:
        httpx = importlib.import_module("httpx")
    except ImportError as e:
        raise Exception(f"httpx is not exist,run:pip install httpx==0.24.1")
    if not connect_config or not isinstance(connect_config, dict):
        connect_config = {"timeout": None}
    with httpx.Client(**connect_config) as session:
        try:
            res = session.request(method.upper(), url=url, params=params, data=data, json=json, **kwargs)
            if result_type == "json":
                result = res.json()
            elif result_type == "text":
                result = res.text
            elif result_type == "origin":
                return res
            else:
                result = res.content
            return result
        except Exception as e:
            raise e


async def async_common_get(url, params=None, result_type="json", connect_config=None, **kwargs):
    return await async_common_request(method="GET", url=url, params=params, result_type=result_type,
                                      connect_config=connect_config, **kwargs)


async def async_common_post(url, params=None, data=None, json=None, result_type="json", connect_config=None, **kwargs):
    return await async_common_request(method="POST", url=url, params=params, data=data, json=json,
                                      result_type=result_type,
                                      connect_config=connect_config, **kwargs)


async def async_common_put(url, params=None, data=None, json=None, result_type="json", connect_config=None, **kwargs):
    return await async_common_request(method="PUT", url=url, params=params, data=data, json=json,
                                      result_type=result_type,
                                      connect_config=connect_config, **kwargs)


async def async_common_delete(url, params=None, data=None, json=None, result_type="json", connect_config=None,
                              **kwargs):
    return await async_common_request(method="DELETE", url=url, params=params, data=data, json=json,
                                      result_type=result_type,
                                      connect_config=connect_config, **kwargs)


def sync_common_get(url, params=None, result_type="json", connect_config=None, **kwargs):
    return sync_common_request(method="GET", url=url, params=params, result_type=result_type,
                               connect_config=connect_config, **kwargs)


def sync_common_post(url, params=None, data=None, json=None, result_type="json", connect_config=None, **kwargs):
    return sync_common_request(method="POST", url=url, params=params, data=data, json=json,
                               result_type=result_type,
                               connect_config=connect_config, **kwargs)


def sync_common_put(url, params=None, data=None, json=None, result_type="json", connect_config=None, **kwargs):
    return sync_common_request(method="PUT", url=url, params=params, data=data, json=json,
                               result_type=result_type,
                               connect_config=connect_config, **kwargs)


def sync_common_delete(url, params=None, data=None, json=None, result_type="json", connect_config=None,
                       **kwargs):
    return sync_common_request(method="DELETE", url=url, params=params, data=data, json=json,
                               result_type=result_type,
                               connect_config=connect_config, **kwargs)
