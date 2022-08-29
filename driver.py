import os
import signal
import subprocess
import time

# configurable
INITIAL_NODES = 3

# static script that can be run standalone
processes = []
nodes = INITIAL_NODES
redis_process = None


def create_processes(election_wait=None) -> None:
    global redis_process
    with open(os.devnull, "w") as fp:
        redis_process = subprocess.Popen(f"redis-server", shell=True, stdout=fp)
        time.sleep(0.5)
        subprocess.Popen(f"redis-cli FLUSHALL", shell=True)
    for i in range(INITIAL_NODES):
        processes.append(
            subprocess.Popen(
                f'python3 server.py {i} {INITIAL_NODES} {election_wait if election_wait else ""}',
                shell=True,
            )
        )


def add_process() -> None:
    global nodes
    processes.append(
        subprocess.Popen(f"python3 server.py {nodes} {nodes} 0.150", shell=True)
    )
    nodes += 1


def delete_process() -> None:
    global nodes
    process = processes.pop(-1)
    os.kill(process.pid, signal.SIGKILL)
    nodes -= 1


def delete_processes() -> None:
    global redis_process
    while processes:
        os.kill(processes.pop().pid, signal.SIGKILL)
    os.kill(redis_process.pid, signal.SIGKILL)


if __name__ == "__main__":
    create_processes()
    time.sleep(30)
    delete_processes()
