"""
Trace schema: Machine-checkable solution traces.

A Trace is a sequence of Steps that transform the initial problem state
into the final answer. Each Step is verifiable independently, enabling:
- Partial credit scoring
- Step-level RL rewards
- Error classification at specific steps
- Curriculum based on step difficulty
- Dataset generation with teacher explanations
"""

from enum import Enum
from typing import Any

from pydantic import (
    BaseModel,
    Field,
    computed_field,
    field_validator,
    model_validator,
)


class StepOperation(str, Enum):
    """
    Operations in the Step DSL.

    These are primitive operations that can appear in solution traces.
    Domains can extend with domain-specific operations.
    """

    # Core evaluation operations
    EVAL = "eval"  # Evaluate a sub-expression/constraint
    SIMPLIFY = "simplify"  # Reduce to canonical form
    LITERAL = "literal"  # Introduce a literal value

    # Arithmetic operations
    ADD = "add"
    SUBTRACT = "subtract"
    MULTIPLY = "multiply"
    DIVIDE = "divide"
    POWER = "power"

    # Algebraic rewrites
    REWRITE = "rewrite"  # Apply a general transformation rule
    DISTRIBUTE = "distribute"  # a(b+c) -> ab + ac
    FACTOR = "factor"  # ab + ac -> a(b+c)
    COMBINE_LIKE = "combine_like_terms"

    # Equation operations
    ADD_BOTH = "add_both_sides"
    SUB_BOTH = "subtract_both_sides"
    MUL_BOTH = "multiply_both_sides"
    DIV_BOTH = "divide_both_sides"
    ISOLATE = "isolate"

    # Validation operations
    SUBSTITUTE = "substitute"  # Plug in a value
    ASSERT = "assert"  # Check a condition holds

    # Fraction operations
    REDUCE = "reduce_fraction"
    COMMON_DENOM = "common_denominator"
    INVERT = "invert_fraction"

    # Puzzle/constraint operations
    PLACE = "place"  # Place a value in a cell
    ELIMINATE = "eliminate"  # Remove a candidate
    DEDUCE = "deduce"  # Logical deduction
    PROPAGATE = "propagate"  # Constraint propagation
    BACKTRACK = "backtrack"  # Undo a decision

    # Word problem operations
    EXTRACT_VARS = "extract_variables"
    BUILD_EQ = "build_equation"
    MAP_RESULT = "map_result"  # Map numeric result to answer


class StepRef(BaseModel):
    """
    Type-safe reference to a previous step's output.

    Replaces magic string placeholders with validated index-based references.

    Example:
        step.input_refs = [StepRef(step_index=0), StepRef(step_index=1)]
        # References outputs from steps 0 and 1
    """

    step_index: int = Field(ge=0, description="Index of referenced step")

    @property
    def placeholder_name(self) -> str:
        """For backward compatibility with string-based systems."""
        return f"x{self.step_index + 1}"

    def __hash__(self) -> int:
        return hash(self.step_index)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, StepRef):
            return self.step_index == other.step_index
        return False


class Step(BaseModel):
    """
    A single step in a solution trace.

    Each step represents an atomic transformation from one state to another.
    Steps are designed to be machine-verifiable: given the inputs and operation,
    the output should be deterministically computable.

    Example (arithmetic):
        Step(
            index=2,
            operation=StepOperation.MULTIPLY,
            before_state="5 * 2",
            after_state="10",
            output_value=10.0,
            rule_applied="multiplication",
            explanation="Multiply 5 by 2 to get 10",
        )

    Example (sudoku):
        Step(
            index=5,
            operation=StepOperation.PLACE,
            before_state="row=1, col=5, candidates=[3,7]",
            after_state="row=1, col=5, value=7",
            output_value=7,
            rule_applied="single_candidate",
            explanation="Only 7 can go in row 1, column 5",
        )
    """

    index: int = Field(description="Step number (0-indexed)")
    operation: StepOperation | str = Field(description="Operation performed")

    # State transition
    before_state: str = Field(description="Expression/state before this step")
    after_state: str = Field(description="Expression/state after this step")

    # Type-safe step references
    input_refs: list[StepRef] = Field(
        default_factory=list,
        description="References to input steps",
    )

    # Output value (for verification)
    output_value: Any = Field(
        default=None,
        description="Value of output (number, position, etc.)",
    )

    # Teacher explanation
    rule_applied: str | None = Field(
        default=None,
        description="Specific rule/technique applied (e.g., 'order_of_operations')",
    )
    explanation: str | None = Field(
        default=None,
        description="Natural language explanation for teaching",
    )

    # Metadata
    difficulty_cost: float = Field(
        default=1.0,
        description="Relative difficulty/cost of this step",
    )
    common_mistake_here: str | None = Field(
        default=None,
        description="Common error type at this step",
    )

    # Position info (for grid-based puzzles)
    position: tuple[int, ...] | None = Field(
        default=None,
        description="Position affected (row, col) or similar",
    )

    # Computed properties for backward compatibility
    @computed_field  # type: ignore[prop-decorator]
    @property
    def output(self) -> str:
        """Backward compatible placeholder name."""
        return f"x{self.index + 1}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def inputs(self) -> list[str]:
        """Backward compatible input placeholder names."""
        return [ref.placeholder_name for ref in self.input_refs]

    def verify_output(self, candidate: Any, tolerance: float = 1e-9) -> bool:
        """Check if a candidate value matches this step's output."""
        if self.output_value is None:
            return True  # No expected value to verify
        if isinstance(self.output_value, (int, float)) and isinstance(candidate, (int, float)):
            return abs(float(self.output_value) - float(candidate)) < tolerance
        return bool(self.output_value == candidate)

    @field_validator("input_refs")
    @classmethod
    def validate_input_refs(cls, refs: list[StepRef], info: Any) -> list[StepRef]:
        """Ensure input references point to earlier steps."""
        index = info.data.get("index", 0)
        for ref in refs:
            if ref.step_index >= index:
                raise ValueError(
                    f"Input reference to step {ref.step_index} "
                    f"must be earlier than current step {index}"
                )
        return refs


