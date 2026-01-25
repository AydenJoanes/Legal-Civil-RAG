"""
Prompt Builder - Builder Pattern Implementation

Design Pattern: Builder
- Separates the construction of complex prompts from their representation
- Allows the same construction process to create different representations
- Provides fine-grained control over prompt construction

SOLID Principles:
- SRP: Only handles prompt construction
- OCP: New prompt styles can be added without modifying existing code
- DIP: ChatService depends on builder abstraction
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class PromptComponents:
    """Data class holding all prompt components."""
    system_instructions: List[str] = field(default_factory=list)
    context_sections: List[Dict[str, str]] = field(default_factory=list)
    user_query: str = ""
    examples: List[Dict[str, str]] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    output_format: Optional[str] = None


class PromptBuilder(ABC):
    """
    Abstract Builder for LLM prompts.
    
    Defines the interface for building prompts step-by-step.
    Concrete builders implement specific prompt formats.
    """
    
    def __init__(self):
        self._components = PromptComponents()
    
    def reset(self) -> "PromptBuilder":
        """Reset builder to initial state."""
        self._components = PromptComponents()
        return self
    
    @abstractmethod
    def add_system_instruction(self, instruction: str) -> "PromptBuilder":
        """Add a system instruction."""
        pass
    
    @abstractmethod
    def add_context(self, context: str, label: str = "Context") -> "PromptBuilder":
        """Add context information."""
        pass
    
    @abstractmethod
    def set_query(self, query: str) -> "PromptBuilder":
        """Set the user query."""
        pass
    
    @abstractmethod
    def add_example(self, question: str, answer: str) -> "PromptBuilder":
        """Add a few-shot example."""
        pass
    
    @abstractmethod
    def add_constraint(self, constraint: str) -> "PromptBuilder":
        """Add an output constraint."""
        pass
    
    @abstractmethod
    def set_output_format(self, format_desc: str) -> "PromptBuilder":
        """Set expected output format."""
        pass
    
    @abstractmethod
    def build_system_prompt(self) -> str:
        """Build the system prompt."""
        pass
    
    @abstractmethod
    def build_user_prompt(self) -> str:
        """Build the user prompt."""
        pass
    
    @abstractmethod
    def build_messages(self) -> List[Dict[str, str]]:
        """Build complete message list for chat API."""
        pass


class RAGPromptBuilder(PromptBuilder):
    """
    Concrete Builder for RAG (Retrieval-Augmented Generation) prompts.
    
    Builds prompts optimized for document-grounded Q&A:
    - System prompt with grounding rules
    - Context sections from retrieved documents
    - User query with optional formatting
    
    Usage:
        builder = RAGPromptBuilder()
        messages = (builder
            .add_system_instruction("You are a helpful assistant.")
            .add_constraint("Only use provided context")
            .add_context(retrieved_text, "Document")
            .set_query("What is the main topic?")
            .build_messages())
    """
    
    # Default RAG instructions
    DEFAULT_INSTRUCTIONS = [
        "You are a document-grounded assistant.",
        "Use ONLY the information present in the provided context.",
        "Do NOT use any external knowledge.",
        "Do NOT make assumptions or guesses.",
        "If the answer is not present in the context, say: \"The document does not contain this information.\"",
        "Be concise and clear.",
        "Summarize information instead of copying raw text.",
    ]
    
    DEFAULT_CONSTRAINTS = [
        "Do NOT include IDs, reference numbers, GSTIN, CIN, signatures, or contact details unless explicitly asked."
    ]
    
    def __init__(self, use_defaults: bool = True):
        """
        Initialize RAG prompt builder.
        
        Args:
            use_defaults: Whether to include default RAG instructions
        """
        super().__init__()
        
        if use_defaults:
            self._components.system_instructions = self.DEFAULT_INSTRUCTIONS.copy()
            self._components.constraints = self.DEFAULT_CONSTRAINTS.copy()
    
    def add_system_instruction(self, instruction: str) -> "RAGPromptBuilder":
        """Add a system instruction."""
        self._components.system_instructions.append(instruction)
        return self
    
    def add_context(self, context: str, label: str = "Context") -> "RAGPromptBuilder":
        """
        Add context information from retrieved documents.
        
        Args:
            context: The retrieved text content
            label: Label for this context section (e.g., "Document", "Reference")
        """
        self._components.context_sections.append({
            "label": label,
            "content": context
        })
        return self
    
    def set_query(self, query: str) -> "RAGPromptBuilder":
        """Set the user's question."""
        self._components.user_query = query
        return self
    
    def add_example(self, question: str, answer: str) -> "RAGPromptBuilder":
        """
        Add a few-shot example for better responses.
        
        Args:
            question: Example question
            answer: Example answer
        """
        self._components.examples.append({
            "question": question,
            "answer": answer
        })
        return self
    
    def add_constraint(self, constraint: str) -> "RAGPromptBuilder":
        """Add an output constraint."""
        self._components.constraints.append(constraint)
        return self
    
    def set_output_format(self, format_desc: str) -> "RAGPromptBuilder":
        """
        Set expected output format.
        
        Args:
            format_desc: Description of expected format (e.g., "JSON", "bullet points")
        """
        self._components.output_format = format_desc
        return self
    
    def build_system_prompt(self) -> str:
        """
        Build the system prompt from components.
        
        Returns:
            Formatted system prompt string
        """
        parts = []
        
        # Add system instructions
        if self._components.system_instructions:
            instructions = "\n".join(f"- {inst}" for inst in self._components.system_instructions)
            parts.append(f"Rules you MUST follow:\n{instructions}")
        
        # Add constraints
        if self._components.constraints:
            constraints = "\n".join(f"- {c}" for c in self._components.constraints)
            parts.append(f"\nConstraints:\n{constraints}")
        
        # Add output format
        if self._components.output_format:
            parts.append(f"\nOutput Format: {self._components.output_format}")
        
        return "\n".join(parts)
    
    def build_user_prompt(self) -> str:
        """
        Build the user prompt with context and query.
        
        Returns:
            Formatted user prompt string
        """
        parts = []
        
        # Add context sections
        for ctx in self._components.context_sections:
            parts.append(f"{ctx['label']}:\n{ctx['content']}")
        
        # Add examples if any
        if self._components.examples:
            examples_text = "\n\nExamples:"
            for ex in self._components.examples:
                examples_text += f"\nQ: {ex['question']}\nA: {ex['answer']}"
            parts.append(examples_text)
        
        # Add query
        if self._components.user_query:
            parts.append(f"\nQuestion:\n{self._components.user_query}")
            parts.append("\nAnswer:")
        
        return "\n\n".join(parts)
    
    def build_messages(self) -> List[Dict[str, str]]:
        """
        Build complete message list for chat API.
        
        Returns:
            List of message dictionaries with role and content
        """
        messages = []
        
        # System message
        system_prompt = self.build_system_prompt()
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # User message
        user_prompt = self.build_user_prompt()
        if user_prompt:
            messages.append({
                "role": "user",
                "content": user_prompt
            })
        
        return messages
    
    def build(self) -> Dict[str, any]:
        """
        Build and return all prompt components.
        
        Returns:
            Dictionary with system_prompt, user_prompt, and messages
        """
        return {
            "system_prompt": self.build_system_prompt(),
            "user_prompt": self.build_user_prompt(),
            "messages": self.build_messages()
        }


