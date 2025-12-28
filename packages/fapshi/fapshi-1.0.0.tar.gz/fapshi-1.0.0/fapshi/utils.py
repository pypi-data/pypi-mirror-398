"""Utility functions for the Fapshi SDK."""

import re
from typing import Literal

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal  # type: ignore


def detect_environment(api_key: str) -> Literal["sandbox", "live"]:
    """
    Detect the environment (sandbox or live) based on the API key format.
    
    Sandbox API keys have the format: FAK_TEST_xxx
    Live API keys have the format: FAK_xxx (but not FAK_TEST_xxx)
    
    Args:
        api_key: The API key to check
        
    Returns:
        "sandbox" if the key starts with FAK_TEST_, "live" if it starts with FAK_ (but not FAK_TEST_)
        
    Raises:
        ValueError: If the API key doesn't match the expected format
    """
    if api_key.startswith("FAK_TEST_"):
        # Ensure there's content after FAK_TEST_
        if len(api_key) <= len("FAK_TEST_"):
            raise ValueError(
                "Invalid sandbox API key format. Sandbox keys must be 'FAK_TEST_' followed by additional characters"
            )
        return "sandbox"
    elif api_key.startswith("FAK_"):
        # Ensure there's content after FAK_ and it's not FAK_TEST_
        if len(api_key) <= len("FAK_"):
            raise ValueError(
                "Invalid live API key format. Live keys must be 'FAK_' followed by additional characters"
            )
        return "live"
    else:
        raise ValueError(
            "Invalid API key format. API keys must start with 'FAK_TEST_' (sandbox) "
            "or 'FAK_' (live)"
        )


def get_base_url(api_key: str) -> str:
    """
    Get the base URL based on the API key.
    
    Args:
        api_key: The API key to check
        
    Returns:
        The base URL for the environment
        
    Raises:
        ValueError: If the API key doesn't match the expected format
    """
    environment = detect_environment(api_key)
    if environment == "sandbox":
        return "https://sandbox.fapshi.com"
    return "https://live.fapshi.com"


def validate_user_id(user_id: str) -> bool:
    """
    Validate the userId format.
    
    Format: ^[a-zA-Z0-9\\-_]{1,100}$
    
    Args:
        user_id: The user ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not user_id:
        return False
    pattern = r"^[a-zA-Z0-9\-_]{1,100}$"
    return bool(re.match(pattern, user_id))


def validate_external_id(external_id: str) -> bool:
    """
    Validate the externalId format.
    
    Format: ^[a-zA-Z0-9\\-_]{1,100}$
    
    Args:
        external_id: The external ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not external_id:
        return False
    pattern = r"^[a-zA-Z0-9\-_]{1,100}$"
    return bool(re.match(pattern, external_id))


def validate_amount(amount: int) -> bool:
    """
    Validate the amount.
    
    Minimum amount is 100.
    
    Args:
        amount: The amount to validate
        
    Returns:
        True if valid (>= 100), False otherwise
    """
    return isinstance(amount, int) and amount >= 100


def validate_email(email: str) -> bool:
    """
    Basic email validation.
    
    Args:
        email: The email to validate
        
    Returns:
        True if valid email format, False otherwise
    """
    if not email:
        return False
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def normalize_phone(phone: str) -> str:
    """
    Normalize phone number for Fapshi API.
    
    Fapshi phone numbers should start with 6 (without country code 237).
    This function removes the 237 country code if present.
    
    Args:
        phone: Phone number (may include 237 country code)
        
    Returns:
        Normalized phone number starting with 6
        
    Raises:
        ValueError: If phone number doesn't start with 6 or 2376
    """
    if not phone:
        raise ValueError("Phone number is required")
    
    phone = phone.strip()
    
    # Remove country code 237 if present
    if phone.startswith("237"):
        phone = phone[3:]
    
    # Validate that it starts with 6
    if not phone.startswith("6"):
        raise ValueError(
            "Phone number must start with 6 (without country code 237). "
            f"Received: {phone}"
        )
    
    return phone

