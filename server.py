import asyncio
import sys
import time
from datetime import datetime

import uvicorn
from fastapi import FastAPI

from consensus_loop import ConsensusLoop
from redis_service_discovery import RedisServiceDiscovery
from settings import APP_BASE_PORT, APP_HOST, DEAD, DUCK, GOOSE
from state import State

# create FastAPI instance
app = FastAPI()

if __name__ == "__main__":
    # setup state with command line arguments. If election wait time specified, set election wait
    state: State = State(
        int(sys.argv[1]),
        int(sys.argv[2]),
        0,
        float(sys.argv[3]) if len(sys.argv) > 3 else None,
    )

# returns some state variables we might care about
@app.get("/status")
async def status():
    global state
    return {
        "status": state.status,
        "term": state.term,
        "partition": state.service_discovery_partition,
        "hatchlings": state.hatchlings,
    }


# for heartbeats, we take the hatchlings and term from the Goose, overwriting anything previously in state
@app.get("/heartbeat/{leader}/{term}/{hatchlings}")
async def hearbeat(leader, term, hatchlings):
    global state
    # reject heartbeats from older terms that may have had network delay, and in the case of Goose race, ensure that new election period begins
    if int(term) < state.term:
        return {"ack": False}
    state.leader = int(leader)
    state.term = int(term)
    if state.leader != state.id:
        state.hatchlings = int(hatchlings)
        state.last_received = datetime.now()
    state.candidate = False
    state.voted = False
    return {"ack": True}


# vot
@app.get("/vote/{new_leader}/{term}")
async def vote(term, new_leader):
    global state
    ack = False
    # on race, consider removing from candidacy
    if state.term <= int(term) and not state.voted:
        if int(new_leader) != state.id:
            state.candidate = False
        state.voted = True
        ack = True
    state.voted = True
    return {"ack": ack}


# set the expected cluster size; this should be sent to every node in the cluster, resemblant of remote configuration
# in the case of split partition and scale up, the Goose should be in already quorum partition, so if joining there, the Goose is maintained. If service discovery results in scale up on the other partition, the Goose will demote and a new Goose will be elected in the partition where there is quorum
# in the case of split partition and scale down, the Goose will be maintained
@app.get("/hatchlings/{count}")
async def hatchlings(count):
    global state
    state.hatchlings = int(count)
    state.last_received = datetime.now()
    return {}


# helper method for simulating node death
async def restore(seconds: float) -> None:
    global state
    time.sleep(seconds)
    state.status: str = DUCK
    state.term: int = 0
    state.leader: int = None
    state.last_received: datetime = datetime.now()
    state.candidate: bool = False
    state.alive = True


# simulate node death for a specified amount of time
@app.get("/simulatedeath/{seconds}")
async def status(seconds):
    global state
    state.alive = False
    asyncio.create_task(restore(float(seconds)))
    return {}


# simulate partitioning, using redis as a stand in for DNS or some service discovery mechanism that provides information about services within the network partition
@app.get("/simulatepartition/{partition_id}")
async def status(partition_id):
    global state
    state.service_discovery_connection.delete(f"{APP_HOST}:{APP_BASE_PORT + state.id}")
    state.service_discovery_partition = int(partition_id)
    state.service_discovery_connection.close()
    state.service_discovery_connection = RedisServiceDiscovery(
        state.service_discovery_partition
    )
    state.service_discovery_connection.write(
        f"{APP_HOST}:{APP_BASE_PORT + state.id}",
        f"{APP_HOST}:{APP_BASE_PORT + state.id}",
    )
    return {}


# test hook to establish a randomized election wait period, in case the election wait period is set as the same for all nodes
@app.get("/electionrandomize")
async def electionrandomize():
    global state
    state.election_wait = None
    return {}


# start event loop on api startup
@app.on_event("startup")
async def startup_event():
    global state
    state.consensus_loop = asyncio.create_task(ConsensusLoop(state).coroutine())


# destroy the event loop
@app.on_event("shutdown")
async def shutdown_event():
    state.consensus_loop.cancel()


if __name__ == "__main__":
    uvicorn.run(app, host=APP_HOST, port=APP_BASE_PORT + state.id, log_level="error")
