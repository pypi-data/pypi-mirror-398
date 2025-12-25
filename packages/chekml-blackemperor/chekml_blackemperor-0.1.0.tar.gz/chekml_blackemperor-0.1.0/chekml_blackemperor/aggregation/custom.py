import torch
from .base import AggregationMethod

class WeightedAverageAggregation(AggregationMethod):
    def aggregate(self, global_weights, local_results, config=None):
        """Weighted average based on accuracy or other metrics"""
        config = config or {}
        weights = config.get('weights', [1.0] * len(local_results))
        
        if len(weights) != len(local_results):
            weights = [1.0] * len(local_results)
        
        # Normalize weights
        weight_sum = sum(weights)
        normalized_weights = [w / weight_sum for w in weights]
        
        aggregated = []
        for i in range(len(local_results[0])):
            weighted_sum = torch.zeros_like(local_results[0][i])
            for j, client_weights in enumerate(local_results):
                weighted_sum += normalized_weights[j] * client_weights[i]
            aggregated.append(weighted_sum)
        
        return aggregated

class MedianAggregation(AggregationMethod):
    def aggregate(self, global_weights, local_results, config=None):
        """Median aggregation (robust to outliers)"""
        aggregated = []
        for i in range(len(local_results[0])):
            # Stack all client weights for this layer
            layer_weights = torch.stack([client_weights[i] for client_weights in local_results])
            # Take median along client dimension
            median_weights, _ = torch.median(layer_weights, dim=0)
            aggregated.append(median_weights)
        
        return aggregated
