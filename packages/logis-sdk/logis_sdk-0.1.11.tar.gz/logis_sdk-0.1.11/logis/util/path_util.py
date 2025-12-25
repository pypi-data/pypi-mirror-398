from pathlib import Path


class AppRoot(Path):
    """
    鉴于每个应用都要有自己的logs、data目录，这里索性增加个工具统一管理
    """

    def dir_of(self, name: str):
        d = self.joinpath(name)
        d.mkdir(parents=True, exist_ok=True)
        return d
