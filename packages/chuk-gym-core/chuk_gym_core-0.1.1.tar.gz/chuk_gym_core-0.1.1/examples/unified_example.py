"""
Unified Example: Using chuk-gym-core with Async Patterns

This example demonstrates how chuk-gym-core provides a unified interface
for both math problems (from chuk-math-gym) and logic puzzles (from puzzle-arcade-server).

Key features demonstrated:
- Pydantic-native schemas (no dictionary goop)
- Async-native environment interface
- Type-safe enums (no magic strings)
- Curriculum learning with progression strategies
- Dataset export for training
"""

import asyncio
from typing import Any

from chuk_gym_core import (
    # Curriculum
    CurriculumScheduler,
    # Schemas
    DifficultyLevel,
    DifficultyProfile,
    ErrorType,
    # Export
    JSONLExporter,
    PerformanceBasedProgression,
    Problem,
    # Environment
    ReasoningEnv,
    # Configuration
    SolverConfig,
    Step,
    StepOperation,
    StepRef,
    ToolPolicy,
    Trace,
    VerificationResult,
)

# =============================================================================
# Example 1: Type-Safe Schemas (No Magic Strings)
# =============================================================================


def demo_type_safe_schemas() -> None:
    """Demonstrate type-safe schemas with Pydantic models."""
    print("=" * 60)
    print("Example 1: Type-Safe Schemas")
    print("=" * 60)

    # Create a problem using typed fields
    problem = Problem(
        id=Problem.generate_id("arithmetic", DifficultyLevel.EASY, 42),
        seed=42,
        domain="arithmetic",
        difficulty=DifficultyLevel.EASY,  # Enum, not string
        prompt="What is 3 + 5 * 2?",
        expression="3 + 5 * 2",
        gold_answer="13",
        tool_policy=ToolPolicy.ALLOWED,  # Enum, not string
        constraint_types=["order_of_operations"],
    )

    print(f"Problem ID: {problem.id}")
    print(f"Difficulty: {problem.difficulty.value} (numeric: {problem.difficulty.numeric})")
    print(f"Tool Policy: {problem.tool_policy.value}")
    print()

    # Create a solution trace with type-safe step references
    trace = Trace(
        problem_id=problem.id,
        steps=[
            Step(
                index=0,
                operation=StepOperation.MULTIPLY,  # Enum, not string
                before_state="5 * 2",
                after_state="10",
                output_value=10,
                explanation="First, evaluate multiplication",
            ),
            Step(
                index=1,
                operation=StepOperation.ADD,
                before_state="3 + 10",
                after_state="13",
                input_refs=[StepRef(step_index=0)],  # Type-safe reference
                output_value=13,
                explanation="Then, add 3",
            ),
        ],
    )

    print("Solution trace:")
    print(trace.to_natural_language())
    print(f"\nFinal value: {trace.final_value}")
    print(f"Verify answer 13: {trace.verify_final(13)}")
    print(f"Verify answer 16: {trace.verify_final(16)}")
    print()


# =============================================================================
# Example 2: Async Environment Pattern
# =============================================================================


