from typing import List

import redis

from settings import REDIS_HOST, REDIS_PORT


# implementation of a service discovery mechanism. In this case we use a single node of Redis. In production, we expect a highly available and somewhat consistent record of services that the nodes can access.
class RedisServiceDiscovery:
    def __init__(self, service_discovery_partition) -> None:
        self.connection = redis.Redis(
            host=REDIS_HOST, port=REDIS_PORT, db=service_discovery_partition
        )

    def write(self, key: str, value: str) -> None:
        self.connection.set(key, value)

    def read(self, key: str) -> None:
        self.connection.get(key)

    def delete(self, key: str) -> None:
        self.connection.delete(key)

    def service_discovery(self) -> List[str]:
        return [service.decode() for service in self.connection.scan_iter("*")]

    def close(self) -> None:
        self.connection.close()
