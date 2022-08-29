from datetime import datetime, timedelta
import time
import driver
import requests

from settings import APP_BASE_PORT, APP_HOST, ELECTION_TIMEOUT_MILLISECONDS, GOOSE, RANDOM_WAIT_RANGE_SECONDS, TIMEOUT_SECONDS

wait_period = 2 * ELECTION_TIMEOUT_MILLISECONDS/1000 + RANDOM_WAIT_RANGE_SECONDS[1]/1000 + 0.4
startup_time = driver.INITIAL_NODES/3

print ('Tests started')

def node_status():
    statuses = []
    print(f'Current Status {datetime.now()}')
    for i in range(driver.nodes):
        try:
            response = requests.get(f"http://{APP_HOST}:{APP_BASE_PORT + i}/status", timeout=TIMEOUT_SECONDS)
            # status = response.json()['status']
            response_json = response.json()
            print(f"Instance {i}: {', '.join([key + ': ' + str(response_json[key]) for key in response_json])}")
            statuses.append(response_json['status'])
        except:
            print(f"Instance {i}: Dead")
    print()
    return statuses

def election_wait_test(start_time):
    print("Beginning Election Wait Test, should expect to see all Ducks in the first pass (representing a rejected election), however, depinding on thread speed, the actual timedelta may result in a Goose.")
    while datetime.now() - start_time < timedelta(seconds=3):
        node_status()
        for i in range(driver.INITIAL_NODES):
            try:
                requests.get(f"http://{APP_HOST}:{APP_BASE_PORT + i}/electionrandomize", timeout=TIMEOUT_SECONDS)
            except:
                pass
        time.sleep(wait_period)
    print("End Election Wait Test")

def basic_test(start_time):
    print("Beginning Basic Test, should expect to see a consistent Goose")
    while datetime.now() - start_time < timedelta(seconds=3):
        node_status()
        time.sleep(wait_period)
    print("End Basic Test")

def death_test(start_time: int):
    print("Beginning Death Test, should expect to see Goose takeovers, to different instances than those killed")
    while datetime.now() - start_time < timedelta(seconds=6):
        statuses = node_status()
        try:
            goose = statuses.index(GOOSE)
            requests.get(f"http://{APP_HOST}:{APP_BASE_PORT + goose}/simulatedeath/{wait_period}", timeout=TIMEOUT_SECONDS)
        except:
            pass
        time.sleep(wait_period)
        node_status()
        time.sleep(wait_period)
    print("End Death Test")

def partition_test(start_time: int):
    print("Beginning Partition Test, should expect to see one Goose takeover, as original Goose will be partitioned, and then current Goose joins that partition")
    while datetime.now() - start_time < timedelta(seconds=5):
        statuses = node_status()
        try:
            goose = statuses.index(GOOSE)
            requests.get(f"http://{APP_HOST}:{APP_BASE_PORT + goose}/simulatepartition/1", timeout=TIMEOUT_SECONDS)
        except:
            pass
        time.sleep(wait_period)
    print("End Partition Test")

def elasticity_test(start_time: int):
    print("Beginning Elasticity Test, should expect to see node get added and removed in successive status reports")
    while datetime.now() - start_time < timedelta(seconds=10):
        statuses = node_status()
        try:
            goose = statuses.index(GOOSE)
            requests.get(f"http://{APP_HOST}:{APP_BASE_PORT + goose}/hatchlings/{driver.nodes + 1}", timeout=TIMEOUT_SECONDS)
            driver.add_process()
        except:
            pass
        time.sleep(wait_period + startup_time)
        statuses = node_status()
        try:
            goose = statuses.index(GOOSE)
            requests.get(f"http://{APP_HOST}:{APP_BASE_PORT + goose}/hatchlings/{driver.nodes - 1}", timeout=TIMEOUT_SECONDS)
            driver.delete_process()
        except:
            pass
        time.sleep(wait_period + startup_time)
        statuses = node_status()
    print("End Elasticity Test")

def complex_test(start_time: int):
    print("Begin Complex Test, expectations will be addressed before printing out each state")
    while datetime.now() - start_time < timedelta(seconds=10):
        statuses = node_status()
        try:
            goose = statuses.index(GOOSE)
            requests.get(f"http://{APP_HOST}:{APP_BASE_PORT + goose}/hatchlings/{driver.nodes + 1}", timeout=TIMEOUT_SECONDS)
            driver.add_process()
            time.sleep(wait_period + startup_time)
            print ("Expect an added node")
            statuses = node_status()
        except:
            pass
        try:
            goose = statuses.index(GOOSE)
            requests.get(f"http://{APP_HOST}:{APP_BASE_PORT + goose}/simulatepartition/1", timeout=TIMEOUT_SECONDS)
            time.sleep(wait_period)
            print ("Expect previous Goose to be in own partition and demote itself to Duck. There should be a new Goose soon.")
            statuses = node_status()
        except:
            pass
        try:
            goose = statuses.index(GOOSE)
            requests.get(f"http://{APP_HOST}:{APP_BASE_PORT + goose}/simulatedeath/{wait_period}", timeout=TIMEOUT_SECONDS)
            time.sleep(wait_period)
            print ("Expect all Ducks, with Goose having been simulated dead. A new Goose will be chosen soon.")
            statuses = node_status()
            time.sleep(wait_period)
        except:
            pass
    print("End Complex Test")

def run_test(function, election_wait = None):
    try:
        driver.create_processes(election_wait)
        time.sleep(startup_time)
        function(datetime.now())
        time.sleep(wait_period)
        print ("Final State")
        statuses = node_status()
        print()
    finally:
        driver.delete_processes()

run_test(basic_test)
run_test(election_wait_test, '0.150')
run_test(death_test)
run_test(partition_test)
run_test(elasticity_test)
run_test(complex_test)