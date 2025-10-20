from abc import ABC, abstractmethod

class BaseDataset(ABC):
    """抽象 Dataset 类，提供获取数据的方法"""
    
    def __init__(self):
        self.data_cache = {}

    @abstractmethod
    def get_data_by_service_name(self, service_name: str, batch_size: int = 1):
        """通过 service_name 获取相应的数据"""
        pass

    @abstractmethod
    def cache_data(self):
        """预加载数据"""
        pass