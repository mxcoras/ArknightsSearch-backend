import asyncio

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import config


class App(FastAPI):
    async def run(self):
        self.add_middleware(
            CORSMiddleware,
            allow_origins=['*'],
            allow_methods=['*'],
            allow_headers=['*'],
            allow_credentials=True
        )
        await uvicorn.Server(uvicorn.Config(
            app=self,
            **config.server.params
        )).serve()

    def start(self):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()

        loop.run_until_complete(self.run())


app = App()
