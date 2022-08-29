from datetime import datetime

from redis_service_discovery import RedisServiceDiscovery
from settings import APP_BASE_PORT, APP_HOST, DUCK


# plain object to store values we care about
class State:
    def __init__(
        self, id: int, hatchlings: int, partition: int, election_wait: float
    ) -> None:
        self.id: int = id
        self.status: str = DUCK
        self.term: int = 0
        self.leader: int = None
        self.last_received: datetime = datetime.now()
        self.hatchlings: int = hatchlings
        self.candidate: bool = False

        self.consensus_loop = None

        self.alive: bool = True
        self.service_discovery_partition: int = partition
        self.service_discovery_connection = RedisServiceDiscovery(
            self.service_discovery_partition
        )
        self.service_discovery_connection.write(
            f"{APP_HOST}:{APP_BASE_PORT + self.id}",
            f"{APP_HOST}:{APP_BASE_PORT + self.id}",
        )
        self.election_wait = election_wait
