import hashlib, socket, uuid, os

def machine_fingerprint(extra=""):
    raw = "|".join([
        socket.gethostname(),
        hex(uuid.getnode()),
        os.getenv("KUBERNETES_SERVICE_HOST", "nok8s"),
        extra
    ])
    return hashlib.sha256(raw.encode()).hexdigest()
