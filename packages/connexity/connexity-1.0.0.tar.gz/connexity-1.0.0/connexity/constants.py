"""
Configuration constants for the Connexity library.

This module defines default endpoint URLs used throughout the library.
These are production-ready defaults that work out of the box.

Constants:
    CONNEXITY_URL (str): Main SDK processing endpoint for Connexity gateway.
    CONNEXITY_METRICS_URL (str): Metrics endpoint.
"""

CONNEXITY_URL = "https://connexity-gateway-owzhcfagkq-uc.a.run.app/process/sdk"
CONNEXITY_METRICS_URL = (
    "https://connexity-gateway-owzhcfagkq-uc.a.run.app/process/sdk/llm_latency"
)
