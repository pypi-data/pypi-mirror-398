def extract_identity_from_cert(cert: dict):
    """
    cert is request.scope['ssl_object'].getpeercert()
    """
    subject = dict(x[0] for x in cert["subject"])
    cn = subject.get("commonName")

    # Example: agent:infra-agent
    kind, name = cn.split(":", 1)

    return {
        "id": name,
        "type": kind,
        "role": kind
    }
