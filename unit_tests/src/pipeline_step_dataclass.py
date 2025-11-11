from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class PipelineStep:
    id: str
    run: str
    env: Dict[str, str] = field(default_factory=dict)
    needs: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate that run is not empty."""
        if not self.run.strip():
            raise ValueError("run cannot be empty")

    def add_need(self, step_id: str) -> None:
        """Add a step ID to the needs list if not already present."""
        if step_id not in self.needs:
            self.needs.append(step_id)

# Demonstration examples
def demonstrate_pipeline_step():
    # Successful scenario
    print("=== Successful Scenario ===")
    try:
        step1 = PipelineStep(id="build", run="npm run build", env={"NODE_ENV": "production"})
        step1.add_need("test")
        print(f"Step 1: {step1}")

        step2 = PipelineStep(id="test", run="npm test")
        step2.add_need("lint")
        print(f"Step 2: {step2}")

    except ValueError as e:
        print(f"Unexpected error in successful scenario: {e}")

    # Unsuccessful scenario - empty run string
    print("\n=== Unsuccessful Scenario ===")
    try:
        invalid_step = PipelineStep(id="invalid", run="")
        print(invalid_step)  # This line won't execute
    except ValueError as e:
        print(f"Error (empty run): {e}")

if __name__ == "__main__":
    demonstrate_pipeline_step()
