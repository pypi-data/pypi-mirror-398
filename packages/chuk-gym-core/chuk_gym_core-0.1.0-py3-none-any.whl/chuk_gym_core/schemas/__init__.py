"""
Core schemas for chuk-gym-core.

This module provides unified data models for reasoning gym environments,
supporting both math problems and logic puzzles.
"""

from chuk_gym_core.schemas.config import (
    DifficultyLevel,
    DifficultyProfile,
    OutputMode,
    SolverConfig,
    ToolPolicy,
)
from chuk_gym_core.schemas.episode import (
    EpisodeRecord,
    EpisodeStatus,
    MoveRecord,
    TrajectoryStep,
)
from chuk_gym_core.schemas.problem import Problem
from chuk_gym_core.schemas.trace import Step, StepOperation, StepRef, Trace
from chuk_gym_core.schemas.verification import (
    ErrorType,
    ToolCallGrade,
    VerificationResult,
)

__all__ = [
    # Config
    "DifficultyLevel",
    "DifficultyProfile",
    "ToolPolicy",
    "SolverConfig",
    "OutputMode",
    # Problem
    "Problem",
    # Trace
    "Step",
    "StepRef",
    "Trace",
    "StepOperation",
    # Verification
    "VerificationResult",
    "ErrorType",
    "ToolCallGrade",
    # Episode
    "EpisodeStatus",
    "EpisodeRecord",
    "TrajectoryStep",
    "MoveRecord",
]
