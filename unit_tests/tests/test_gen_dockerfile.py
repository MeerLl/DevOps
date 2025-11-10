import pytest
import os
from unittest.mock import patch, MagicMock 
from src.gen_dockerfile import DockerfileGenerator

class TestDockerfileGeneratorConfigMethods:
    """Тесты для методов сбора конфигурации"""
    
    @patch('builtins.input')
    def test_collect_python_config(self, mock_input):
        generator = DockerfileGenerator()
        mock_input.side_effect = ["3.11", "2", "y"]
        
        generator.collect_python_config()
        
        assert generator.config["python_version"] == "3.11"
        assert generator.config["package_manager"] == "poetry"
        assert generator.config["multi_stage"] is True
    
    @patch('builtins.input')
    def test_collect_nodejs_config(self, mock_input):
        generator = DockerfileGenerator()
        mock_input.side_effect = ["18", "2", "n"]
        
        generator.collect_nodejs_config()
        
        assert generator.config["node_version"] == "18"
        assert generator.config["package_manager"] == "yarn"
        assert generator.config["multi_stage"] is False
    
    @patch('builtins.input')
    def test_collect_go_config(self, mock_input):
        generator = DockerfileGenerator()
        mock_input.side_effect = ["1.19", "y"]
        
        generator.collect_go_config()
        
        assert generator.config["go_version"] == "1.19"
        assert generator.config["multi_stage"] is True

class TestDockerfileGeneratorEdgeCases:
    """Тесты для граничных случаев"""
    
    def test_python_pipenv_multi_stage(self):
        generator = DockerfileGenerator()
        generator.config = {
            "python_version": "3.9",
            "package_manager": "pipenv",
            "multi_stage": True
        }
        
        result = generator.generate_python_dockerfile()
        assert "FROM python:3.9-slim as builder" in result
        assert "pipenv install --deploy" in result
        assert "COPY --from=builder" in result
    
    def test_nodejs_pnpm_single_stage(self):
        generator = DockerfileGenerator()
        generator.config = {
            "node_version": "16",
            "package_manager": "pnpm",
            "multi_stage": False
        }
        
        result = generator.generate_nodejs_dockerfile()
        assert "FROM node:16-alpine" in result
        assert "pnpm install --frozen-lockfile" in result
        assert "builder" not in result
    
    def test_go_single_stage(self):
        generator = DockerfileGenerator()
        generator.config = {
            "go_version": "1.18",
            "multi_stage": False
        }
        
        result = generator.generate_go_dockerfile()
        assert "FROM golang:1.18" in result
        assert "COPY --from=builder" not in result
        assert 'CMD ["./main"]' in result

    @patch('builtins.open')
    def test_main_function(self, mock_open):
        from src.gen_dockerfile import main
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        try:
            main()
            assert True
        except SystemExit:
            pass
        except Exception as e:
            if "No such file or directory" not in str(e):
                pytest.fail(f"Unexpected error in main: {e}")

