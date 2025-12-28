from .base import AggregationMethod, AggregationRegistry
from .federated import FederatedAggregation
from .distributed import DistributedAggregation
from .hybrid import HybridAggregation
from .custom import WeightedAverageAggregation, MedianAggregation

__all__ = [
    'AggregationMethod',
    'AggregationRegistry',
    'FederatedAggregation',
    'DistributedAggregation',
    'HybridAggregation',
    'WeightedAverageAggregation',
    'MedianAggregation',
]
