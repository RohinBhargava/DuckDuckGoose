import asyncio
import random
import traceback
from datetime import datetime, timedelta

import aiohttp

from settings import (
    DUCK,
    ELECTION_TIMEOUT_MILLISECONDS,
    GOOSE,
    HEARTBEAT_DELAY,
    RANDOM_WAIT_RANGE_SECONDS,
    STALENESS_TIMEOUT_MILLISECONDS,
    TIMEOUT_SECONDS,
)
from state import State

election_timeout: timedelta = timedelta(milliseconds=ELECTION_TIMEOUT_MILLISECONDS)
staleness_timeout: timedelta = timedelta(milliseconds=STALENESS_TIMEOUT_MILLISECONDS)


class ConsensusLoop:
    def __init__(self, state: State) -> None:
        self.state = state

    # helper function to count the number of acknowledgements from an api call
    async def __count_acknowledgements(self, url_path: str) -> int:
        acks = 0
        for service in self.state.service_discovery_connection.service_discovery():
            try:
                # canned aiohttp http client to perform get requests asynchronously with asyncio
                session_timeout = aiohttp.ClientTimeout(
                    total=None, sock_connect=TIMEOUT_SECONDS, sock_read=TIMEOUT_SECONDS
                )
                async with aiohttp.ClientSession(timeout=session_timeout) as session:
                    async with session.get(f"http://{service}{url_path}") as resp:
                        response_json = await resp.json()
                        if response_json["ack"]:
                            acks += 1
            except Exception:
                # can debug with this, uncomment to debug
                # print(traceback.format_exc())
                pass
        return acks

    # custom event loop coroutine to handle constantly changing state
    async def coroutine(self) -> None:
        while True:
            # used purely for simulation
            if self.state.alive:
                if self.state.status == DUCK:
                    if datetime.now() - self.state.last_received > election_timeout:
                        # prepare self for candidacy, election period has begun
                        self.state.candidate = True
                        self.state.leader = None
                        self.state.voted = False
                        # wait a random amount of time to prevent election contention
                        random_wait_lower, random_wait_upper = RANDOM_WAIT_RANGE_SECONDS
                        election_wait = self.state.election_wait
                        if not election_wait:
                            election_wait = round(
                                random.uniform(random_wait_lower, random_wait_upper), 3
                            )
                        await asyncio.sleep(election_wait)

                        # prepare votes
                        term = self.state.term + 1
                        if self.state.candidate:
                            acks = await self.__count_acknowledgements(
                                f"/vote/{self.state.id}/{term}"
                            )
                            # if node has achieved quorum, and has not responded to another vote, become the goose
                            if (
                                acks > self.state.hatchlings // 2
                                and self.state.candidate
                            ):
                                self.state.status = GOOSE
                                self.state.leader = self.state.id
                                self.state.term = term
                                self.state.last_received = datetime.now()

                elif self.state.status == GOOSE:
                    # ensure that node is connected to the cluster, and doesn't need to demote itself
                    if datetime.now() - self.state.last_received < staleness_timeout:
                        # sleep to prevent too many requests from overwhelming partner node http queues
                        await asyncio.sleep(HEARTBEAT_DELAY)
                        # broadcast heartbeats, count the number of acknowledgements to make sure that quorum is still maintained
                        acks = await self.__count_acknowledgements(
                            f"/heartbeat/{self.state.id}/{self.state.term}/{self.state.hatchlings}"
                        )
                        if acks > self.state.hatchlings // 2:
                            self.state.last_received = datetime.now()
                    # if a stale goose, the node is really a duck :p
                    else:
                        self.state.status = DUCK
                        self.state.leader = None
