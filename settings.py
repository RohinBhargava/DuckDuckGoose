# contains configurable settings for initial state of service. this can be also done with remote config, which may be a better candidate for changeable values

# static values
REDIS_HOST = "0.0.0.0"
REDIS_PORT = 6379

APP_HOST = "0.0.0.0"
APP_BASE_PORT = 8000

DUCK = "Duck"
GOOSE = "Goose"
DEAD = "Dead"

# changeable values (remote possible)
ELECTION_TIMEOUT_MILLISECONDS = 350
STALENESS_TIMEOUT_MILLISECONDS = 600

HEARTBEAT_DELAY = 0.05

RANDOM_WAIT_RANGE_SECONDS = (0.150, 0.300)


TIMEOUT_SECONDS = 0.5
