from typing import List
import redis
from settings import REDIS_HOST, REDIS_PORT

class RedisServiceDiscovery:
    def __init__(self, service_discovery_partition):
        self.connection = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=service_discovery_partition)

    def write(self, key: str, value: str):
        self.connection.set(key, value)

    def read(self, key: str):
        self.connection.get(key)

    def delete(self, key: str):
        self.connection.delete(key)

    def service_discovery(self) -> List[str]:
        return [service.decode() for service in self.connection.scan_iter('*')]

    def close(self):
        self.connection.close()
