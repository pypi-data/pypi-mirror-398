from .base import AggregationMethod
from .federated import FederatedAggregation
from .distributed import DistributedAggregation

class HybridAggregation(AggregationMethod):
    def aggregate(self, global_weights, local_results, config=None):
        """Hybrid aggregation - chooses based on number of workers"""
        config = config or {}
        threshold = config.get('threshold', 5)
        
        if len(local_results) > threshold:
            # Use distributed for many workers
            distributed = DistributedAggregation()
            return distributed.aggregate(global_weights, local_results, config)
        else:
            # Use federated for few workers
            federated = FederatedAggregation()
            return federated.aggregate(global_weights, local_results, config)
