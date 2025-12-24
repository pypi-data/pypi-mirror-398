"""DSPy signatures for BRAID reasoning."""

import dspy


class BraidPlanSignature(dspy.Signature):
    """
    Signature for GRD planning phase.

    This signature defines the input/output structure for generating
    a Guided Reasoning Diagram (GRD) from a problem statement.

    BRAID Protocol Requirements:
    - Procedural Scaffolding: Describe HOW to solve, not WHAT the answer is
    - Atomicity: Keep each node under 15 tokens for optimal performance
    - No Answer Leakage: Never include computed values in the diagram
    """

    problem: str = dspy.InputField(desc="The problem to solve, described clearly and completely")

    grd: str = dspy.OutputField(
        desc="A Guided Reasoning Diagram in Mermaid flowchart format. "
        "CRITICAL RULES: "
        "1) Do NOT write the answer - only describe HOW to find it. "
        "2) Create a procedural scaffold that outlines the solution PROCESS. "
        "3) Each node should describe an ACTION (e.g., 'Calculate speed by dividing distance by time'), not a computed VALUE (e.g., '60 km/h'). "
        "4) Keep each node label UNDER 15 tokens for optimal performance. "
        "5) Use flowchart TD format with clear, atomic step descriptions. "
        "6) Never include numerical results in node labels - use placeholders or descriptive text."
    )


class BraidExecuteSignature(dspy.Signature):
    """
    Signature for GRD execution phase.

    This signature defines the input/output structure for executing
    a Guided Reasoning Diagram step by step.
    """

    problem: str = dspy.InputField(desc="The original problem to solve")

    grd: str = dspy.InputField(desc="The Guided Reasoning Diagram (Mermaid format) to follow")

    current_step: str = dspy.InputField(
        desc="The current step in the GRD that needs to be executed"
    )

    previous_results: str = dspy.InputField(desc="Results from previous steps (if any)", default="")

    step_result: str = dspy.OutputField(
        desc="The result of executing the current step. "
        "This should be a clear, concise output that can be used "
        "in subsequent steps."
    )


class BraidReasoningSignature(dspy.Signature):
    """
    Complete BRAID reasoning signature combining planning and execution.

    This is a convenience signature that can be used for end-to-end
    BRAID reasoning in a single call.
    """

    problem: str = dspy.InputField(desc="The problem to solve, described clearly and completely")

    grd: str = dspy.OutputField(desc="A Guided Reasoning Diagram in Mermaid flowchart format")

    reasoning_steps: str = dspy.OutputField(
        desc="Step-by-step reasoning following the GRD. "
        "Each step should reference the corresponding GRD node."
    )

    answer: str = dspy.OutputField(desc="The final answer to the problem")


class BraidStepSignature(dspy.Signature):
    """
    Signature for executing a single step in a GRD.

    Used internally by the BRAID module for step-by-step execution.
    """

    step_description: str = dspy.InputField(desc="Description of the step to execute")

    context: str = dspy.InputField(desc="Context from previous steps and the original problem")

    step_output: str = dspy.OutputField(desc="Output from executing this step")
