import asyncio
import aiohttp
from datetime import datetime, timedelta
import random
import traceback

from settings import DUCK, ELECTION_TIMEOUT_MILLISECONDS, GOOSE, RANDOM_WAIT_RANGE_SECONDS, STALENESS_TIMEOUT_MILLISECONDS, TIMEOUT_SECONDS

from state import State

election_timeout: timedelta = timedelta(milliseconds=ELECTION_TIMEOUT_MILLISECONDS)
staleness_timeout: timedelta = timedelta(milliseconds=STALENESS_TIMEOUT_MILLISECONDS)

class ConsensusLoop:
    def __init__(self, state: State):
        self.state = state

    async def __count_acknowledgements(self, url_path: str) -> int:
        acks = 0
        for service in self.state.service_discovery_connection.service_discovery():
            try:
                session_timeout = aiohttp.ClientTimeout(total=None,sock_connect=TIMEOUT_SECONDS,sock_read=TIMEOUT_SECONDS)
                async with aiohttp.ClientSession(timeout=session_timeout) as session:
                    async with session.get(f'http://{service}{url_path}') as resp:
                        response_json = await resp.json()
                        if response_json['ack']:
                            acks += 1
            except Exception:
                # print(traceback.format_exc())
                pass
        return acks

    async def coroutine(self):
        while True:
            if self.state.alive:
                if self.state.status == DUCK:
                    # print (self.state.status, datetime.now() - self.state.last_received, election_timeout, self.state.hatchlings)
                    if datetime.now() - self.state.last_received > election_timeout:
                        self.state.candidate = True
                        self.state.leader = None
                        random_wait_lower, random_wait_upper = RANDOM_WAIT_RANGE_SECONDS
                        election_wait = self.state.election_wait
                        if not election_wait:
                            election_wait = round(random.uniform(random_wait_lower, random_wait_upper), 3)
                        await asyncio.sleep(election_wait)

                        term = self.state.term + 1
                        if self.state.candidate:
                            acks = await self.__count_acknowledgements(f'/vote/{self.state.id}/{term}')
                            if acks > self.state.hatchlings//2 and self.state.candidate:
                                self.state.status = GOOSE
                                self.state.leader = self.state.id
                                self.state.term = term
                                self.state.last_received = datetime.now()

                else:
                    # print (self.state.status, datetime.now() - self.state.last_received, staleness_timeout, self.state.hatchlings)
                    if datetime.now() - self.state.last_received < staleness_timeout:
                        acks = await self.__count_acknowledgements(f'/heartbeat/{self.state.id}/{self.state.term}/{self.state.hatchlings}')
                        if acks > self.state.hatchlings//2:
                            self.state.last_received = datetime.now()
                    else:
                        self.state.status = DUCK
                        self.state.leader = None
