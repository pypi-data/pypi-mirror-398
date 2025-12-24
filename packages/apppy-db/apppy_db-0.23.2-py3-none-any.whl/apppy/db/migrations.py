import abc


class Migrations(abc.ABC):
    @abc.abstractmethod
    async def head(self) -> str | None:
        pass


class DefaultMigrations(Migrations):
    async def head(self) -> str | None:
        return None
