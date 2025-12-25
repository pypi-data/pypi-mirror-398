import os


def is_local_temporal() -> bool:
    """
    Check if the Temporal running temporal is in a docker container or not.
    """
    temporal_host = os.getenv("TEMPORAL_HOST", "us-east-1.aws.api.temporal.io:7233")
    return any([
        temporal_host.startswith("temporal:"),
        temporal_host.startswith("host.docker.internal"),
    ])
