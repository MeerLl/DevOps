import pytest
import os
from unittest.mock import patch, MagicMock
from src.gen_dockerfile import DockerfileGenerator

class TestDockerfileGenerator:
    
    def test_init(self):
        generator = DockerfileGenerator()
        assert generator.config == {}
    
    @patch('builtins.input')
    def test_get_choice(self, mock_input):
        generator = DockerfileGenerator()
        mock_input.return_value = "1"
        options = ["option1", "option2", "option3"]
        result = generator.get_choice("Choose:", options)
        assert result == "option1"
    
    @patch('builtins.input')
    def test_get_choice_with_default(self, mock_input):
        generator = DockerfileGenerator()
        mock_input.return_value = ""
        options = ["option1", "option2"]
        result = generator.get_choice("Choose:", options, default="option2")
        assert result == "option2"
    
    @patch('builtins.input')
    def test_get_input(self, mock_input):
        generator = DockerfileGenerator()
        mock_input.return_value = "test_value"
        result = generator.get_input("Enter value:")
        assert result == "test_value"
    
    @patch('builtins.input')
    def test_get_input_with_default(self, mock_input):
        generator = DockerfileGenerator()
        mock_input.return_value = ""
        result = generator.get_input("Enter value:", default="default_value")
        assert result == "default_value"
    
    @patch('builtins.input')
    def test_get_yes_no_yes(self, mock_input):
        generator = DockerfileGenerator()
        mock_input.return_value = "y"
        result = generator.get_yes_no("Continue?")
        assert result is True
    
    @patch('builtins.input')
    def test_get_yes_no_no(self, mock_input):
        generator = DockerfileGenerator()
        mock_input.return_value = "n"
        result = generator.get_yes_no("Continue?")
        assert result is False
    
    def test_generate_python_dockerfile_single_stage(self):
        generator = DockerfileGenerator()
        generator.config = {
            "python_version": "3.11",
            "package_manager": "pip",
            "multi_stage": False
        }
        result = generator.generate_python_dockerfile()
        assert "FROM python:3.11-slim" in result
        assert "COPY requirements.txt ." in result
        assert "RUN pip install -r requirements.txt" in result
        assert "builder" not in result
    
    def test_generate_python_dockerfile_multi_stage(self):
        generator = DockerfileGenerator()
        generator.config = {
            "python_version": "3.11",
            "package_manager": "pip",
            "multi_stage": True
        }
        result = generator.generate_python_dockerfile()
        assert "FROM python:3.11-slim as builder" in result
        assert "COPY --from=builder" in result
    
    def test_generate_nodejs_dockerfile(self):
        generator = DockerfileGenerator()
        generator.config = {
            "node_version": "18",
            "package_manager": "npm",
            "multi_stage": False
        }
        result = generator.generate_nodejs_dockerfile()
        assert "FROM node:18-alpine" in result
        assert "npm ci" in result
        assert 'CMD ["npm", "start"]' in result
    
    def test_generate_go_dockerfile(self):
        generator = DockerfileGenerator()
        generator.config = {
            "go_version": "1.19",
            "multi_stage": True
        }
        result = generator.generate_go_dockerfile()
        assert "FROM golang:1.19 as builder" in result
        assert "COPY --from=builder" in result
        assert "go mod download" in result
    
    def test_generate_dockerignore(self):
        generator = DockerfileGenerator()
        result = generator.generate_dockerignore("python")
        assert ".git" in result
        assert "node_modules" in result
        assert "__pycache__" in result
        assert "*.pyc" in result
    
    @patch('builtins.input')
    @patch('builtins.open')
    def test_run_python_flow(self, mock_open, mock_input):
        generator = DockerfileGenerator()
        mock_input.side_effect = ["1", "3.11", "1", "n"]
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        generator.run()
        assert mock_open.call_count >= 2
        mock_file.write.assert_called()

class TestDockerfileGeneratorIntegration:
    
    def test_python_dockerfile_content(self):
        generator = DockerfileGenerator()
        generator.config = {
            "python_version": "3.9",
            "package_manager": "poetry",
            "multi_stage": True
        }
        result = generator.generate_python_dockerfile()
        lines = result.split('\n')
        assert lines[0] == "FROM python:3.9-slim as builder"
        assert "poetry install" in result
        assert "COPY . ." in result
    
    def test_all_package_managers(self):
        generators = []
        for package_manager in ["pip", "poetry", "pipenv"]:
            generator = DockerfileGenerator()
            generator.config = {
                "python_version": "3.11",
                "package_manager": package_manager,
                "multi_stage": False
            }
            generators.append((package_manager, generator.generate_python_dockerfile()))
        
        for package_manager, content in generators:
            assert "FROM python:3.11-slim" in content
            if package_manager == "poetry":
                assert "poetry" in content
            elif package_manager == "pipenv":
                assert "pipenv" in content
            else:
                assert "requirements.txt" in content

