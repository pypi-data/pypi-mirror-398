from abc import ABC, abstractmethod


class Database(ABC):
    @abstractmethod
    async def connect(self): pass

    @abstractmethod
    async def disconnect(self): pass

    @abstractmethod
    async def execute_query(self, query: str, params: tuple = ()): pass

    @abstractmethod
    async def fetch_query(self, query: str, params: tuple = ()) -> list: pass