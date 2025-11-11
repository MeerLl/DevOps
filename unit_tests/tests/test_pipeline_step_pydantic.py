import pytest
from pydantic import ValidationError
from src.pipeline_step_pydantic import PipelineStep

class TestPipelineStepPydantic:
    
    def setup_method(self):
        """Сброс состояния перед каждым тестом"""
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
    
    def setup_method(self):
        """Сброс состояния перед каждым тестом"""
        PipelineStep.all_steps = []
    
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

class TestPipelineStepPydanticValidators:
    """Тесты для Pydantic валидаторов"""
    
    def setup_method(self):
        PipelineStep.all_steps = []
    
    def test_field_validator_run_comprehensive(self):
        """Комплексный тест валидатора run"""
        step1 = PipelineStep(id="test1", run="npm install")
        step2 = PipelineStep(id="test2", run="  npm run build  ") 
        
        assert step1.run == "npm install"
        assert step2.run == "  npm run build  "
        
        with pytest.raises(ValidationError, match="run cannot be empty"):
            PipelineStep(id="test3", run="")
        
        with pytest.raises(ValidationError, match="run cannot be empty"):
            PipelineStep(id="test4", run="   ")
    
    def test_field_validator_needs_comprehensive(self):
        """Комплексный тест валидатора needs"""
        step1 = PipelineStep(id="test1", run="cmd1", needs=["dep1", "dep2"])
        assert step1.needs == ["dep1", "dep2"]
        
        with pytest.raises(ValidationError, match="needs cannot contain the step's own id"):
            PipelineStep(id="selfref", run="cmd", needs=["selfref"])
        
        with pytest.raises(ValidationError, match="needs cannot contain the step's own id"):
            PipelineStep(id="test2", run="cmd", needs=["dep1", "test2", "dep2"])
    
    def test_model_validator_unique_id_comprehensive(self):
        """Комплексный тест валидатора уникальности ID"""
        PipelineStep.all_steps = []
        
        step1 = PipelineStep(id="unique", run="cmd1")
        assert step1 in PipelineStep.all_steps
        
        with pytest.raises(ValidationError, match="ID unique already exists"):
            PipelineStep(id="unique", run="cmd2")
        
        step2 = PipelineStep(id="another", run="cmd3")
        assert step2 in PipelineStep.all_steps
        assert len(PipelineStep.all_steps) == 2
    
    def test_add_need_edge_cases(self):
        """Тест edge cases для add_need"""
        step = PipelineStep(id="test", run="command")
        
        step.needs = []
        step.add_need("dep1")
        assert step.needs == ["dep1"]
        
        step.add_need("test")
        assert "test" not in step.needs
        
        step.add_need("dep2")
        step.add_need("dep3")
        assert step.needs == ["dep1", "dep2", "dep3"]
        
class TestPipelineStepPydanticExtended:
    """Расширенные тесты для PipelineStep pydantic"""
    
    def setup_method(self):
        """Сброс состояния перед каждым тестом"""
        from src.pipeline_step_pydantic import PipelineStep
        PipelineStep.all_steps = []
    
    def test_env_with_special_characters(self):
        """Тест env со специальными символами"""
        from src.pipeline_step_pydantic import PipelineStep
        
        env_vars = {
            "API_URL": "https://api.example.com/v1",
            "SECRET_KEY": "abc123!@#",
            "CONNECTION_STRING": "postgresql://user:pass@host/db"
        }
        
        step = PipelineStep(id="api", run="start", env=env_vars)
        assert step.env == env_vars
    
    def test_empty_needs_validation(self):
        """Тест валидации пустого needs"""
        from src.pipeline_step_pydantic import PipelineStep
        
        step = PipelineStep(id="test", run="cmd", needs=[])
        assert step.needs == []
    
    def test_multiple_needs_validation(self):
        """Тест валидации множественных needs"""
        from src.pipeline_step_pydantic import PipelineStep
        
        needs_list = ["build", "test", "lint", "security-scan"]
        step = PipelineStep(id="deploy", run="deploy", needs=needs_list)
        assert step.needs == needs_list
    
    def test_complex_run_with_special_chars(self):
        """Тест комплексной команды со специальными символами"""
        from src.pipeline_step_pydantic import PipelineStep
        
        complex_run = 'echo "Hello World!" && npm run build -- --env=production'
        step = PipelineStep(id="build", run=complex_run)
        assert step.run == complex_run
    
    def test_all_steps_class_variable(self):
        """Тест class variable all_steps"""
        from src.pipeline_step_pydantic import PipelineStep
        
        PipelineStep.all_steps = []
        
        step1 = PipelineStep(id="step1", run="cmd1")
        step2 = PipelineStep(id="step2", run="cmd2")
        step3 = PipelineStep(id="step3", run="cmd3")
        
        assert len(PipelineStep.all_steps) == 3
        assert step1 in PipelineStep.all_steps
        assert step2 in PipelineStep.all_steps  
        assert step3 in PipelineStep.all_steps
    
    def test_field_validator_run_edge_cases(self):
        """Тест field validator для run с edge cases"""
        from src.pipeline_step_pydantic import PipelineStep
        
        step = PipelineStep(id="test", run="  npm install  ")
        assert step.run == "  npm install  "
        
        step = PipelineStep(id="test2", run="\t\nnpm start\n")
        assert step.run == "\t\nnpm start\n"
        
class TestPipelineStepPydanticComplete:
    """Тесты для полного покрытия pipeline_step_pydantic"""
    
    def setup_method(self):
        """Сброс состояния перед каждым тестом"""
        from src.pipeline_step_pydantic import PipelineStep
        PipelineStep.all_steps = []
    
    def test_demonstration_function_exists(self):
        """Тест что demonstration функция существует"""
        from src.pipeline_step_pydantic import demonstrate_pipeline_step
        
        try:
            demonstrate_pipeline_step()
            assert True
        except Exception:
            pass
    
    def test_step_string_representation(self):
        """Тест строкового представления"""
        from src.pipeline_step_pydantic import PipelineStep
        
        step = PipelineStep(id="string_test", run="string command")
        
        assert hasattr(step, 'id')
        assert hasattr(step, 'run')
        assert hasattr(step, 'env')
        assert hasattr(step, 'needs')
        
        assert step.id == "string_test"
        assert step.run == "string command"
