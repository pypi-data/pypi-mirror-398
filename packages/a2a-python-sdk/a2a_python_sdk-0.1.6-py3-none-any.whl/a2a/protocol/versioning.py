A2A_PROTOCOL = "A2A"

SUPPORTED_VERSIONS = ["1.0"]

def negotiate_version(peer_versions: list[str]) -> str:
    """
    Select highest mutually supported version
    """
    for v in sorted(SUPPORTED_VERSIONS, reverse=True):
        if v in peer_versions:
            return v
    raise RuntimeError("No compatible A2A protocol version found")