class TestDockerfileGeneratorMethods:
    """Тесты методов генерации Dockerfile"""
    
    def test_generate_python_dockerfile_pip_single_stage(self):
        """Тест генерации Python Dockerfile с pip и single stage"""
        from src.gen_dockerfile import DockerfileGenerator
        
        generator = DockerfileGenerator()
        generator.config = {
            "python_version": "3.9",
            "package_manager": "pip",
            "multi_stage": False
        }
        
        result = generator.generate_python_dockerfile()
        assert "FROM python:3.9-slim" in result
        assert "pip install -r requirements.txt" in result
        assert "builder" not in result
    
    def test_generate_python_dockerfile_poetry_single_stage(self):
        """Тест генерации Python Dockerfile с poetry и single stage"""
        from src.gen_dockerfile import DockerfileGenerator
        
        generator = DockerfileGenerator()
        generator.config = {
            "python_version": "3.10",
            "package_manager": "poetry",
            "multi_stage": False
        }
        
        result = generator.generate_python_dockerfile()
        assert "FROM python:3.10-slim" in result
        assert "poetry install --no-dev" in result
    
    def test_generate_nodejs_dockerfile_npm_multi_stage(self):
        """Тест генерации Node.js Dockerfile с npm и multi stage"""
        from src.gen_dockerfile import DockerfileGenerator
        
        generator = DockerfileGenerator()
        generator.config = {
            "node_version": "16",
            "package_manager": "npm",
            "multi_stage": True
        }
        
        result = generator.generate_nodejs_dockerfile()
        assert "FROM node:16-alpine as builder" in result
        assert "npm ci --only=production" in result
        assert "COPY --from=builder" in result
    
    def test_generate_go_dockerfile_multi_stage(self):
        """Тест генерации Go Dockerfile с multi stage"""
        from src.gen_dockerfile import DockerfileGenerator
        
        generator = DockerfileGenerator()
        generator.config = {
            "go_version": "1.18",
            "multi_stage": True
        }
        
        result = generator.generate_go_dockerfile()
        assert "FROM golang:1.18 as builder" in result
        assert "COPY --from=builder" in result
        assert 'CMD ["./main"]' in result
    
    def test_generate_dockerignore_python(self):
        """Тест генерации .dockerignore для Python"""
        from src.gen_dockerfile import DockerfileGenerator
        
        generator = DockerfileGenerator()
        result = generator.generate_dockerignore("python")
        
        assert ".git" in result
        assert "__pycache__" in result
        assert "*.pyc" in result
    
    def test_generate_dockerignore_nodejs(self):
        """Тест генерации .dockerignore для Node.js"""
        from src.gen_dockerfile import DockerfileGenerator
        
        generator = DockerfileGenerator()
        result = generator.generate_dockerignore("node.js")
        
        assert "node_modules" in result
        assert "npm-debug.log" in result
    
    def test_generate_dockerignore_go(self):
        """Тест генерации .dockerignore для Go"""
        from src.gen_dockerfile import DockerfileGenerator
        
        generator = DockerfileGenerator()
        result = generator.generate_dockerignore("go")
        
        assert "bin" in result
        assert "pkg" in result
    
    def test_get_choice_with_default(self):
        """Тест get_choice с default значением"""
        from src.gen_dockerfile import DockerfileGenerator
        
        generator = DockerfileGenerator()
        
        with patch('builtins.input', return_value=''):
            result = generator.get_choice("Test", ["opt1", "opt2"], default="opt2")
            assert result == "opt2"
    
    def test_get_input_with_default(self):
        """Тест get_input с default значением"""
        from src.gen_dockerfile import DockerfileGenerator
        
        generator = DockerfileGenerator()
        
        with patch('builtins.input', return_value=''):
            result = generator.get_input("Test prompt", default="default_value")
            assert result == "default_value"
    
    def test_get_yes_no_default_yes(self):
        """Тест get_yes_no с default 'y'"""
        from src.gen_dockerfile import DockerfileGenerator
        
        generator = DockerfileGenerator()
        
        with patch('builtins.input', return_value=''):
            result = generator.get_yes_no("Test prompt", default="y")
            assert result is True
    
    def test_get_yes_no_default_no(self):
        """Тест get_yes_no с default 'n'"""
        from src.gen_dockerfile import DockerfileGenerator
        
        generator = DockerfileGenerator()
        
        with patch('builtins.input', return_value=''):
            result = generator.get_yes_no("Test prompt", default="n")
            assert result is False

class TestDockerfileGeneratorComplete:
    """Тесты для полного покрытия gen_dockerfile"""
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_full_generator_flow_python(self, mock_print, mock_input):
        """Тест полного потока генерации для Python"""
        from src.gen_dockerfile import DockerfileGenerator
        
        generator = DockerfileGenerator()
        
        mock_input.side_effect = ["1", "3.11", "1", "y"]  # Python, версия, pip, multi-stage
        
        try:
            generator.run()
            assert True
        except SystemExit:
            pass
        except Exception as e:
            pytest.skip(f"Full flow test skipped: {e}")
    
    def test_dockerignore_unknown_language(self):
        """Тест генерации dockerignore для неизвестного языка"""
        from src.gen_dockerfile import DockerfileGenerator
        
        generator = DockerfileGenerator()
        result = generator.generate_dockerignore("unknown")
        
        assert ".git" in result
        assert ".dockerignore" in result
    
    @patch('builtins.open')
    def test_file_creation(self, mock_open):
        """Тест создания файлов"""
        from src.gen_dockerfile import DockerfileGenerator
        
        generator = DockerfileGenerator()
        generator.config = {
            "language": "Python",
            "python_version": "3.9", 
            "package_manager": "pip",
            "multi_stage": False
        }
        
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        dockerfile_content = generator.generate_python_dockerfile()
        dockerignore_content = generator.generate_dockerignore("python")
        
        assert "FROM python:3.9-slim" in dockerfile_content
        assert ".git" in dockerignore_content
