from typing import Type

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apex.app.users.schemas import UserCreate, UserOut, UserUpdate
from apex.domain.services.user import UserService


class UserManager:
    def __init__(self, session: AsyncSession, user_model: Type) -> None:
        self.session = session
        self.user_service = UserService(session, user_model)

    async def list_users(self) -> list[UserOut]:
        result = await self.session.execute(select(self.user_service.user_model))
        users = result.scalars().all()
        return [UserOut.model_validate(u) for u in users]

    async def create_user(self, payload: UserCreate) -> UserOut:
        existing = await self.user_service.get_user_by_email(payload.email)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists.")

        user = await self.user_service.create_user(**payload.model_dump())
        await self.session.refresh(user)
        return UserOut.model_validate(user)

    async def get_user(self, user_id: str) -> UserOut:
        user = await self.user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        return UserOut.model_validate(user)

    async def update_user(self, user_id: str, payload: UserUpdate) -> UserOut:
        user = await self.user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        user = await self.user_service.update_user(user, **payload.model_dump(exclude_unset=True))
        return UserOut.model_validate(user)

    async def delete_user(self, user_id: str) -> None:
        user = await self.user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        await self.session.delete(user)
        await self.session.flush()

