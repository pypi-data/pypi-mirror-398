import time
import json
import yaml
from typing import List, Any, Callable, Dict, Union
from pathlib import Path
from .image import Image

class Pipeline:
    """
    Processing pipeline engine.
    
    Allows chaining of transforms and lazy execution.
    """
    
    def __init__(self, transforms: List[Callable] = None):
        self._transforms = transforms or []
        self._execution_times = {}

    def add(self, transform: Callable) -> 'Pipeline':
        """Add a transform to the pipeline."""
        self._transforms.append(transform)
        return self

    def __call__(self, image: Image) -> Image:
        """
        Execute the pipeline on an image.
        
        Args:
            image: Input Image object.
            
        Returns:
            Processed Image object.
        """
        current_image = image
        self._execution_times = {}
        
        for i, transform in enumerate(self._transforms):
            t_start = time.perf_counter()
            
            # Support both class-based transforms (with __call__) and simple functions
            # Assuming transforms take an Image and return an Image
            current_image = transform(current_image)
            
            t_end = time.perf_counter()
            name = getattr(transform, '__class__', {}).__name__
            if name == 'function':
                name = transform.__name__
            
            # Handle duplicate names
            key = f"{i}_{name}"
            self._execution_times[key] = t_end - t_start
            
        return current_image

    def benchmark(self) -> Dict[str, float]:
        """Return execution times of the last run."""
        return self._execution_times

    def serialize(self, path: Union[str, Path] = None, format: str = "yaml") -> str:
        """
        Serialize the pipeline configuration.
        Note: This requires transforms to be serializable (e.g. have to_dict() or be standard classes).
        For now, we implement a basic schematic serialization.
        """
        pipeline_config = []
        for t in self._transforms:
            # Check if transform has a config/dict method
            if hasattr(t, "get_config"):
                config = t.get_config()
                name = t.__class__.__name__
                pipeline_config.append({"name": name, "params": config})
            else:
                # Fallback for simple callables
                pipeline_config.append({"name": str(t)})
        
        data = {"pipeline": pipeline_config}
        
        serialized = ""
        if format.lower() == "json":
            serialized = json.dumps(data, indent=2)
        elif format.lower() == "yaml":
            serialized = yaml.dump(data)
        else:
            raise ValueError("Format must be 'json' or 'yaml'")
            
        if path:
            with open(path, "w") as f:
                f.write(serialized)
                
        return serialized

    @classmethod
    def load(cls, path: Union[str, Path], transform_registry: Dict[str, Any]) -> 'Pipeline':
        """
        Load a pipeline from a file.
        
        Args:
            path: Path to YAML/JSON file.
            transform_registry: Dict mapping transform names to classes/functions in the codebase.
                                Needed to reconstruct the objects.
        """
        path = Path(path)
        with open(path, "r") as f:
            if path.suffix in [".yaml", ".yml"]:
                data = yaml.safe_load(f)
            elif path.suffix == ".json":
                data = json.load(f)
            else:
                raise ValueError("Unknown file extension")
                
        pipeline = cls()
        config_list = data.get("pipeline", [])
        
        for step in config_list:
            name = step["name"]
            params = step.get("params", {})
            
            if name not in transform_registry:
                raise ValueError(f"Unknown transform: {name}. Make sure it is registered.")
                
            transform_cls = transform_registry[name]
            # Instantiate with params
            transform_instance = transform_cls(**params)
            pipeline.add(transform_instance)
            
        return pipeline
