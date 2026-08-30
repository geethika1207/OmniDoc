from pydantic import BaseModel, EmailStr

class LoginResponse(BaseModel):
    access_token : str
    token_type : str

class UserRequest(BaseModel):
    email : EmailStr
    password : str 

class UserResponse(BaseModel):
    id : int
    email : EmailStr
    class Config():
        orm_mode = True