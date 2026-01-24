from typing import Annotated, Optional
from pydantic import BaseModel, EmailStr, constr, validator

# Type aliases
FirstNameStr = constr(strip_whitespace=True, min_length=2, max_length=30)
LastNameStr = constr(strip_whitespace=True, min_length=2, max_length=30)
PhoneNumberStr = Annotated[
    str,
    constr(
        strip_whitespace=True,
        pattern=r'^(?:\+91)?[6-9]\d{9}$'
    )
]
RoleStr = Annotated[str, constr(strip_whitespace=True)]

class RegisterRequest(BaseModel):
    """Schema for user registration."""
    first_name: FirstNameStr
    last_name: LastNameStr
    email: EmailStr
    phone_number: PhoneNumberStr
    password: str
    role: RoleStr

    @validator('first_name')
    def validate_first_name_pattern(cls, v):
        import re
        pattern = r"^[A-Za-z\s'-]+$"
        if not re.match(pattern, v):
            raise ValueError("First name may only contain letters, spaces, hyphens, or apostrophes.")
        return v

    @validator('last_name')
    def validate_last_name_pattern(cls, v):
        import re
        pattern = r"^[A-Za-z\s'-]+$"
        if not re.match(pattern, v):
            raise ValueError("Last name may only contain letters, spaces, hyphens, or apostrophes.")
        return v

    @validator('phone_number')
    def validate_phone_number(cls, v):
        import re
        pattern = r'^(?:\+91)?[6-9]\d{9}$'
        if not re.match(pattern, v):
            raise ValueError("Phone number must be a valid Indian mobile number (10 digits, may start with +91, and must start with 6-9).")
        # Additional real-world checks to avoid placeholders
        normalized = v.strip()
        if normalized.startswith('+91'):
            normalized = normalized[3:]
        # Reject all same-digit numbers (e.g., 9999999999)
        if len(set(normalized)) == 1:
            raise ValueError("Phone number looks like a placeholder (repeated digits). Please provide a real contact number.")
        # Reject obvious sequences
        if normalized in {"1234567890", "9876543210"}:
            raise ValueError("Phone number looks like a placeholder (sequential digits). Please provide a real contact number.")
        return v

    @validator('password', pre=True, always=True)
    def validate_password(cls, v):
        import re
        if not isinstance(v, str):
            raise ValueError("Password must be a string.")
        if len(v) < 8 or len(v) > 128:
            raise ValueError("Password must be 8-128 characters, include uppercase, lowercase, digit, and special character.")
        pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,128}$'
        if not re.match(pattern, v):
            raise ValueError("Password must be 8-128 characters, include uppercase, lowercase, digit, and special character.")
        common_passwords = {"password", "123456", "12345678", "qwerty", "abc123", "111111", "123123", "letmein", "welcome", "admin", "iloveyou", "monkey", "login", "passw0rd", "starwars"}
        if v.lower() in common_passwords:
            raise ValueError("Password is too common. Please choose a stronger password.")
        return v

    @validator('role')
    def role_must_be_valid(cls, v):
        allowed = {"user", "trainer", "admin"}
        v_norm = v.lower().strip() if isinstance(v, str) else v
        if v_norm not in allowed:
            raise ValueError("Role must be one of: user, trainer, admin.")
        return v_norm

class RegisterResponse(BaseModel):
    """Schema for registration response."""
    email: str
    message: str
    status: bool

class UserUpdate(BaseModel):
    """Schema for updating user information. Only allows safe fields to be modified."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    dietary_preference: Optional[str] = None

class UserResponse(BaseModel):
    """Schema for user response."""
    user_id: str
    name: str
    email: str
    role_id: str
    dietary_preference: Optional[str] = None
    rating_score: float
    credit: float
    created_at: Optional[str] = None
    last_login_at: Optional[str] = None

class UserProfileResponse(BaseModel):
    """Schema for user profile response - minimal fields."""
    first_name: str
    last_name: str
    phone_number: str
