from abc import ABC, abstractmethod
from typing import List, Any, Dict
import torch

class AggregationMethod(ABC):
    @abstractmethod
    def aggregate(self, global_weights: List[torch.Tensor], 
                 local_results: List[List[torch.Tensor]],
                 config: Dict[str, Any] = None) -> List[torch.Tensor]:
        """
        Aggregate results from multiple workers.
        
        Args:
            global_weights: Current global model weights
            local_results: List of results from each worker
            config: Additional configuration parameters
        
        Returns:
            Aggregated weights
        """
        pass

class AggregationRegistry:
    def __init__(self):
        self.methods = {}
    
    def register(self, name: str, aggregator: AggregationMethod):
        self.methods[name] = aggregator
    
    def get(self, name: str) -> AggregationMethod:
        return self.methods.get(name)
    
    def list(self):
        return list(self.methods.keys())

