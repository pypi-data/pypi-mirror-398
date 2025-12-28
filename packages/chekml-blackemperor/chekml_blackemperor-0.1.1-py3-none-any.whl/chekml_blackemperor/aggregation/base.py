from abc import ABC, abstractmethod
from typing import List, Any, Dict, Optional
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
    
    def on_intermediate(self, global_weights: List[torch.Tensor], local_payload: Any, config: Dict[str, Any] = None) -> Optional[Any]:
        """
        Optional hook called when workers send intermediate data during training (e.g. after forward/backward).

        Args:
            global_weights: current global model weights (list of tensors)
            local_payload: arbitrary payload sent by a worker (e.g. grad norms, activations)
            config: aggregator-specific config

        Returns:
            Optional value. If returning a dict that contains a 'weights' key with a state-like dict/list
            of tensors, the server will attempt to apply and broadcast those weights as an update.
            Otherwise the return value is ignored.
        """
        return None

class AggregationRegistry:
    def __init__(self):
        self.methods = {}
    
    def register(self, name: str, aggregator: AggregationMethod):
        self.methods[name] = aggregator
    
    def get(self, name: str) -> AggregationMethod:
        return self.methods.get(name)
    
    def list(self):
        return list(self.methods.keys())

