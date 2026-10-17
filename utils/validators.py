"""
Validators
Input validation functions with complete regex patterns
"""

import re
from typing import Tuple


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate email format.
    Returns (is_valid, message) tuple.
    """
    if not email:
        return False, "Email is required"
    
    # Complete email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email.strip()):
        return False, "Invalid email format"
    
    return True, "Valid email"


def validate_phone(phone: str) -> Tuple[bool, str]:
    """
    Validate phone number format (Indian format).
    Returns (is_valid, message) tuple.
    """
    if not phone:
        return True, "Phone is optional"
    
    # Remove non-numeric characters
    digits = ''.join(filter(str.isdigit, phone))
    
    if len(digits) < 10:
        return False, "Phone number must have at least 10 digits"
    
    if len(digits) > 15:
        return False, "Phone number is too long"
    
    return True, "Valid phone number"


def validate_password(password: str) -> Tuple[bool, str]:
    """
    Validate password strength.
    Requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    
    Returns (is_valid, message) tuple.
    """
    if not password:
        return False, "Password is required"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if len(password) > 128:
        return False, "Password is too long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    return True, "Strong password"


def validate_username(username: str) -> Tuple[bool, str]:
    """
    Validate username format.
    Requirements:
    - 3-50 characters
    - Alphanumeric, underscore, or hyphen only
    - Cannot start with number
    
    Returns (is_valid, message) tuple.
    """
    if not username:
        return False, "Username is required"
    
    username = username.strip()
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"
    
    if len(username) > 50:
        return False, "Username cannot exceed 50 characters"
    
    # Complete username regex pattern
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_-]*$', username):
        return False, "Username must start with a letter and contain only letters, numbers, underscores, or hyphens"
    
    return True, "Valid username"


def validate_vin(vin: str) -> Tuple[bool, str]:
    """
    Validate VIN (Vehicle Identification Number).
    VINs are 17 characters, alphanumeric (excluding I, O, Q).
    
    Returns (is_valid, message) tuple.
    """
    if not vin:
        return True, "VIN is optional"
    
    vin = vin.strip().upper()
    
    if len(vin) != 17:
        return False, "VIN must be exactly 17 characters"
    
    # VINs cannot contain I, O, or Q
    if re.search(r'[IOQ]', vin):
        return False, "VIN cannot contain letters I, O, or Q"
    
    # Complete VIN regex pattern
    if not re.match(r'^[A-HJ-NPR-Z0-9]{17}$', vin):
        return False, "VIN contains invalid characters"
    
    return True, "Valid VIN"


def validate_license_plate(plate: str) -> Tuple[bool, str]:
    """
    Validate Gujarat license plate format: GJ-XX-####-YY
    - GJ: State code for Gujarat
    - XX: Two-digit RTO district code (01-38)
    - ####: Four-digit unique number (0001-9999)
    - YY: Two-digit year (00-99, representing 2000-2099)
    
    Examples: GJ-01-1234-23, GJ01123423, GJ 01 1234 23
    
    Returns (is_valid, message) tuple.
    """
    if not plate:
        return True, "License plate is optional"
    
    plate = plate.strip().upper()
    
    # Remove spaces and dashes for validation
    plate_clean = plate.replace(' ', '').replace('-', '')
    
    # Complete Gujarat format regex: GJ + 2 digits + 4 digits + 2 digits = 12 characters
    pattern = r'^GJ(\d{2})(\d{4})(\d{2})$'
    match = re.match(pattern, plate_clean)
    
    if not match:
        return False, "License plate must follow Gujarat format: GJ-XX-####-YY (e.g., GJ-01-1234-23)"
    
    rto_code = int(match.group(1))
    number = int(match.group(2))
    year_suffix = int(match.group(3))
    
    # Validate RTO code (01-38 for Gujarat)
    if rto_code < 1 or rto_code > 38:
        return False, f"Invalid RTO code: {rto_code:02d}. Must be between 01 and 38 for Gujarat"
    
    # Validate number (0001-9999)
    if number < 1 or number > 9999:
        return False, f"Invalid number: {number:04d}. Must be between 0001 and 9999"
    
    # Validate year (reasonable range: 00-30 for 2000-2030)
    from datetime import datetime
    current_year_suffix = datetime.now().year % 100
    if year_suffix > current_year_suffix + 5:  # Allow up to 5 years in future
        return False, f"Invalid year: {year_suffix:02d}. Cannot be more than 5 years in the future"
    
    return True, "Valid Gujarat license plate"


def validate_year(year: int) -> Tuple[bool, str]:
    """
    Validate vehicle year.
    
    Returns (is_valid, message) tuple.
    """
    from datetime import datetime
    
    if year is None:
        return True, "Year is optional"
    
    current_year = datetime.now().year
    
    if year < 1900:
        return False, "Year must be 1900 or later"
    
    if year > current_year + 1:
        return False, f"Year cannot be later than {current_year + 1}"
    
    return True, "Valid year"


def validate_positive_number(value: float, field_name: str = "Value") -> Tuple[bool, str]:
    """
    Validate that a number is positive.
    
    Returns (is_valid, message) tuple.
    """
    if value is None:
        return False, f"{field_name} is required"
    
    try:
        from decimal import Decimal
        num = Decimal(str(value))
        if num < 0:
            return False, f"{field_name} must be a positive number"
        return True, f"Valid {field_name.lower()}"
    except (TypeError, ValueError):
        return False, f"{field_name} must be a valid number"


def validate_quantity(quantity: int) -> Tuple[bool, str]:
    """
    Validate quantity is a positive integer.
    
    Returns (is_valid, message) tuple.
    """
    if quantity is None:
        return False, "Quantity is required"
    
    try:
        qty = int(quantity)
        if qty <= 0:
            return False, "Quantity must be greater than zero"
        return True, "Valid quantity"
    except (TypeError, ValueError):
        return False, "Quantity must be a whole number"


def sanitize_input(text: str) -> str:
    """
    Sanitize user input by removing potentially harmful characters.
    """
    if not text:
        return ""
    
    # Remove HTML-like tags
    text = re.sub(r'<[^>]*>', '', text)
    
    # Remove control characters except newlines and tabs
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    
    return text.strip()


def validate_gst_number(gst: str) -> Tuple[bool, str]:
    """
    Validate Indian GST number format.
    Format: 22AAAAA0000A1Z5 (15 characters)
    
    Returns (is_valid, message) tuple.
    """
    if not gst:
        return True, "GST number is optional"
    
    gst = gst.strip().upper()
    
    # GST format: 2 digits (state) + 10 chars (PAN) + 1 digit + 1 char + 1 digit
    pattern = r'^\d{2}[A-Z]{5}\d{4}[A-Z]{1}\d{1}[A-Z]{1}\d{1}$'
    
    if not re.match(pattern, gst):
        return False, "Invalid GST number format. Expected: 22AAAAA0000A1Z5"
    
    return True, "Valid GST number"
