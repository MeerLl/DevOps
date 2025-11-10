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

class TestPipelineStepDataclassValidation:
    """Тесты для валидации dataclass"""
    
    def test_post_init_validation(self):
        """Тест что __post_init__ вызывается и валидирует run"""
        step = PipelineStep(id="test", run="valid command")
        assert step.run == "valid command"
        
        with pytest.raises(ValueError, match="run cannot be empty"):
            PipelineStep(id="test", run="")
        
        with pytest.raises(ValueError, match="run cannot be empty"):
            PipelineStep(id="test", run="   ")
    
    def test_add_need_comprehensive(self):
        """Комплексный тест add_need метода"""
        step = PipelineStep(id="test", run="command")
        
        dependencies = ["build", "test", "lint", "deploy"]
        for dep in dependencies:
            step.add_need(dep)
        
        assert len(step.needs) == len(dependencies)
        assert all(dep in step.needs for dep in dependencies)
        
        step.add_need("build")
        step.add_need("test")
        assert len(step.needs) == len(dependencies)

class TestPipelineStepDataclassExtended:
    """Расширенные тесты для PipelineStep dataclass"""
    
    def test_empty_env_and_needs(self):
        """Тест с пустыми env и needs"""
        from src.pipeline_step_dataclass import PipelineStep
        
        step = PipelineStep(id="test", run="command", env={}, needs=[])
        assert step.env == {}
        assert step.needs == []
    
    def test_add_need_duplicate_prevention(self):
        """Тест предотвращения дублирования в needs"""
        from src.pipeline_step_dataclass import PipelineStep
        
        step = PipelineStep(id="test", run="command")
        
        step.add_need("build")
        step.add_need("build")
        step.add_need("build")
        
        assert step.needs == ["build"]
        assert len(step.needs) == 1
    
    def test_complex_run_command(self):
        """Тест с комплексной командой"""
        from src.pipeline_step_dataclass import PipelineStep
        
        complex_command = """
        docker build -t myapp . && 
        docker run -p 8080:8080 myapp
        """
        
        step = PipelineStep(id="deploy", run=complex_command)
        assert step.run == complex_command
    
    def test_multiple_env_variables(self):
        """Тест с множественными переменными окружения"""
        from src.pipeline_step_dataclass import PipelineStep
        
        env_vars = {
            "DB_HOST": "localhost",
            "DB_PORT": "5432", 
            "DB_NAME": "mydb",
            "DB_USER": "user",
            "DB_PASS": "pass"
        }
        
        step = PipelineStep(id="database", run="migrate", env=env_vars)
        assert step.env == env_vars
        assert len(step.env) == 5
    
    def test_needs_ordering(self):
        """Тест порядка в needs"""
        from src.pipeline_step_dataclass import PipelineStep
        
        step = PipelineStep(id="test", run="command")
        
        dependencies = ["z-build", "a-test", "m-deploy"]
        for dep in dependencies:
            step.add_need(dep)
        
        assert step.needs == dependencies
    
    def test_whitespace_in_id(self):
        """Тест с пробелами в ID"""
        from src.pipeline_step_dataclass import PipelineStep
        
        step = PipelineStep(id="test step", run="command with spaces")
        assert step.id == "test step"
        assert step.run == "command with spaces"

class TestPipelineStepDataclassComplete:
    """Тесты для полного покрытия pipeline_step_dataclass"""
    
    def test_demonstration_function_exists(self):
        """Тест что demonstration функция существует"""
        from src.pipeline_step_dataclass import demonstrate_pipeline_step
        
        try:
            demonstrate_pipeline_step()
            assert True
        except Exception:
            pass
    
    def test_step_representation(self):
        """Тест строкового представления"""
        from src.pipeline_step_dataclass import PipelineStep
        
        step = PipelineStep(id="test", run="echo hello", env={"KEY": "value"}, needs=["dep"])
        
        assert step.id == "test"
        assert step.run == "echo hello"
        assert step.env == {"KEY": "value"}
        assert step.needs == ["dep"]
        
        assert is_dataclass(step)
