"""
Validation utilities
"""

import re


class Validator:
    """A class for validating various inputs"""
    
    @staticmethod
    def is_email(email: str) -> bool:
        """Validate email address"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def is_phone(phone: str) -> bool:
        """Validate phone number (10 digits)"""
        pattern = r'^\d{10}$'
        return bool(re.match(pattern, phone.replace('-', '').replace(' ', '')))
    
    @staticmethod
    def is_strong_password(password: str) -> bool:
        """Validate strong password (min 8 chars, uppercase, lowercase, digit)"""
        if len(password) < 8:
            return False
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        return has_upper and has_lower and has_digit

