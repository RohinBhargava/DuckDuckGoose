
import os
import signal
import subprocess
import time

INITIAL_NODES = 5

processes = []
nodes = INITIAL_NODES

def create_processes(election_wait = None):
    subprocess.Popen(f'redis-cli FLUSHALL', shell=True)
    for i in range(INITIAL_NODES):
        processes.append(subprocess.Popen(f'python3 server.py {i} {INITIAL_NODES} {election_wait if election_wait else ""}', shell=True))

def add_process():
    global nodes
    processes.append(subprocess.Popen(f'python3 server.py {nodes} {nodes} 0.150', shell=True))
    nodes += 1

def delete_process():
    global nodes
    process = processes.pop(-1)
    os.kill(process.pid, signal.SIGKILL)
    nodes -= 1

def delete_processes():
    while processes:
        os.kill(processes.pop().pid, signal.SIGKILL)
    

if __name__ == '__main__':
    time.sleep(30)
    delete_processes()
