from datetime import datetime
import sys
from consensus_loop import ConsensusLoop

import uvicorn
from fastapi import FastAPI

import asyncio
import time
from redis_service_discovery import RedisServiceDiscovery
from settings import APP_BASE_PORT, APP_HOST, DEAD, DUCK

from state import State

app = FastAPI()

if __name__ == '__main__':
    state: State = State(int(sys.argv[1]), int(sys.argv[2]), 0, float(sys.argv[3]) if len(sys.argv) > 3 else None)

@app.get("/status")
async def status():
    global state
    return {'status': state.status, 'term': state.term, 'partition': state.service_discovery_partition, 'hatchlings': state.hatchlings, 'leader': state.leader}

@app.get("/heartbeat/{leader}/{term}/{hatchlings}")
async def hearbeat(leader, term, hatchlings):
    global state
    state.leader = int(leader)
    state.term = int(term)
    if state.leader != state.id:
        state.hatchlings = int(hatchlings)
        state.last_received = datetime.now()
    state.candidate = False
    return {'ack': True}

@app.get("/vote/{new_leader}/{term}")
async def vote(term, new_leader):
    global state
    if state.term <= int(term):
        if int(new_leader) != state.id:
            state.candidate = False
        return {'ack': True}
    return {'ack': False}

@app.get("/hatchlings/{count}")
async def hatchlings(count):
    global state
    state.hatchlings = int(count)
    state.term += 1
    state.last_received = datetime.now()
    return {}

async def restore(seconds):
    time.sleep(float(seconds))
    state.status: str = DUCK
    state.term: int = 0
    state.leader: int = None
    state.last_received: datetime = datetime.now()
    state.candidate: bool = False
    state.alive = True

@app.get("/simulatedeath/{seconds}")
async def status(seconds):
    global state
    state.alive = False
    asyncio.create_task(restore(seconds))
    return {}

@app.get("/simulatepartition/{partition_id}")
async def status(partition_id):
    global state
    state.service_discovery_connection.delete(f'{APP_HOST}:{APP_BASE_PORT + state.id}')
    state.service_discovery_partition = int(partition_id)
    state.service_discovery_connection.close()
    state.service_discovery_connection = RedisServiceDiscovery(state.service_discovery_partition)
    state.service_discovery_connection.write(f'{APP_HOST}:{APP_BASE_PORT + state.id}', f'{APP_HOST}:{APP_BASE_PORT + state.id}')
    return {}

@app.get("/partition")
async def partition():
    global state
    return {"partition" : state.service_discovery_partition}

@app.get("/electionrandomize")
async def electionrandomize():
    global state
    state.election_wait = None
    return {}

@app.on_event("startup")
async def startup_event():
    global state
    state.consensus_loop = asyncio.create_task(ConsensusLoop(state).coroutine())

@app.on_event("shutdown")
async def shutdown_event():
    state.consensus_loop.cancel()

if __name__ == '__main__':
    uvicorn.run(app, host=APP_HOST, port=APP_BASE_PORT + state.id, log_level='error')

class DuckDuckGooseNode:
    def __init__(self, id: int, hatchlings: int):
        global state
        state = State(id, hatchlings)
        uvicorn.run(app, host=APP_HOST, port=APP_BASE_PORT + state.id, log_level='error')
