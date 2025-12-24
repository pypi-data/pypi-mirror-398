import os
import hashlib

def default_test_keys(seed="kafkagraph-0.1.0"):
    keys = []
    for i in range(1, 11):
        h = hashlib.sha256(f"{seed}:{i}".encode()).hexdigest()[:32]
        keys.append(h)
    return keys

def load_api_keys():
    env = os.getenv("KAFKAGRAPH_API_KEYS")
    if env:
        return set([k.strip() for k in env.split(",") if k.strip()])
    path = os.getenv("KAFKAGRAPH_API_KEYS_FILE")
    if path and os.path.exists(path):
        with open(path) as f:
            return set([line.strip() for line in f if line.strip()])
    return set(default_test_keys())
