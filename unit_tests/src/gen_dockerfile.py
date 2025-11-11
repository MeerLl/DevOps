import os
from pathlib import Path

class DockerfileGenerator:
    def __init__(self):
        self.config = {}
        
    def get_choice(self, prompt, options, default=None):
        """Получить выбор пользователя из списка опций"""
        print(prompt)
        for i, option in enumerate(options, 1):
            print(f"{i}) {option}")
        
        while True:
            choice = input("> ").strip()
            if not choice and default is not None:
                return default
            try:
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(options):
                    return options[choice_idx]
            except ValueError:
                pass
            print("Неверный выбор. Попробуйте снова.")
    
    def get_input(self, prompt, default=None):
        """Получить ввод от пользователя"""
        if default:
            prompt = f"{prompt} ({default})"
        prompt += "\n> "
        
        user_input = input(prompt).strip()
        return user_input if user_input else default
    
    def get_yes_no(self, prompt, default="n"):
        """Получить ответ да/нет"""
        default_text = "y" if default == "y" else "n"
        response = input(f"{prompt} (y/n) (default: {default_text})\n> ").strip().lower()
        
        if not response:
            return default == "y"
        return response in ["y", "yes", "да"]
    
    def collect_python_config(self):
        """Собрать конфигурацию для Python"""
        self.config["python_version"] = self.get_input("Python version", "3.11")
        
        package_managers = ["pip", "poetry", "pipenv"]
        self.config["package_manager"] = self.get_choice(
            "Package manager:", 
            package_managers
        )
        
        self.config["multi_stage"] = self.get_yes_no("Multi-stage build?", "y")
    
    def collect_nodejs_config(self):
        """Собрать конфигурацию для Node.js"""
        self.config["node_version"] = self.get_input("Node.js version", "18")
        
        package_managers = ["npm", "yarn", "pnpm"]
        self.config["package_manager"] = self.get_choice(
            "Package manager:", 
            package_managers
        )
        
        self.config["multi_stage"] = self.get_yes_no("Multi-stage build?", "y")
    
    def collect_go_config(self):
        """Собрать конфигурацию для Go"""
        self.config["go_version"] = self.get_input("Go version", "1.19")
        self.config["multi_stage"] = self.get_yes_no("Multi-stage build?", "y")
    
    def generate_python_dockerfile(self):
        """Сгенерировать Dockerfile для Python"""
        version = self.config["python_version"]
        package_manager = self.config["package_manager"]
        multi_stage = self.config["multi_stage"]
        
        lines = []
        
        if multi_stage:
            # Multi-stage build
            lines.extend([
                f"FROM python:{version}-slim as builder",
                "WORKDIR /app",
            ])
            
            if package_manager == "poetry":
                lines.extend([
                    "COPY pyproject.toml poetry.lock ./",
                    "RUN pip install poetry && poetry install --no-dev",
                    "",
                    f"FROM python:{version}-slim",
                    "WORKDIR /app",
                    "COPY --from=builder /app/.venv .venv",
                ])
            elif package_manager == "pipenv":
                lines.extend([
                    "COPY Pipfile Pipfile.lock ./",
                    "RUN pip install pipenv && pipenv install --deploy",
                    "",
                    f"FROM python:{version}-slim",
                    "WORKDIR /app",
                    "COPY --from=builder /root/.local/share/virtualenvs /root/.local/share/virtualenvs",
                ])
            else:  # pip
                lines.extend([
                    "COPY requirements.txt .",
                    "RUN pip install --user -r requirements.txt",
                    "",
                    f"FROM python:{version}-slim",
                    "WORKDIR /app",
                    "COPY --from=builder /root/.local /root/.local",
                    "ENV PATH=/root/.local/bin:$PATH",
                ])
        else:
            lines.extend([
                f"FROM python:{version}-slim",
                "WORKDIR /app",
            ])
            
            if package_manager == "poetry":
                lines.extend([
                    "COPY pyproject.toml poetry.lock ./",
                    "RUN pip install poetry && poetry install --no-dev",
                ])
            elif package_manager == "pipenv":
                lines.extend([
                    "COPY Pipfile Pipfile.lock ./",
                    "RUN pip install pipenv && pipenv install --deploy",
                ])
            else:  # pip
                lines.extend([
                    "COPY requirements.txt .",
                    "RUN pip install -r requirements.txt",
                ])
        

        lines.extend([
            "COPY . .",
            'HEALTHCHECK CMD curl -f http://localhost:8080/health || exit 1',
        ])
        
        if package_manager == "poetry":
            lines.append('CMD [".venv/bin/python", "main.py"]')
        elif package_manager == "pipenv":
            lines.append('CMD ["pipenv", "run", "python", "main.py"]')
        else:
            lines.append('CMD ["python", "main.py"]')
        
        return "\n".join(lines)
    
    def generate_nodejs_dockerfile(self):
        """Сгенерировать Dockerfile для Node.js"""
        version = self.config["node_version"]
        package_manager = self.config["package_manager"]
        multi_stage = self.config["multi_stage"]
        
        lines = []
        
        if multi_stage:
            # Multi-stage build
            lines.extend([
                f"FROM node:{version}-alpine as builder",
                "WORKDIR /app",
                "COPY package*.json .",
            ])
            
            if package_manager == "yarn":
                lines.append("RUN yarn install --frozen-lockfile --production")
            elif package_manager == "pnpm":
                lines.append("RUN pnpm install --frozen-lockfile --production")
            else:  # npm
                lines.append("RUN npm ci --only=production")
            
            lines.extend([
                "",
                f"FROM node:{version}-alpine",
                "WORKDIR /app",
                "COPY --from=builder /app/node_modules ./node_modules",
            ])
        else:
            # Single stage
            lines.extend([
                f"FROM node:{version}-alpine",
                "WORKDIR /app",
                "COPY package*.json .",
            ])
            
            if package_manager == "yarn":
                lines.append("RUN yarn install --frozen-lockfile")
            elif package_manager == "pnpm":
                lines.append("RUN pnpm install --frozen-lockfile")
            else:  # npm
                lines.append("RUN npm ci")
        

        lines.extend([
            "COPY . .",
            'HEALTHCHECK CMD curl -f http://localhost:3000/health || exit 1',
        ])
        
        if package_manager == "yarn":
            lines.append('CMD ["yarn", "start"]')
        elif package_manager == "pnpm":
            lines.append('CMD ["pnpm", "start"]')
        else:
            lines.append('CMD ["npm", "start"]')
        
        return "\n".join(lines)
    
    def generate_go_dockerfile(self):
        """Сгенерировать Dockerfile для Go"""
        version = self.config["go_version"]
        multi_stage = self.config["multi_stage"]
        
        lines = []
        
        if multi_stage:
            # Multi-stage build
            lines.extend([
                f"FROM golang:{version} as builder",
                "WORKDIR /app",
                "COPY go.mod go.sum ./",
                "RUN go mod download",
                "COPY . .",
                "RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o main .",
                "",
                "FROM alpine:latest",
                "RUN apk --no-cache add ca-certificates",
                "WORKDIR /root/",
                "COPY --from=builder /app/main .",
            ])
        else:
            # Single stage
            lines.extend([
                f"FROM golang:{version}",
                "WORKDIR /app",
                "COPY go.mod go.sum ./",
                "RUN go mod download",
                "COPY . .",
            ])
        

        lines.extend([
            'HEALTHCHECK CMD curl -f http://localhost:8080/health || exit 1',
        ])
        
        if multi_stage:
            lines.append('CMD ["./main"]')
        else:
            lines.append('RUN CGO_ENABLED=0 GOOS=linux go build -o main .')
            lines.append('CMD ["./main"]')
        
        return "\n".join(lines)
    
    def generate_dockerignore(self, language):
        """Сгенерировать .dockerignore файл"""
        common_ignores = [
            ".git",
            ".gitignore",
            ".dockerignore",
            "Dockerfile",
            "README.md",
            ".env",
            "node_modules",
            "__pycache__",
            "*.pyc",
            ".venv",
            "venv",
        ]
        
        language_specific = {
            "python": ["*.egg-info", "dist", "build"],
            "node.js": ["npm-debug.log*", "yarn-debug.log*", "yarn-error.log*"],
            "go": ["bin", "pkg"],
        }
        
        ignores = common_ignores + language_specific.get(language.lower(), [])
        return "\n".join(ignores)
    
    def run(self):
        """Запустить генератор"""
        print("Dockerfile Generator")
        print("=" * 50)
        
        languages = ["Python", "Node.js", "Go"]
        language = self.get_choice("Language:", languages)
        self.config["language"] = language
        

        if language == "Python":
            self.collect_python_config()
            dockerfile_content = self.generate_python_dockerfile()
        elif language == "Node.js":
            self.collect_nodejs_config()
            dockerfile_content = self.generate_nodejs_dockerfile()
        else:  # Go
            self.collect_go_config()
            dockerfile_content = self.generate_go_dockerfile()
        
    
        print("\nGenerating Dockerfile...")
        
        
        with open("Dockerfile", "w") as f:
            f.write(dockerfile_content)
        print("✅ Created Dockerfile")
        
    
        dockerignore_content = self.generate_dockerignore(language)
        with open(".dockerignore", "w") as f:
            f.write(dockerignore_content)
        print("✅ Created .dockerignore")
        
    
        print("\nPreview:")
        print("_" * 70)
        print(dockerfile_content)
        print("_" * 70)

def main():
    try:
        generator = DockerfileGenerator()
        generator.run()
    except KeyboardInterrupt:
        print("\n\nГенерация прервана пользователем.")
    except Exception as e:
        print(f"\nПроизошла ошибка: {e}")

if __name__ == "__main__":
    main()