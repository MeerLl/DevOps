import pytest
from pydantic import ValidationError
from src.pipeline_step_pydantic import PipelineStep

class TestPipelineStepPydantic:
    
    def setup_method(self):
        PipelineStep.all_steps = []
    
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
        assert step in PipelineStep.all_steps
    
    def test_default_values(self):
        step = PipelineStep(id="test", run="some command")
        assert step.env == {}
        assert step.needs == []
    
    def test_add_need(self):
        step = PipelineStep(id="test", run="command")
        step.add_need("build")
        step.add_need("lint")
        assert step.needs == ["build", "lint"]
    
    def test_add_need_prevents_self_reference(self):
        step = PipelineStep(id="test", run="command")
        step.add_need("test")
        assert "test" not in step.needs
    
    def test_empty_run_validation(self):
        with pytest.raises(ValidationError, match="run cannot be empty"):
            PipelineStep(id="test", run="")
    
    def test_self_dependency_validation(self):
        with pytest.raises(ValidationError, match="needs cannot contain the step's own id"):
            PipelineStep(id="selfdep", run="command", needs=["selfdep"])
    
    def test_unique_id_validation(self):
        PipelineStep(id="unique", run="command1")
        with pytest.raises(ValidationError, match="ID unique already exists"):
            PipelineStep(id="unique", run="command2")
    
    def test_whitespace_run_validation(self):
        with pytest.raises(ValidationError, match="run cannot be empty"):
            PipelineStep(id="test", run="   ")
    
    def test_valid_run_with_whitespace(self):
        step = PipelineStep(id="test", run="  npm install  ")
        assert step.run == "  npm install  "

class TestPipelineStepPydanticEdgeCases:
    
    def test_multiple_steps_different_ids(self):
        steps = [
            PipelineStep(id=f"step_{i}", run=f"command_{i}")
            for i in range(5)
        ]
        assert len(PipelineStep.all_steps) == 5
        assert all(step in PipelineStep.all_steps for step in steps)
    
    def test_complex_needs_scenario(self):
        step1 = PipelineStep(id="build", run="build cmd")
        step2 = PipelineStep(id="test", run="test cmd", needs=["build"])
        step3 = PipelineStep(id="deploy", run="deploy cmd", needs=["build", "test"])
        assert step2.needs == ["build"]
        assert set(step3.needs) == {"build", "test"}
    
    def test_env_variable_handling(self):
        complex_env = {
            "DATABASE_URL": "postgresql://user:pass@localhost/db",
            "DEBUG": "true",
            "PORT": "8000"
        }
        step = PipelineStep(
            id="api",
            run="node server.js",
            env=complex_env
        )
        assert step.env == complex_env
    
    def test_reset_all_steps(self):
        step = PipelineStep(id="new_step", run="command")
        assert len(PipelineStep.all_steps) == 1
        assert PipelineStep.all_steps[0].id == "new_step"
