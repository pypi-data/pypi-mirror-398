"""Meta-prompt templates for different prompt types."""


def critique_meta_prompt(task: str, context: str = "") -> str:
    """
    Meta-prompt for generating critique prompts.

    Args:
        task: The task to critique.
        context: Optional additional context.

    Returns:
        Meta-prompt string.
    """
    prompt = f"""Generate a critique prompt for the following task:

Task: {task}

The critique prompt should:
1. Identify strengths and weaknesses
2. Provide constructive feedback
3. Suggest specific improvements
4. Be balanced and objective
5. Use a professional tone
"""
    if context:
        prompt += f"\nContext: {context}"
    return prompt


def synthesis_meta_prompt(task: str, context: str = "") -> str:
    """
    Meta-prompt for generating synthesis prompts.

    Args:
        task: The task for synthesis.
        context: Optional additional context.

    Returns:
        Meta-prompt string.
    """
    prompt = f"""Generate a synthesis prompt for the following task:

Task: {task}

The synthesis prompt should:
1. Combine multiple perspectives into a unified view
2. Identify common themes and patterns
3. Resolve contradictions where possible
4. Highlight key insights
5. Produce a coherent summary
"""
    if context:
        prompt += f"\nContext: {context}"
    return prompt


def refinement_meta_prompt(original: str, feedback: str = "") -> str:
    """
    Meta-prompt for refining prompts.

    Args:
        original: The original prompt to refine.
        feedback: Optional feedback for refinement.

    Returns:
        Meta-prompt string.
    """
    prompt = f"""Refine the following prompt to improve its quality:

Original Prompt:
{original}

Refinement goals:
1. Improve clarity and precision
2. Add specificity where needed
3. Remove ambiguity
4. Ensure actionability
5. Maintain the original intent
"""
    if feedback:
        prompt += f"\nFeedback to address: {feedback}"
    return prompt


def expansion_meta_prompt(task: str, context: str = "") -> str:
    """
    Meta-prompt for expanding brief prompts.

    Args:
        task: The task to expand.
        context: Optional additional context.

    Returns:
        Meta-prompt string.
    """
    prompt = f"""Generate an expanded prompt for the following brief task:

Task: {task}

The expansion should:
1. Add relevant details and context
2. Include specific requirements
3. Clarify expectations
4. Add examples if helpful
5. Specify constraints and boundaries
"""
    if context:
        prompt += f"\nContext: {context}"
    return prompt


def compression_meta_prompt(task: str, context: str = "") -> str:
    """
    Meta-prompt for compressing verbose prompts.

    Args:
        task: The verbose task to compress.
        context: Optional additional context.

    Returns:
        Meta-prompt string.
    """
    prompt = f"""Generate a compressed, concise version of the following task:

Task: {task}

The compression should:
1. Preserve essential information
2. Remove redundancy
3. Use precise language
4. Maintain clarity
5. Keep critical constraints
"""
    if context:
        prompt += f"\nContext: {context}"
    return prompt


def system_prompt_template(role: str, capabilities: str, constraints: str = "") -> str:
    """
    Template for generating system prompts.

    Args:
        role: The AI assistant's role.
        capabilities: What the assistant can do.
        constraints: Optional constraints on behavior.

    Returns:
        System prompt template.
    """
    prompt = f"""You are {role}.

Your capabilities:
{capabilities}
"""
    if constraints:
        prompt += f"""
Constraints:
{constraints}
"""
    return prompt


def user_query_template(objective: str, requirements: str = "", format_spec: str = "") -> str:
    """
    Template for generating user query prompts.

    Args:
        objective: What the user wants.
        requirements: Optional specific requirements.
        format_spec: Optional output format specification.

    Returns:
        User query template.
    """
    prompt = f"""Objective: {objective}
"""
    if requirements:
        prompt += f"""
Requirements:
{requirements}
"""
    if format_spec:
        prompt += f"""
Output Format:
{format_spec}
"""
    return prompt
