
import os, json, time

TRACE_DIR = os.getenv("TRACE_DIR", "./traces")
os.makedirs(TRACE_DIR, exist_ok=True)

def checkpoint_state(run_id: str, step_name: str, state: dict):
    ts = int(time.time() * 1000)
    path = os.path.join(TRACE_DIR, f"{run_id}_{ts}_{step_name}.json")
    with open(path, "w") as f:
        json.dump({"step": step_name, "state": state}, f, default=str)
    return path

def retry_call(fn, retries: int = 2, delay: float = 0.6):
    import time
    last_err = None
    for i in range(retries + 1):
        try:
            return fn()
        except Exception as e:
            last_err = e
            if i < retries:
                time.sleep(delay)
    raise last_err
