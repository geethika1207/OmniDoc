from pydantic import BaseModel, EmailStr, ConfigDict

class LoginResponse(BaseModel):
    access_token: str
    token_type: str

class UserRequest(BaseModel):
    email: EmailStr
    password: str 

class UserResponse(BaseModel):
    id: str  # Has to match UUID string from models.User
    email: EmailStr
    
    model_config = ConfigDict(from_attributes=True)