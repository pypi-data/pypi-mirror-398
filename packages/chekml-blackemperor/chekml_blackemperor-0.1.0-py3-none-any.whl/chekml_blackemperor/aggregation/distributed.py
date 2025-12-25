import torch
from .base import AggregationMethod

class DistributedAggregation(AggregationMethod):
    def aggregate(self, global_weights, local_results, config=None):
        """Aggregate gradients for distributed training"""
        if not global_weights or not local_results:
            return global_weights
        
        config = config or {}
        learning_rate = config.get('learning_rate', 0.01)
        
        num_clients = len(local_results)
        aggregated_grads = []
        
        for i in range(len(local_results[0])):
            grad_sum = torch.zeros_like(local_results[0][i])
            for client_grads in local_results:
                grad_sum += client_grads[i]
            aggregated_grads.append(grad_sum / num_clients)
        
        # Update weights: w = w - lr * avg_grad
        updated_weights = []
        for w, g in zip(global_weights, aggregated_grads):
            updated_weights.append(w - learning_rate * g)
        
        return updated_weights
