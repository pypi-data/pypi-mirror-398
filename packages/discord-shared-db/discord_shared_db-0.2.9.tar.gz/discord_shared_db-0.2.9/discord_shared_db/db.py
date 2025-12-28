# This file is part of discord-shared-db
#
# Copyright (C) 2026 CouchComfy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

import os
import logging
from typing import AsyncGenerator

from sqlalchemy import select
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from discord_shared_db.user import User, Base

load_dotenv()

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASS = os.getenv("POSTGRES_PASS")
POSTGRES_ADDY = os.getenv("POSTGRES_ADDY")
POSTGRES_NAME = os.getenv("POSTGRES_NAME")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", '5432')

class BotDatabase:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(BotDatabase, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return  # Prevent reinitialization on multiple calls

        if not POSTGRES_USER:
            raise Exception("Postgres User not Defined")
        if not POSTGRES_PASS:
            raise Exception("Postgres Password not Defined")
        if not POSTGRES_ADDY:
            raise Exception("Postgres Address not Defined")
        if not POSTGRES_NAME:
            raise Exception("Postgres Database Name not Defined")
        if not POSTGRES_PORT:
            raise Exception("Postgres Port not Defined. How did you manage this!!")

        database_url = (
            f'postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASS}'
            f'@{POSTGRES_ADDY}:{POSTGRES_PORT}/{POSTGRES_NAME}'
        )
        
        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = async_sessionmaker(
            self.engine, 
            class_=AsyncSession,
            expire_on_commit=False
        )

        self._initialized = True 
    
    async def init_database(self):
        """Create all tables"""
        logging.info(f'Initializing the Database with the models')
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Context manager for database sessions - one per command"""
        logging.debug(f'Get database Session')
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()
    
    async def get_or_create_user(self, user_id, username, session=None):
        owns_session = False
        if session is None:
            session = self.async_session()
            owns_session = True

        try:
            result = await session.execute(select(User).where(User.user_id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                user = User(user_id=user_id, username=username)
                session.add(user)
                await session.flush()
            return user
        finally:
            if owns_session:
                await session.commit()
                await session.close()

    async def get_all_users(self, session=None):
        owns_session = False
        if session is None:
            session = self.async_session()
            owns_session = True

        try:
            async with session.begin():
                result = await session.execute(select(User))
                users = result.scalars().all()
        finally:
            if owns_session:
                await session.close()

        return users
    
    async def ensure_user_stats(self, user: User, relation_name, session, stat_cls):
        '''
        Pass in the stat class that needs to be initallized
        '''
        await session.refresh(user, attribute_names=[relation_name])
        if getattr(user, relation_name) is None:
            setattr(user, relation_name, stat_cls())
            session.add(user)
            await session.commit()
            await session.refresh(user, attribute_names=[relation_name])
