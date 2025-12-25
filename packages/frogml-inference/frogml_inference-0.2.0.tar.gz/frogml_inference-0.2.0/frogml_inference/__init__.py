from frogml_inference.configuration.log_config import logger
from frogml_inference.realtime_client import RealTimeClient

clients = ["RealTimeClient"]
try:
    from frogml import wire_dependencies

    from frogml_inference.batch_client.batch_client import BatchInferenceClient

    clients.extend(["BatchInferenceClient"])

    wire_dependencies()
except ImportError:
    # We are conditional loading these clients since the skinny does
    # not support them due to the pandas, numpy, joblib, etc. dependencies
    logger.debug(
        "Notice that BatchInferenceClient is not available in the skinny package. "
        'In order to use it, please install them as extras: pip install "frogml-inference[batch]".'
    )

__all__ = clients

__version__ = "0.2.0"
