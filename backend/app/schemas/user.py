from pydantic import BaseModel


class UserBase(BaseModel):
    name: str
    current_applying_role: str | None = None


class UserCreate(UserBase):
    clerk_user_id: str


class UserResponse(UserBase):
    clerk_user_id: str

    class Config:
        from_attributes = True
