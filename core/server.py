import os
import asyncio

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import config
from .rate_limiter import LimiterManager


class App(FastAPI):
    server: uvicorn.Server | None
    loop: asyncio.AbstractEventLoop | None

    async def run(self):
        self.add_middleware(
            CORSMiddleware,
            allow_origins=['*'],
            allow_methods=['*'],
            allow_headers=['*'],
            allow_credentials=True
        )
        self.post('/internal/shutdown', include_in_schema=False)(self.shutdown)
        server = uvicorn.Server(uvicorn.Config(
            app=self,
            **config.server.params
        ))
        self.server = server
        await server.serve()

    def start(self):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()

        self.loop = loop
        loop.create_task(LimiterManager.scavenger())
        loop.run_until_complete(self.run())

    async def stop(self):
        # shutdown 不能正常关闭？🤔
        # await self.server.shutdown() 太怪了，不看
        # 强制退出
        os._exit(36888)
        # 摆烂了，能退出就行👍

    async def shutdown(self, req: Request, key: str):
        if req.client.host != '127.0.0.1' or key != config.key:
            raise HTTPException(status_code=403)
        with open('RESTART', mode='wb') as f:
            f.write(b'RESTART')
        asyncio.create_task(self.stop())
        return {'code': 200}


app = App()
