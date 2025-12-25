"""Prompt template management for DocRAG Kit."""

# Predefined prompt templates for different project types

SYMFONY_TEMPLATE = """You are a Symfony expert. Answer based on this context:

{context}

Question: {question}

Answer concisely:"""

IOS_TEMPLATE = """You are an iOS development expert. Answer based on this context:

{context}

Question: {question}

Answer concisely:"""

GENERAL_TEMPLATE = """You are a developer assistant. Answer based on this context:

{context}

Question: {question}

Answer:"""


class PromptTemplateManager:
    """Manages prompt templates for different project types."""
    
    TEMPLATES = {
        "symfony": SYMFONY_TEMPLATE,
        "ios": IOS_TEMPLATE,
        "general": GENERAL_TEMPLATE,
        "custom": GENERAL_TEMPLATE  # Default to general for custom
    }
    
    @staticmethod
    def get_template(project_type: str) -> str:
        """
        Get prompt template for project type.
        
        Args:
            project_type: Type of project (symfony, ios, general, custom).
        
        Returns:
            Prompt template string.
        """
        return PromptTemplateManager.TEMPLATES.get(project_type, GENERAL_TEMPLATE)
    
    @staticmethod
    def create_custom_template(template: str) -> str:
        """
        Validate and return custom template.
        
        Args:
            template: Custom template string.
        
        Returns:
            Validated template string.
        
        Raises:
            ValueError: If template is missing required placeholders.
        """
        required_placeholders = ['{context}', '{question}']
        for placeholder in required_placeholders:
            if placeholder not in template:
                raise ValueError(f"Template must contain {placeholder} placeholder")
        
        return template


def get_template_for_project_type(project_type: str) -> str:
    """
    Get prompt template for project type (convenience function).
    
    Args:
        project_type: Type of project (symfony, ios, general, custom).
    
    Returns:
        Prompt template string.
    """
    return PromptTemplateManager.get_template(project_type.lower())
