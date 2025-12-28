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

from enum import Enum
from datetime import datetime

from discord_shared_db.base import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, BigInteger, ForeignKey, Integer, DateTime, Enum as SqlEnum

class Colors(Enum):

    PINK = '#eaaeba'
    RED = '#cc4049'
    ORANGE = '#e79438'
    YELLOW = '#f6cc6c'
    GREEN = '#85af64'
    BLUE = '#6babe9'
    PURPLE = '#a590d1'
    BROWN = '#b66d55'
    BLACK = '#32373d'
    WHITE = "#ffffff"
    GRAY = '#babbbd'
    TAN1 = "#f0ddcf"
    TAN2 = "#a27d7d"

class PixelData(Base):
    __tablename__ = "pixels_data"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"))

    # Store enum as string (or use SqlEnum if you prefer native enum support)
    color = Column(SqlEnum(Colors), nullable=False)
    dd_time = Column(DateTime, nullable=False)

    # Flatten Location into x and y columns
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)

    user = relationship("User", back_populates="pixels_data")
