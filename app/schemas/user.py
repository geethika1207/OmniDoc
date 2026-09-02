from pydantic import BaseModel, EmailStr, ConfigDict, Field

class LoginResponse(BaseModel):
    access_token: str
    token_type: str

class UserRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=72)

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    
    model_config = ConfigDict(from_attributes=True)