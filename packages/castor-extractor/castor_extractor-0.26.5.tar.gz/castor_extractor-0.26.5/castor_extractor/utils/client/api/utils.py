def build_url(host: str | None, endpoint: str):
    if not host:
        return endpoint
    if not host.startswith("https://"):
        host = "https://" + host
    return f"{host.strip('/')}/{endpoint}"