class Trace(BaseModel):
    """
    Complete solution trace for a problem.

    A Trace contains all steps needed to solve a problem, plus metadata
    for verification and reward shaping.

    Example:
        trace = Trace(
            problem_id="arith_easy_12345",
            steps=[step1, step2, step3],
            final_step_index=2,
        )
    """

    problem_id: str = Field(description="ID of the problem this trace solves")
    steps: list[Step] = Field(description="Ordered list of solution steps")

    # Checkpoints for partial credit / reward shaping
    checkpoints: list[int] = Field(
        default_factory=list,
        description="Step indices that are key milestones",
    )

    # Final answer reference
    final_step_index: int = Field(
        default=-1,
        description="Index of final answer step (-1 means last step)",
    )

    @model_validator(mode="after")
    def set_final_step_default(self) -> "Trace":
        """Set final_step_index to last step if not specified."""
        if self.final_step_index == -1 and self.steps:
            object.__setattr__(self, "final_step_index", len(self.steps) - 1)
        return self

    # Computed properties
    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_steps(self) -> int:
        """Total number of steps in the trace."""
        return len(self.steps)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_cost(self) -> float:
        """Sum of difficulty costs across all steps."""
        return sum(step.difficulty_cost for step in self.steps)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def placeholder_map(self) -> dict[str, Any]:
        """Backward compatible placeholder mapping."""
        return {step.output: step.output_value for step in self.steps}

    @computed_field  # type: ignore[prop-decorator]
    @property
    def final_placeholder(self) -> str:
        """Backward compatible final placeholder name."""
        if self.steps and 0 <= self.final_step_index < len(self.steps):
            return self.steps[self.final_step_index].output
        return ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def final_value(self) -> Any:
        """Value of final answer."""
        if self.steps and 0 <= self.final_step_index < len(self.steps):
            return self.steps[self.final_step_index].output_value
        return None

    # Methods
    def verify_step(self, step_index: int, candidate_value: Any, tolerance: float = 1e-9) -> bool:
        """Verify a single step's output."""
        if step_index < 0 or step_index >= len(self.steps):
            raise IndexError(f"Step index {step_index} out of range")
        return self.steps[step_index].verify_output(candidate_value, tolerance)

    def verify_final(self, candidate: Any, tolerance: float = 1e-9) -> bool:
        """Verify the final answer."""
        final = self.final_value
        if final is None:
            return True
        if isinstance(final, (int, float)) and isinstance(candidate, (int, float)):
            return abs(float(final) - float(candidate)) < tolerance
        return bool(final == candidate)

    def get_step_values(self) -> list[tuple[str, Any]]:
        """Get all (placeholder, value) pairs in step order."""
        return [(step.output, step.output_value) for step in self.steps]

    def get_checkpoint_values(self) -> list[Any]:
        """Get values at checkpoint steps (for partial credit)."""
        return [self.steps[i].output_value for i in self.checkpoints if i < len(self.steps)]

    def count_operations(self) -> dict[str, int]:
        """Count occurrences of each operation type."""
        counts: dict[str, int] = {}
        for step in self.steps:
            if isinstance(step.operation, StepOperation):
                op = step.operation.value
            else:
                op = step.operation
            counts[op] = counts.get(op, 0) + 1
        return counts

    def to_natural_language(self) -> str:
        """Convert trace to natural language explanation."""
        lines = []
        for step in self.steps:
            if step.explanation:
                lines.append(f"Step {step.index + 1}: {step.explanation}")
            else:
                lines.append(f"Step {step.index + 1}: {step.before_state} → {step.after_state}")
        return "\n".join(lines)

    def to_placeholder_format(self) -> str:
        """Convert trace to placeholder format (machine-readable)."""
        lines = []
        for step in self.steps:
            if step.input_refs:
                inputs_str = ", ".join(f"<{ref.placeholder_name}>" for ref in step.input_refs)
                if isinstance(step.operation, StepOperation):
                    op = step.operation.value
                else:
                    op = step.operation
                lines.append(f"STEP {step.index}: ({inputs_str}) {op} = <{step.output}>")
            else:
                lines.append(f"STEP {step.index}: <{step.output}> = {step.output_value}")
        return "\n".join(lines)

    def to_jsonl_steps(self) -> list[dict[str, Any]]:
        """Convert trace to list of dicts for JSONL export."""
        result = []
        for step in self.steps:
            if isinstance(step.operation, StepOperation):
                op = step.operation.value
            else:
                op = step.operation
            result.append(
                {
                    "index": step.index,
                    "operation": op,
                    "before": step.before_state,
                    "after": step.after_state,
                    "value": step.output_value,
                    "rule": step.rule_applied,
                    "explanation": step.explanation,
                }
            )
        return result
