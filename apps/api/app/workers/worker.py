from rq import Connection, Worker

from app.workers.queue import get_redis


def run_worker():
    redis = get_redis()
    with Connection(redis):
        worker = Worker(["comp_ingest"])
        worker.work()


if __name__ == "__main__":
    run_worker()
