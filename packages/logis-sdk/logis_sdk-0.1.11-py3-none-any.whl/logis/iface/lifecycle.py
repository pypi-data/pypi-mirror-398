from abc import ABCMeta, abstractmethod


class ILifecycle(metaclass=ABCMeta):
    """
    生命周期接口
    """

    @abstractmethod
    def on_start(self, **kwargs):
        """
        启动
        """

    @abstractmethod
    def on_stop(self, **kwargs):
        """
        停止
        """

    @abstractmethod
    def on_restart(self, **kwargs):
        """
        重启
        """
