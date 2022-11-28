from library import *

# cleaner function
def ctrl_c(redisobj,redispool):
    print("Closing Redis connection")
    redisobj.close()
    print("Removing connection pool")
    redispool.disconnect()
    print("Exiting")
    exit(0)

random.seed(555)

pool = redis.BlockingConnectionPool(host='myredis.whatever.com',port='6379',password='GiggleBot.2015',decode_responses=True,timeout=10000)
r = redis.Redis(connection_pool=pool)

# 'standard' infinite loop
while True:
    # we need a way to clean up things after a CTRL-C from the user
    try:
        chiave = random.randint(0,999)
        valore = run_with_backoff(lambda: r.get(f"chiave{chiave}"))
        print(f"{chiave} {valore}")
    except KeyboardInterrupt:
        ctrl_c(r,pool)

