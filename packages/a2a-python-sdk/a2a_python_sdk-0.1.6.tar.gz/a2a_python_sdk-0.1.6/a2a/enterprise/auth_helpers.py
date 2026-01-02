def validate_scope(scopes: list[str], required: list[str]):
    return all(s in scopes for s in required)


def enforce_mtls(cert_info):
    # placeholder for mTLS enforcement
    if not cert_info.get("verified"):
        raise PermissionError("mTLS not verified")
