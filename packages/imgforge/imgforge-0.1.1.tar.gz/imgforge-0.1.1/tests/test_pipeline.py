from newlib.core.pipeline import Pipeline
from newlib.core.image import Image
from newlib.transforms import geometric, color
import pytest
import os
import json

def test_pipeline_execution(sample_image):
    pipe = Pipeline([
        geometric.Resize(50, 50),
        color.ToGray()
    ])
    result = pipe(sample_image)
    assert result.width == 50
    assert result.color_space == "GRAY"
    assert "0_Resize" in pipe.benchmark()

def test_pipeline_serialization(tmp_path):
    pipe = Pipeline([
        geometric.Resize(100, 100),
        color.ToGray()
    ])
    
    # Save to json for simple check
    path = tmp_path / "pipe.json"
    pipe.serialize(path, format="json")
    
    assert path.exists()
    with open(path) as f:
        data = json.load(f)
        assert len(data["pipeline"]) == 2
        assert data["pipeline"][0]["name"] == "Resize"
