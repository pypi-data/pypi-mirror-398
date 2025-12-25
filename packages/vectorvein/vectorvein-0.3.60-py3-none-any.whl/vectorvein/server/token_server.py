import uvicorn
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException

from ..settings import settings
from ..chat_clients.utils import get_token_counts

token_server = FastAPI()


class TokenCountRequest(BaseModel):
    text: str | dict
    model: str = ""


@token_server.post("/count_tokens")
async def count_tokens(request: TokenCountRequest):
    try:
        token_count = get_token_counts(request.text, request.model, use_token_server_first=False)
        return {"total_tokens": token_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from None


def run_token_server(host: str | None = None, port: int | None = None):
    """
    启动一个简单的HTTP服务器来处理token计数请求。参数均留空则使用 settings.token_server 的配置。

    参数:
        host (str): 服务器主机地址。
        port (int): 服务器端口。
    """
    if host is None or port is None:
        if settings.token_server is None:
            raise ValueError("Token server is not enabled.")

        _host = settings.token_server.host
        _port = settings.token_server.port
    else:
        _host = host
        _port = port

    uvicorn.run(token_server, host=_host, port=_port)


if __name__ == "__main__":
    run_token_server()