class SimpleArithmeticEnv(ReasoningEnv):
    """Example async environment for arithmetic problems."""

    def __init__(self) -> None:
        super().__init__(
            max_steps=10,
            correct_reward=1.0,
            completion_bonus=10.0,
        )
        self._answer: int = 0
        self._solved: bool = False

    @property
    def domain(self) -> str:
        return "simple_arithmetic"

    async def _generate_problem(
        self,
        seed: int,
        difficulty: DifficultyLevel,
    ) -> Problem:
        # Generate a simple addition problem
        import random

        rng = random.Random(seed)
        a = rng.randint(1, 10 * difficulty.numeric)
        b = rng.randint(1, 10 * difficulty.numeric)
        self._answer = a + b
        self._solved = False

        return Problem(
            id=f"arith_{seed}",
            seed=seed,
            domain=self.domain,
            difficulty=difficulty,
            prompt=f"What is {a} + {b}?",
            gold_answer=str(self._answer),
        )

    async def _generate_trace(self, problem: Problem) -> Trace | None:
        return Trace(
            problem_id=problem.id,
            steps=[
                Step(
                    index=0,
                    operation=StepOperation.ADD,
                    before_state=problem.prompt,
                    after_state=str(self._answer),
                    output_value=self._answer,
                )
            ],
        )

    async def _validate_action(self, action: str) -> tuple[bool, float, str]:
        try:
            guess = int(action.strip())
            if guess == self._answer:
                self._solved = True
                return True, 0.0, "Correct!"
            return False, 0.0, f"Wrong. Expected {self._answer}"
        except ValueError:
            return False, 0.0, "Please enter a number"

    def _is_complete(self) -> bool:
        return self._solved

    def _get_observation(self) -> dict[str, Any]:
        if self.state is None:
            return {}
        return {
            "prompt": self.state.problem.prompt,
            "attempts": self.state.steps_taken,
        }


async def demo_async_environment() -> None:
    """Demonstrate async environment pattern."""
    print("=" * 60)
    print("Example 2: Async Environment Pattern")
    print("=" * 60)

    env = SimpleArithmeticEnv()

    # Reset with typed difficulty
    obs, info = await env.reset(seed=42, difficulty=DifficultyLevel.EASY)
    print(f"Problem: {obs['prompt']}")
    print(f"Domain: {info['domain']}")

    # Step through the episode
    obs, reward, terminated, truncated, info = await env.step("wrong")
    print(f"Tried 'wrong': {info['message']}")

    # Get the correct answer from observation
    obs, reward, terminated, truncated, info = await env.step(str(env._answer))
    print(f"Tried correct answer: {info['message']}")
    print(f"Terminated: {terminated}, Reward: {reward:.2f}")

    # Get episode record
    record = env.get_episode_record()
    if record:
        print("\nEpisode summary:")
        print(f"  Status: {record.status.value}")
        print(f"  Steps: {record.steps_taken}")
        print(f"  Invalid: {record.invalid_actions}")
        print(f"  Efficiency: {record.efficiency_score:.2f}")

    env.close()
    print()


# =============================================================================
# Example 3: Curriculum Learning
# =============================================================================


def demo_curriculum_learning() -> None:
    """Demonstrate curriculum learning with type-safe progression."""
    print("=" * 60)
    print("Example 3: Curriculum Learning")
    print("=" * 60)

    # Performance-based progression
    scheduler = CurriculumScheduler(
        strategy=PerformanceBasedProgression(
            advance_threshold=0.8,
            retreat_threshold=0.3,
            min_episodes=5,
        ),
        start_difficulty=DifficultyLevel.EASY,
    )

    print("Simulating training with performance-based progression:")
    print()

    # Simulate episodes
    import random

    rng = random.Random(42)

    for episode in range(20):
        difficulty = scheduler.get_current_difficulty()

        # Simulate solving - harder difficulties are less likely to succeed
        success_rate = 1.0 - (difficulty.numeric - 1) * 0.1
        solved = rng.random() < success_rate

        scheduler.record_episode(
            solved=solved,
            steps=rng.randint(5, 15),
            invalid=rng.randint(0, 3),
            hints=0,
            efficiency=0.8 if solved else 0.0,
        )

        if episode % 5 == 4:
            summary = scheduler.get_summary()
            print(
                f"Episode {episode + 1}: "
                f"difficulty={summary['current_difficulty']}, "
                f"solve_rate={summary['solve_rate']:.2%}"
            )

    print()


# =============================================================================
# Example 4: Difficulty Profiles
# =============================================================================


def demo_difficulty_profiles() -> None:
    """Demonstrate difficulty profiles for curriculum design."""
    print("=" * 60)
    print("Example 4: Difficulty Profiles")
    print("=" * 60)

    print("Difficulty profiles by level:\n")

    for level in DifficultyLevel:
        profile = DifficultyProfile.from_difficulty_level(level, "math")
        print(
            f"  {level.value:12} | "
            f"logic_depth={profile.logic_depth}, "
            f"branching={profile.branching_factor:.1f}, "
            f"complexity={profile.estimated_complexity:.1f}"
        )

    print()


