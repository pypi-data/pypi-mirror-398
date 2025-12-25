"""
Text formatting utilities
"""


class TextFormatter:
    """A class for formatting text in various ways"""
    
    @staticmethod
    def to_title_case(text: str) -> str:
        """Convert text to title case"""
        return text.title()
    
    @staticmethod
    def to_snake_case(text: str) -> str:
        """Convert text to snake_case"""
        import re
        text = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
        text = re.sub('([a-z0-9])([A-Z])', r'\1_\2', text)
        return text.lower().replace(' ', '_')
    
    @staticmethod
    def reverse_text(text: str) -> str:
        """Reverse the text"""
        return text[::-1]
    
    @staticmethod
    def capitalize_words(text: str) -> str:
        """Capitalize first letter of each word"""
        return ' '.join(word.capitalize() for word in text.split())
    
    @staticmethod
    def remove_whitespace(text: str) -> str:
        """Remove all whitespace from text"""
        return ''.join(text.split())

