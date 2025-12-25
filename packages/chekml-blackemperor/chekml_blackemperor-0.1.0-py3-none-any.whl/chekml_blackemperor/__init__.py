"""
ChekML - Cross-machine training system
"""

__version__ = "0.1.0"
__author__ = "Chek Chee Him"

from .server import ChekMLServer
from .worker import ChekMLWorker
from .aggregation.base import AggregationMethod, AggregationRegistry
from .aggregation.federated import FederatedAggregation
from .aggregation.distributed import DistributedAggregation
from .aggregation.hybrid import HybridAggregation
from .aggregation.custom import WeightedAverageAggregation, MedianAggregation
from .utils import get_available_gpus, GoogleDriveClient
from .config import ServerConfig, WorkerConfig

__all__ = [
    'ChekMLServer',
    'ChekMLWorker',
    'AggregationMethod',
    'AggregationRegistry',
    'FederatedAggregation',
    'DistributedAggregation',
    'HybridAggregation',
    'WeightedAverageAggregation',
    'MedianAggregation',
    'get_available_gpus',
    'GoogleDriveClient',
    'ServerConfig',
    'WorkerConfig'
]