# =============================================================================
# Example 5: Verification with Error Types
# =============================================================================


def demo_verification() -> None:
    """Demonstrate type-safe verification results."""
    print("=" * 60)
    print("Example 5: Verification with Error Types")
    print("=" * 60)

    # Successful verification
    success = VerificationResult.success(expected=13, actual=13)
    print(f"Correct answer: score={success.score}, reward={success.to_reward():.2f}")

    # Failed verification with specific error type
    failure = VerificationResult.failure(
        error_type=ErrorType.ORDER_OF_OPS,
        message="PEMDAS violation: multiplication before addition",
        expected=13,
        actual=16,
        partial_credit=0.3,
    )
    print(f"Wrong answer: error={failure.error_type.value}")
    print(f"  partial_credit={failure.partial_credit}, reward={failure.to_reward():.2f}")

    # Different error types
    print("\nError types for analysis:")
    for error_type in [
        ErrorType.SIGN_ERROR,
        ErrorType.ROUNDING_ERROR,
        ErrorType.CONSTRAINT_VIOLATION,
        ErrorType.TOOL_POLICY_VIOLATION,
    ]:
        print(f"  - {error_type.value}")

    print()


# =============================================================================
# Example 6: Solver Configuration
# =============================================================================


def demo_solver_config() -> None:
    """Demonstrate solver configuration options."""
    print("=" * 60)
    print("Example 6: Solver Configuration")
    print("=" * 60)

    # Different configurations for experiments
    configs = [
        ("Pure reasoning", SolverConfig.solver_free()),
        ("5 hints with penalty", SolverConfig.solver_assisted(budget=5, penalty=0.1)),
        ("Unlimited hints", SolverConfig.unlimited()),
    ]

    for name, config in configs:
        print(f"{name}:")
        print(f"  solver_allowed={config.solver_allowed}")
        print(f"  hint_budget={config.hint_budget}")
        print(f"  hint_penalty={config.hint_penalty}")
        print()


# =============================================================================
# Example 7: Dataset Export
# =============================================================================


def demo_dataset_export() -> None:
    """Demonstrate dataset export for training."""
    print("=" * 60)
    print("Example 7: Dataset Export")
    print("=" * 60)

    from io import StringIO

    # Create sample data
    problem = Problem(
        id="export_demo_1",
        seed=42,
        domain="arithmetic",
        difficulty=DifficultyLevel.EASY,
        prompt="What is 2 + 2?",
        gold_answer="4",
    )

    trace = Trace(
        problem_id=problem.id,
        steps=[
            Step(
                index=0,
                operation=StepOperation.ADD,
                before_state="2 + 2",
                after_state="4",
                output_value=4,
                explanation="Add the numbers",
            )
        ],
    )

    # Export to different formats
    output = StringIO()
    with JSONLExporter(output) as exporter:
        # Problem format
        exporter.write_problem(problem, trace)

        # Chat format for fine-tuning
        exporter.write_training_example(problem, trace, format_type="chat")

        # Q&A format
        exporter.write_training_example(problem, trace, format_type="qa")

    print(f"Exported {exporter.count} records")
    print("\nSample output (first 200 chars of each line):")

    output.seek(0)
    for i, line in enumerate(output.readlines()):
        print(f"  Record {i + 1}: {line[:200]}...")

    print()


# =============================================================================
# Main
# =============================================================================


async def main() -> None:
    """Run all examples."""
    print()
    print("=" * 60)
    print("chuk-gym-core: Unified Reasoning Training Infrastructure")
    print("=" * 60)
    print()

    demo_type_safe_schemas()
    await demo_async_environment()
    demo_curriculum_learning()
    demo_difficulty_profiles()
    demo_verification()
    demo_solver_config()
    demo_dataset_export()

    print("=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
