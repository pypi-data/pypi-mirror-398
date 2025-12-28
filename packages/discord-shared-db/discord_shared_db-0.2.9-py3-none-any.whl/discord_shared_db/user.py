# This file is part of discord-shared-db
#
# Copyright (C) 2025 CouchComfy
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

from sqlalchemy.orm import relationship
from sqlalchemy import Column, BigInteger, Integer, String

from discord_shared_db.base import Base

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(BigInteger, primary_key=True)
    username = Column(String, nullable=False)
    level = Column(Integer, default=1, nullable=False)
    xp = Column(Integer, default=0, nullable=False)

    pixels = Column(Integer, default=5, nullable=False)

    rps_stats = relationship("RPSStats", back_populates="user", uselist=False, lazy="selectin")
    ttt_stats = relationship("TTTStats", back_populates="user", uselist=False, lazy="selectin")
    pixels_data = relationship("PixelData", back_populates="user", cascade="all, delete-orphan", lazy="selectin")
