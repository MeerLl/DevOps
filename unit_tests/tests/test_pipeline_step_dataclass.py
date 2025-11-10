import pytest
from dataclasses import is_dataclass
from src.pipeline_step_dataclass import PipelineStep

class TestPipelineStepDataclass:
    
    def test_is_dataclass(self):
        assert is_dataclass(PipelineStep)
    
    def test_initialization(self):
        step = PipelineStep(
            id="test_step",
            run="npm run test",
            env={"NODE_ENV": "test"},
            needs=["build"]
        )
        assert step.id == "test_step"
        assert step.run == "npm run test"
        assert step.env == {"NODE_ENV": "test"}
        assert step.needs == ["build"]
    
    def test_default_values(self):
        step = PipelineStep(id="test", run="some command")
        assert step.env == {}
        assert step.needs == []
    
    def test_add_need(self):
        step = PipelineStep(id="test", run="command")
        step.add_need("build")
        step.add_need("lint")
        step.add_need("build")
        assert step.needs == ["build", "lint"]
        assert len(step.needs) == 2
    
    def test_empty_run_validation(self):
        with pytest.raises(ValueError, match="run cannot be empty"):
            PipelineStep(id="test", run="")
    
    def test_whitespace_only_run_validation(self):
        with pytest.raises(ValueError, match="run cannot be empty"):
            PipelineStep(id="test", run="   ")
    
    def test_valid_run_with_whitespace(self):
        step = PipelineStep(id="test", run="  npm install  ")
        assert step.run == "  npm install  "
    
    def test_complex_environment(self):
        complex_env = {
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "API_KEY": "secret123"
        }
        step = PipelineStep(
            id="deploy",
            run="docker deploy",
            env=complex_env,
            needs=["build", "test"]
        )
        assert step.env == complex_env
        assert len(step.needs) == 2

class TestPipelineStepEdgeCases:
    
    def test_special_characters_in_id(self):
        step = PipelineStep(id="step-with-dashes", run="command")
        assert step.id == "step-with-dashes"
    
    def test_long_command(self):
        long_command = " && ".join([f"echo {i}" for i in range(10)])
        step = PipelineStep(id="test", run=long_command)
        assert step.run == long_command
    
    def test_multiple_needs_operations(self):
        step = PipelineStep(id="test", run="cmd")
        for i in range(5):
            step.add_need(f"step_{i}")
        step.add_need("step_0")
        step.add_need("step_1")
        assert len(step.needs) == 5
        assert all(f"step_{i}" in step.needs for i in range(5))
