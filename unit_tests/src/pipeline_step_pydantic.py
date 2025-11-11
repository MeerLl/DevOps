from pydantic import BaseModel, field_validator, model_validator, ValidationError
from typing import Dict, List, ClassVar

class PipelineStep(BaseModel):
    id: str
    run: str
    env: Dict[str, str] = {}
    needs: List[str] = []
    all_steps: ClassVar[List['PipelineStep']] = []

    @field_validator('run')
    @classmethod
    def validate_run(cls, value: str) -> str:
        """Ensure run is not empty."""
        if not value.strip():
            raise ValueError("run cannot be empty")
        return value

    @field_validator('needs')
    @classmethod
    def validate_needs(cls, value: List[str], info: 'pydantic.ValidationInfo') -> List[str]:
        """Ensure needs does not contain the step's own id."""
        if 'id' in info.data and info.data['id'] in value:
            raise ValueError("needs cannot contain the step's own id")
        return value

    @model_validator(mode='after')
    def validate_unique_id(self) -> 'PipelineStep':
        """Ensure id is unique among all steps."""
        if any(step.id == self.id for step in PipelineStep.all_steps):
            raise ValueError(f"ID {self.id} already exists")
        PipelineStep.all_steps.append(self)
        return self

    def add_need(self, step_id: str) -> None:
        """Add a step ID to the needs list if not already present and not self.id."""
        if step_id != self.id and step_id not in self.needs:
            self.needs.append(step_id)

# Demonstration examples
def demonstrate_pipeline_step():
    # Reset all_steps for demonstration
    PipelineStep.all_steps = []

    # Successful scenario
    print("=== Successful Scenario ===")
    try:
        step1 = PipelineStep(id="build", run="npm run build", env={"NODE_ENV": "production"})
        step1.add_need("test")
        print(f"Step 1: {step1}")

        step2 = PipelineStep(id="test", run="npm test")
        step2.add_need("lint")
        print(f"Step 2: {step2}")

    except ValidationError as e:
        print(f"Unexpected error: {e}")

    # Unsuccessful scenarios
    print("\n=== Unsuccessful Scenarios ===")
    # 1. Empty run
    try:
        invalid_step = PipelineStep(id="invalid", run="")
        print(invalid_step)  # This line won't execute
    except ValidationError as e:
        print(f"Error (empty run): {e}")

    # 2. Duplicate ID
    try:
        duplicate_step = PipelineStep(id="build", run="npm run build")
        print(duplicate_step)  # This line won't execute
    except ValidationError as e:
        print(f"Error (duplicate ID): {e}")

    # 3. Self-dependency in needs
    try:
        self_dep_step = PipelineStep(id="selfdep", run="npm run self", needs=["selfdep"])
        print(self_dep_step)  # This line won't execute
    except ValidationError as e:
        print(f"Error (self-dependency): {e}")

if __name__ == "__main__":
    demonstrate_pipeline_step()
