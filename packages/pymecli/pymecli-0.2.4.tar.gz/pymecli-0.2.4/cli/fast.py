import os

import typer
import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.v1 import api_router
from core.clash import ClashConfig, init_generator
from core.config import settings
from data.dou_dict import model_path_map
from douzero import LandlordModel
from models.response import SuccessResponse

typer_app = typer.Typer()


model_path = model_path_map["landlord"]
if not os.path.exists(model_path):
    raise Exception("模型文件不存在")
LandlordModel.init_model(model_path)

app = FastAPI(
    title=settings.NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
)

# 注册 v1 版本的所有路由
app.include_router(api_router, prefix=settings.API_V1_STR)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源，生产环境建议设置具体的源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有 headers
)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "success": False, "data": None},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    # 将错误信息转换为可序列化的格式
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "type": error.get("type"),
                "loc": error.get("loc"),
                "msg": error.get("msg"),
                "input": error.get("input"),
            }
        )

    return JSONResponse(
        status_code=422,
        content={
            "error": errors,
            "success": False,
            "data": None,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "success": False,
            "data": None,
        },
    )


@app.get("/")
async def root():
    return SuccessResponse(data=f"Welcome to {settings.DESCRIPTION}")


@app.get("/ping", response_class=PlainTextResponse)
async def pingpong():
    return "pong"


@typer_app.command()
def run_app(
    host: str = typer.Argument(
        "0.0.0.0",
        help="fastapi监听的<ip>地址",
    ),
    port: int = typer.Option(
        80,
        "--port",
        help="fastapi监听的端口号",
    ),
    ssl_keyfile: str = typer.Option(
        None,
        "--ssl-keyfile",
        "-sk",
        help="ssl keyfile",
    ),
    ssl_certfile: str = typer.Option(
        None,
        "--ssl-certfile",
        "-sc",
        help="ssl certfile",
    ),
    rule: str = typer.Option(
        "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release",
        "--rule",
        "-r",
        help="clash Rule base URL",
    ),
    my_rule: str = typer.Option(
        "https://raw.githubusercontent.com/meme2046/data/refs/heads/main/clash",
        "--my-rule",
        "-mr",
        help="my clash rule base URL(自定义规则)",
    ),
    proxy: str = typer.Option(
        None,
        "--proxy",
        "-p",
        help="服务器代理,传入则通过代理转换Clash订阅,比如:socks5://127.0.0.1:7890",
    ),
):
    settings.reload()

    clash_config = ClashConfig(rule, my_rule, proxy)
    init_generator(clash_config)

    uvicorn.run(
        "cli.fast:app",
        host=host,
        port=port,
        reload=False,
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile,
    )
