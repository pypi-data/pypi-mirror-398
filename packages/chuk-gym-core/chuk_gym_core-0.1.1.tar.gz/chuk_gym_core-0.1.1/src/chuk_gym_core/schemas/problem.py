"""
Problem schema: The canonical representation of a reasoning task.

A Problem is the fundamental unit of work in chuk-gym-core. It contains:
- The question/prompt to present to the agent
- The initial state (grid, expression, etc.)
- Tool policy constraints
- Difficulty metadata for curriculum learning

This schema works for both math expressions and logic puzzles.
"""

import hashlib
from typing import Any

from pydantic import BaseModel, Field

from chuk_gym_core.schemas.config import (
    DifficultyLevel,
    DifficultyProfile,
    ToolPolicy,
)


class Problem(BaseModel):
    """
    Canonical problem representation for all reasoning domains.

    Works for math expressions, logic puzzles, constraint satisfaction,
    and optimization problems.

    Example (arithmetic):
        problem = Problem(
            id="arithmetic_easy_12345",
            seed=12345,
            domain="arithmetic",
            difficulty=DifficultyLevel.EASY,
            prompt="What is 3 + 5 * 2?",
            initial_state="3 + 5 * 2",
            gold_answer="13",
        )

    Example (sudoku):
        problem = Problem(
            id="sudoku_medium_42",
            seed=42,
            domain="sudoku",
            difficulty=DifficultyLevel.MEDIUM,
            prompt="Solve the following Sudoku puzzle.",
            initial_state=[[5, 3, 0, ...], ...],  # 9x9 grid
            gold_answer=None,  # Validated by is_complete()
        )
    """

    # Identity
    id: str = Field(description="Unique problem identifier")
    seed: int = Field(description="Deterministic seed for reproducibility")

    # Classification
    domain: str = Field(description="Domain identifier (e.g., 'arithmetic', 'sudoku')")
    difficulty: DifficultyLevel = Field(description="Difficulty level")

    # Content
    prompt: str = Field(description="Natural language question/instruction")
    initial_state: Any = Field(
        default=None,
        description="Initial problem state (grid, expression, etc.)",
    )
    expression: str | None = Field(
        default=None,
        description="Mathematical expression (if applicable)",
    )

    # Solution
    gold_answer: str | None = Field(
        default=None,
        description="Canonical correct answer (if applicable)",
    )
    answer_tolerance: float | None = Field(
        default=None,
        description="Numeric tolerance for approximate answers",
    )

    # Tool policy
    tool_policy: ToolPolicy = Field(
        default=ToolPolicy.ALLOWED,
        description="Whether tools can be used",
    )
    allowed_tools: list[str] | None = Field(
        default=None,
        description="Specific tools allowed (if tool_policy is ALLOWED)",
    )

    # Constraint types (for cross-domain analysis)
    constraint_types: list[str] = Field(
        default_factory=list,
        description="Constraint types demonstrated (e.g., 'all_different', 'linear_sum')",
    )
    business_analogies: list[str] = Field(
        default_factory=list,
        description="Real-world problems this models (e.g., 'scheduling', 'routing')",
    )

    # Difficulty profile
    difficulty_profile: DifficultyProfile | None = Field(
        default=None,
        description="Detailed difficulty characteristics",
    )

    # Difficulty axes (backward compatible with chuk-math)
    depth: int | None = Field(
        default=None,
        description="Expression nesting/reasoning depth",
    )
    operation_count: int | None = Field(
        default=None,
        description="Number of operations in optimal solution",
    )
    numeric_range: tuple[float, float] | None = Field(
        default=None,
        description="Range of numbers used (min, max)",
    )
    has_decimals: bool | None = Field(
        default=None,
        description="Whether decimals are involved",
    )
    has_negatives: bool | None = Field(
        default=None,
        description="Whether negative numbers are involved",
    )

    # Metadata
    tags: list[str] = Field(
        default_factory=list,
        description="Searchable tags for filtering",
    )
    common_mistakes: list[str] = Field(
        default_factory=list,
        description="Expected error types for this problem",
    )

    @classmethod
    def generate_id(cls, domain: str, difficulty: DifficultyLevel, seed: int) -> str:
        """Generate a deterministic problem ID."""
        return f"{domain}_{difficulty.value}_{seed}"

    @classmethod
    def generate_id_from_content(cls, domain: str, content: str) -> str:
        """Generate a content-based ID (for problems without seeds)."""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"{domain}_{content_hash}"

    def to_prompt_dict(self) -> dict[str, Any]:
        """Export as a simple prompt dict for training."""
        return {
            "id": self.id,
            "prompt": self.prompt,
            "gold_answer": self.gold_answer,
        }

    def to_full_dict(self) -> dict[str, Any]:
        """Export full problem specification."""
        return self.model_dump(exclude_none=True)

    def get_difficulty_profile(self) -> DifficultyProfile:
        """Get difficulty profile, creating default if not set."""
        if self.difficulty_profile is not None:
            return self.difficulty_profile
        return DifficultyProfile.from_difficulty_level(self.difficulty, self.domain)

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Problem):
            return self.id == other.id
        return False