class SummarizationPromptBuilder(PromptBuilder):
    """
    Concrete Builder for summarization prompts.
    
    Builds prompts optimized for document summarization tasks.
    """
    
    DEFAULT_INSTRUCTIONS = [
        "You are a summarization assistant.",
        "Create concise, accurate summaries of the provided content.",
        "Preserve key information and main points.",
        "Use clear and professional language.",
    ]
    
    def __init__(self, use_defaults: bool = True):
        super().__init__()
        if use_defaults:
            self._components.system_instructions = self.DEFAULT_INSTRUCTIONS.copy()
    
    def add_system_instruction(self, instruction: str) -> "SummarizationPromptBuilder":
        self._components.system_instructions.append(instruction)
        return self
    
    def add_context(self, context: str, label: str = "Document") -> "SummarizationPromptBuilder":
        self._components.context_sections.append({
            "label": label,
            "content": context
        })
        return self
    
    def set_query(self, query: str) -> "SummarizationPromptBuilder":
        self._components.user_query = query
        return self
    
    def add_example(self, question: str, answer: str) -> "SummarizationPromptBuilder":
        self._components.examples.append({
            "question": question,
            "answer": answer
        })
        return self
    
    def add_constraint(self, constraint: str) -> "SummarizationPromptBuilder":
        self._components.constraints.append(constraint)
        return self
    
    def set_output_format(self, format_desc: str) -> "SummarizationPromptBuilder":
        self._components.output_format = format_desc
        return self
    
    def set_max_length(self, max_words: int) -> "SummarizationPromptBuilder":
        """Set maximum summary length."""
        self._components.constraints.append(f"Keep summary under {max_words} words")
        return self
    
    def build_system_prompt(self) -> str:
        parts = []
        
        if self._components.system_instructions:
            instructions = "\n".join(f"- {inst}" for inst in self._components.system_instructions)
            parts.append(f"Instructions:\n{instructions}")
        
        if self._components.constraints:
            constraints = "\n".join(f"- {c}" for c in self._components.constraints)
            parts.append(f"\nConstraints:\n{constraints}")
        
        if self._components.output_format:
            parts.append(f"\nOutput Format: {self._components.output_format}")
        
        return "\n".join(parts)
    
    def build_user_prompt(self) -> str:
        parts = []
        
        for ctx in self._components.context_sections:
            parts.append(f"{ctx['label']} to summarize:\n{ctx['content']}")
        
        if self._components.user_query:
            parts.append(f"\nSpecific focus: {self._components.user_query}")
        
        parts.append("\nSummary:")
        
        return "\n\n".join(parts)
    
    def build_messages(self) -> List[Dict[str, str]]:
        return [
            {"role": "system", "content": self.build_system_prompt()},
            {"role": "user", "content": self.build_user_prompt()}
        ]


