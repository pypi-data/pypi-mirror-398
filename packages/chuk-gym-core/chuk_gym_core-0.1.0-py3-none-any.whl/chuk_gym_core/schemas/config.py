"""
Configuration schemas for reasoning gym environments.

Provides unified enums and config models used across all domains.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, computed_field


class DifficultyLevel(str, Enum):
    """
    Unified difficulty levels with consistent semantics across domains.

    7-level system that maps to specific parameter ranges:
    - VERY_EASY: Trivial problems, minimal reasoning
    - EASY: Simple problems, single-step reasoning
    - PRETTY_EASY: Slightly harder, may need 2 steps
    - MEDIUM: Moderate complexity, multi-step reasoning
    - HARD: Challenging, requires careful planning
    - PRETTY_HARD: Very challenging, deep reasoning
    - VERY_HARD: Expert level, maximum complexity
    """

    VERY_EASY = "very_easy"
    EASY = "easy"
    PRETTY_EASY = "pretty_easy"
    MEDIUM = "medium"
    HARD = "hard"
    PRETTY_HARD = "pretty_hard"
    VERY_HARD = "very_hard"

    @classmethod
    def from_simple(cls, level: str) -> "DifficultyLevel":
        """Convert simple 3-level (easy/medium/hard) to 7-level."""
        mapping = {
            "easy": cls.EASY,
            "medium": cls.MEDIUM,
            "hard": cls.HARD,
        }
        return mapping.get(level.lower(), cls.MEDIUM)

    def to_simple(self) -> str:
        """Convert 7-level to simple 3-level."""
        if self in (self.VERY_EASY, self.EASY, self.PRETTY_EASY):
            return "easy"
        elif self == self.MEDIUM:
            return "medium"
        else:
            return "hard"

    @property
    def numeric(self) -> int:
        """Numeric difficulty (1-7) for ordering and arithmetic."""
        return list(DifficultyLevel).index(self) + 1


class ToolPolicy(str, Enum):
    """Policy for tool/solver usage on a problem."""

    ALLOWED = "allowed"  # Agent may use tools freely
    FORBIDDEN = "forbidden"  # Mental reasoning only - no tools
    REQUIRED = "required"  # Agent must use specific tools
    PENALIZED = "penalized"  # Tools allowed but with score penalty


class OutputMode(str, Enum):
    """Output modes for server communication."""

    NORMAL = "normal"  # Human-friendly with explanations
    AGENT = "agent"  # AI-optimized with clear delimiters
    COMPACT = "compact"  # Minimal output for bandwidth
    STRICT = "strict"  # Machine-verifiable, fixed grammar
    JSON = "json"  # Full JSON protocol for RL integration


class SolverConfig(BaseModel):
    """
    Configuration for solver/hint usage in an environment.

    Makes solver usage a first-class experimental variable,
    enabling research comparing "small model + tools" vs "big model without tools".
    """

    model_config = ConfigDict(frozen=True)

    solver_allowed: bool = Field(
        default=True,
        description="Whether the agent can request solver hints",
    )
    hint_budget: int = Field(
        default=100,
        ge=0,
        description="Maximum number of solver hint invocations allowed",
    )
    hint_penalty: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Score penalty per hint used (0.0-1.0)",
    )
    partial_hints: bool = Field(
        default=True,
        description="If True, hints reveal one step; if False, hints reveal strategy",
    )

    @classmethod
    def solver_free(cls) -> "SolverConfig":
        """Create a solver-free configuration (pure model reasoning)."""
        return cls(solver_allowed=False, hint_budget=0)

    @classmethod
    def solver_assisted(cls, budget: int = 10, penalty: float = 0.1) -> "SolverConfig":
        """Create a solver-assisted configuration with budget and penalty."""
        return cls(solver_allowed=True, hint_budget=budget, hint_penalty=penalty)

    @classmethod
    def unlimited(cls) -> "SolverConfig":
        """Create an unlimited solver configuration (no restrictions)."""
        return cls(solver_allowed=True, hint_budget=1000, hint_penalty=0.0)


class DifficultyProfile(BaseModel):
    """
    Detailed difficulty characteristics for curriculum learning.

    Goes beyond simple easy/medium/hard to enable:
    - Curriculum learning with skill ladders
    - Fair comparisons across identical difficulty profiles
    - Automated training runs with reproducible difficulty scaling
    """

    model_config = ConfigDict(frozen=True)

    # Core difficulty dimensions
    logic_depth: int = Field(
        default=1,
        ge=1,
        le=10,
        description="Steps of deduction required (1=trivial, 10=expert)",
    )
    branching_factor: float = Field(
        default=1.0,
        ge=1.0,
        description="Average number of choices per decision point",
    )
    state_observability: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Fraction of state visible (1.0=fully observable)",
    )
    constraint_density: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Ratio of constrained cells/variables",
    )

    # Optional domain-specific metrics
    operation_count: int | None = Field(
        default=None,
        ge=0,
        description="Number of operations/moves in optimal solution",
    )
    variable_count: int | None = Field(
        default=None,
        ge=0,
        description="Number of decision variables",
    )
    domain_size: int | None = Field(
        default=None,
        ge=1,
        description="Size of value domain per variable",
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def estimated_complexity(self) -> float:
        """Composite complexity score for difficulty ordering."""
        return self.logic_depth * self.branching_factor * (2 - self.state_observability)

    @classmethod
    def from_difficulty_level(
        cls, level: DifficultyLevel, domain: str | None = None
    ) -> "DifficultyProfile":
        """Create a profile from a difficulty level with sensible defaults."""
        base_logic = {
            DifficultyLevel.VERY_EASY: 1,
            DifficultyLevel.EASY: 2,
            DifficultyLevel.PRETTY_EASY: 2,
            DifficultyLevel.MEDIUM: 4,
            DifficultyLevel.HARD: 6,
            DifficultyLevel.PRETTY_HARD: 7,
            DifficultyLevel.VERY_HARD: 8,
        }
        base_branching = {
            DifficultyLevel.VERY_EASY: 1.5,
            DifficultyLevel.EASY: 2.0,
            DifficultyLevel.PRETTY_EASY: 2.5,
            DifficultyLevel.MEDIUM: 4.0,
            DifficultyLevel.HARD: 6.0,
            DifficultyLevel.PRETTY_HARD: 7.0,
            DifficultyLevel.VERY_HARD: 9.0,
        }
        base_density = {
            DifficultyLevel.VERY_EASY: 0.7,
            DifficultyLevel.EASY: 0.6,
            DifficultyLevel.PRETTY_EASY: 0.55,
            DifficultyLevel.MEDIUM: 0.5,
            DifficultyLevel.HARD: 0.4,
            DifficultyLevel.PRETTY_HARD: 0.35,
            DifficultyLevel.VERY_HARD: 0.3,
        }

        return cls(
            logic_depth=base_logic.get(level, 3),
            branching_factor=base_branching.get(level, 3.0),
            state_observability=1.0,
            constraint_density=base_density.get(level, 0.5),
        )
