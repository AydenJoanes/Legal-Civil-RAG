"""
Prompt Builders - Builder Pattern Implementation

This package contains builders for constructing LLM prompts
in a flexible and maintainable way.

Design Pattern: Builder
- Separates prompt construction from representation
- Allows step-by-step prompt building
- Supports multiple prompt formats/styles
"""
from .prompt_builder import PromptBuilder, RAGPromptBuilder, ConstructionLegalPromptBuilder

__all__ = ["PromptBuilder", "RAGPromptBuilder", "ConstructionLegalPromptBuilder"]
