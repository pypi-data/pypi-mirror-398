## 项目开发文档


### 项目目录结构

```
├── api
│   ├── app.py                    FastApi实例(get_app)
│   ├── base.py                   封装FastApi类(UdfAPIRoute)
│   ├── dependencies.py           接口依赖注入
│   ├── route.py                  路由汇总
│   ├── interface                 接口路由目录
│   │   ├── healthcheck.py
│   ├── middleware                服务启动中间件
│   │   ├── event.py              事件中间件
│   │   ├── http.py               接口中间件
│   └── schema                    接口请求及返回数据模型
│       ├── payload.py
│       └── response.py
├── config                        
│   ├── __init__.py               配置文件
│   ├── logger.py                 日志配置
│   ├── serving.py                serving所需信息配置
│   └── skywalking.py             skywalking配置
├── dependency                    加密方法
│   └── model_protector.so        模型解密
├── lib                           公共方法封装目录
│   ├── common.py                 常用方法
│   ├── exception.py              异常类型
│   ├── load_image.py             加载图片
│   ├── log.py                    日志封装
│   ├── requests.py               requests请求参数/响应日志打印
│   └── share_memory.py           共享内存
├── README.md
```

### 项目介绍

- 项目基于fastapi进行二次封装, 加入特定的事件、路由封装、参数打印、接口耗时统计、异常捕获等
    - linker_atom.api.interface.healthcheck: 内置健康检查接口, 路由:$ATOM_API_PREFIX/v1/health/ping
    - linker_atom.api.middleware.event: 注册事件类型, 传递内部配置、按需启动skywalking、按需启动后台线程apscheduler、进行向Serving服务注册及定时发送心跳
    - linker_atom.api.middleware.http: 注册接口中间件, 进行全局异常捕获,返回标准结构数据
    - linker_atom.api.app: 获取fastapi app实例, get_app
    - linker_atom.api.base: 获取fastapi APIRoute实例, UdfAPIRoute
- 通用方法封装
    - linker_atom.lib.common: 异常方法捕获装饰器、长字符截断、限定内存类
    - linker_atom.lib.exception: 通用异常返回
    - linker_atom.lib.load_image: 根据src_type类型加载数据成numpy格式
    - linker_atom.lib.log: logging持久化封装、支持skywalking、日志格式化
    - linker_atom.lib.requests: requests封装、参数、返回数据、耗时日志打印
    - linker_atom.lib.share_memory: 共享内存类封装
- 加密方法目录
    - from linker_atom.dependency.model_protector import ModelProtector: 模型解密类

---

### 使用介绍

#### 环境安装

pypi安装

```shell
pip install --no-cache-dir -U linker_atom -i https://pypi.org/simple 
```

wheel安装

```shell
pip install linker_atom-0.1.0-py3-none-any.whl --force-reinstall
```
---
#### 注意事项

- 环境变量META中servingHost传值时, 会向serving进行服务注册和心跳
- 服务注册: 服务启动后会由后台线程通过环境变量加载META信息, 并向serving地址发送注册请求,如果未注册成功,会一直进行注册,直至注册成功
- 注册心跳: 服务注册成功后,会定时发送atom心跳, 即定时请求serving

---
#### 使用示例

项目根目录下创建server.py

```python
import argparse
import os

import uvicorn
from uvicorn.loops.auto import auto_loop_setup

os.environ.setdefault('ATOM_API_PREFIX', '/d2atom')
# META = {
#     "abilityCode": "OD210_101_001866_020",
#     "abilityCodeInstance": "OD210_101_001866_020cuy4v0htvv7",
#     "abilityDependAtomCodes": [
#         "a009_msrcnn_trtv115_encrypted_d2atom_v1_serving_inf_predict_v2Om_O_V2_XXS_1"
#     ],
#     "atomCode": "a009_msrcnn_trtv115_encrypted_d2atom_v1_serving_inf_predict_v2Om_O_V2_XXS_1",
#     "atomProcessUrl": "/d2atom/v1/serving/inf_predict_v2",
#     "k8sHealthcheckUrl": "/d2atom/v1/health/ping",
#     "modelIds": "linker_z2cLOu3962_best_AP_omdet_bs4_A2_fp16",
#     "servingHost": "172.16.36.3",
#     "servingPort": "0",
#     "svcAddress": "http://omai-a009-msrcnn-trt-20231113174051749-c-s.ai:8000"
# }
# os.environ.setdefault('META', json.dumps(META))

# Fastapi 实例
from linker_atom.api.app import get_app
# APIRoute 实例
from linker_atom.api.base import UdfAPIRoute
# 内置配置类实例
from linker_atom.config import settings

app = get_app()
parser = argparse.ArgumentParser(description='Start a RESTful server.')
parser.add_argument('--port', type=int, default=8000)
args = parser.parse_args()


@app.on_event("startup")
async def startup_event():
    # 算法实现,在服务启动前加载解密模型
    for model_id in settings.model_id_list:
        pass


# 实例化路由
route = UdfAPIRoute()


# 编写接口
@route.post('/detect', name='detect')
async def detect():
    return {'code': 200}


# 添加路由
app.include_router(
    router=route,
    prefix=settings.atom_api_prefix,
)


# 运行服务
def run():
    auto_loop_setup(True)
    uvicorn.run(
        app='server:app',
        host='0.0.0.0',
        port=args.port,
        access_log=False
    )


if __name__ == '__main__':
    run()



```
---

镜像中使用nginx进行多端口负载均衡启动
使用步骤: 
- 项目根目录下实现上述server.py, 支持使用命令行参数--port指定端口启动
- 创建nginx_run.py
```python
from linker_atom.deploy import nginx_run


if __name__ == '__main__':
    nginx_run()
```
- Dockerfile文件中增加两行
```dockerfile
RUN apt-get update && apt-get install -y nginx
CMD ["python", "nginx_run.py"]
```
---
#### 项目内置环境变量

|                变量名称                 | 描述               | 默认值             |
|:-----------------------------------:|------------------|-----------------|
|            ATOM_WORKERS             | 接口服务数量           | 1               |
|           ATOM_API_PREFIX           | API前缀            | ''              |
|             ATOM_TITLE              | 标题               | ''              |
|              ATOM_DESC              | 描述               | ''              |
|          LOG_BACKUP_COUNT           | 日志保留数量           | 30              |
|               LOG_DIR               | 日志子目录            | atom            |
|         LOG_FILE_MAX_BYTES          | 单个日志文件最大字节数      | 104857600(100M) |
|              SW_SWITCH              | skywalking是否开启   | False           |
| SW_AGENT_COLLECTOR_BACKEND_SERVICES | skywalking地址     | ''              |
|            SW_AGENT_NAME            | skywalking服务名    | ''              |
|       SW_AGENT_INSTANCE_NAME        | skywalking实例名称   | uuid            |
|    SW_AGENT_LOG_REPORTER_ACTIVE     | skywalking是否记录日志 | True            |
|     SW_AGENT_LOG_REPORTER_LEVEL     | skywalking日志等级   | DEBUG           |
|                META                 | Serving传递信息json  | ''              |
|             DOCS_SWITCH             | API接口文档开关        | True            |
|              PROFILING              | 是否开启性能分析日志       | False           |
|        ATOM_INNER_START_PORT        | 多端口启动时内部起始端口     | 9000            |
