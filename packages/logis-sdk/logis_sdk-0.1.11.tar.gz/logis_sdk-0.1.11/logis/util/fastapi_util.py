from abc import ABC, abstractmethod

from fastapi import APIRouter, FastAPI


class RouteRegister(ABC):

    @abstractmethod
    def get_router(self, **kwargs) -> APIRouter:
        pass

    def register(self, app: FastAPI, **kwargs):
        app.include_router(self.get_router(**kwargs))
