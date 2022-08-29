# DuckDuckGoose

This is Rohin Bhargava's Submission for the DuckDuckGoose assignment for Sleeper.

The assignment is as follows:
## Requirements:
- Design a system that will select a single node as a “Goose” within a cluster of nodes. Every other node should be considered a “Duck”.
- If the Goose dies, another Duck should become the new Goose. 
- If a dead Goose rejoins, it should become a Duck (assuming there is already another Goose)
- There can be only one Goose, even if some working nodes are unreachable (network partition)
- Each node should run an http server with an endpoint allowing us to check if that node is a Duck or a Goose.
## Rules
- You can use your language of choice
- You can use Google/Stackoverflow/Github/etc
- You can employ 3rd party libraries / software in your program, including full fledged applications such as databases (single node or distributed)
- We will be evaluating your submission based on the original code that you write, so it is up to you on what you should write yourself vs what you use from a library. Please cite any copy-pasted code.
## Ideally
- Your design should accommodate a dynamic and changing number of nodes (elastic scale). 
- There should be a way to make your design highly available

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

## Automated testing:
- Recommended to use a virtual env, e.g. venv https://docs.python.org/3/library/venv.html
- Install requirements with `pip3 install -r requirements.txt`
- Run `python3 tests.py`. You can control settings in there or in `driver.py`. Settings are optimized for an 2021 M1 Mac with base specs.