class ConstructionLegalPromptBuilder(PromptBuilder):
    """
    Concrete Builder for Civil/Construction Legal RAG prompts.
    
    Specialized for analyzing construction contracts (FIDIC, NEC, JCT),
    regulatory compliance, and legal liability.
    """
    
    DEFAULT_INSTRUCTIONS = [
        "You are a specialized Legal Assistant for Construction and Civil Engineering.",
        "Your expertise covers FIDIC, NEC, and standard construction contracts.",
        "When analyzing documents, you MUST:",
        "1. Identify liability ownership (who is responsible?)",
        "2. Detect potential delays and associated penalties (Liquidated Damages)",
        "3. Highlight safety compliance interactions (OSHA, local regulations)",
        "4. Quote specific clauses exactly from the context.",
        "Do NOT infer legal advice not present in the text.",
    ]
    
    DEFAULT_CONSTRAINTS = [
        "Always cite the Clause Number (e.g., 'Clause 12.3') when provided.",
        "Distinguish between 'Contractor' and 'Employer' obligations clearly.",
        "If a definition is ambiguous, state: 'The provided text does not define this term explicitly.'",
    ]
    
    def __init__(self, use_defaults: bool = True):
        super().__init__()
        
        if use_defaults:
            self._components.system_instructions = self.DEFAULT_INSTRUCTIONS.copy()
            self._components.constraints = self.DEFAULT_CONSTRAINTS.copy()
            
    def add_system_instruction(self, instruction: str) -> "ConstructionLegalPromptBuilder":
        self._components.system_instructions.append(instruction)
        return self
    
    def add_context(self, context: str, label: str = "Legal Document") -> "ConstructionLegalPromptBuilder":
        self._components.context_sections.append({
            "label": label,
            "content": context
        })
        return self
    
    def set_query(self, query: str) -> "ConstructionLegalPromptBuilder":
        self._components.user_query = query
        return self
    
    def add_example(self, question: str, answer: str) -> "ConstructionLegalPromptBuilder":
        self._components.examples.append({
            "question": question,
            "answer": answer
        })
        return self
    
    def add_constraint(self, constraint: str) -> "ConstructionLegalPromptBuilder":
        self._components.constraints.append(constraint)
        return self
    
    def set_output_format(self, format_desc: str) -> "ConstructionLegalPromptBuilder":
        self._components.output_format = format_desc
        return self
    
    def build_system_prompt(self) -> str:
        parts = []
        
        if self._components.system_instructions:
            instructions = "\\n".join(f"- {inst}" for inst in self._components.system_instructions)
            parts.append(f"ROLE & RULES:\\n{instructions}")
        
        if self._components.constraints:
            constraints = "\\n".join(f"- {c}" for c in self._components.constraints)
            parts.append(f"\\nLEGAL CONSTRAINTS:\\n{constraints}")
        
        if self._components.output_format:
            parts.append(f"\\nREQUIRED FORMAT: {self._components.output_format}")
        
        return "\\n".join(parts)
    
    def build_user_prompt(self) -> str:
        parts = []
        
        for ctx in self._components.context_sections:
            parts.append(f"DOCUMENT SEGMENT ({ctx['label']}):\\n{ctx['content']}")
        
        if self._components.examples:
            examples_text = "\\n\\nPRECEDENT EXAMPLES:"
            for ex in self._components.examples:
                examples_text += f"\\nQuery: {ex['question']}\\nAnalysis: {ex['answer']}"
            parts.append(examples_text)
        
        if self._components.user_query:
            parts.append(f"\\nLEGAL QUERY:\\n{self._components.user_query}")
            parts.append("\\nANALYSIS:")
        
        return "\\n\\n".join(parts)
    
    def build_messages(self) -> List[Dict[str, str]]:
        return [
            {"role": "system", "content": self.build_system_prompt()},
            {"role": "user", "content": self.build_user_prompt()}
        ]
