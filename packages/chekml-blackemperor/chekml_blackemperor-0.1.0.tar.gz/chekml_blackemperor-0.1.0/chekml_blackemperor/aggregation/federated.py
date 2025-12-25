import torch
from .base import AggregationMethod

class FederatedAggregation(AggregationMethod):
    def aggregate(self, global_weights, local_results, config=None):
        """Average weights (FedAvg)"""
        if not local_results:
            return global_weights
        
        num_clients = len(local_results)
        aggregated = []
        
        for i in range(len(local_results[0])):
            layer_sum = torch.zeros_like(local_results[0][i])
            for client_weights in local_results:
                layer_sum += client_weights[i]
            aggregated.append(layer_sum / num_clients)
        
        return aggregated
