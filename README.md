# DuckDuckGoose

This is Rohin Bhargava's Submission for the DuckDuckGoose assignment.

To accomplish this assignment, I implemented a slightly modified version of the election process as specified by the Raft Consensus Algorithm:
https://raft.github.io/raft.pdf (section 5.2)

Essentially there are three conditions:
- If a node hasn't received a hearbeat for longer than the election timeout, it puts itself into candidate mode.
- If a node receives a vote, it takes itself out of consideration for goose election and defers to the goose it received a vote from.
- In the instance of a split vote, both candidates will demote themselves and the election process begins anew.

## Prerequisites:
- Redis: https://redis.io/docs/getting-started/
- Python3: https://www.python.org/downloads/
- Unix based terminal

## Running locally:
- Recommended to use a virtual env, e.g. venv https://docs.python.org/3/library/venv.html
- Install requirements with `pip3 install -r requirements.txt`
- Run `python3 driver.py`. There are settings/lifetime settings for the program in the file that are configurable.
- Killing nodes and using using the `/simulatedeath` api have nearly the same effect (not fully equal).

## Automated testing:
- Recommended to use a virtual env, e.g. venv https://docs.python.org/3/library/venv.html
- Install requirements with `pip3 install -r requirements.txt`
- Run `python3 tests.py`. You can control settings in there or in `driver.py`. Settings are optimized for an 2021 M1 Mac with base specs.

## Comments:
- While this solution uses Redis to simulate service discovery, in a production system, a consistent service discovery implementation should be used. DNS or a consistent Data Source was what I was envisioning here.
- Asyncio is not a direct implementation of async I have seen in other languages (it uses a single main thread), but the decision to use python was to spin up an API quickly. In production, I would use a staticly typed language with threaded async support.
- There are spots of canned code I found from stack overflow (boilerplate or syntax). All the internal logic is of my own understanding.
- Simulating voting ties is a little difficult, since the processes start at different times. The election wait test can sometimes be a little flaky.
