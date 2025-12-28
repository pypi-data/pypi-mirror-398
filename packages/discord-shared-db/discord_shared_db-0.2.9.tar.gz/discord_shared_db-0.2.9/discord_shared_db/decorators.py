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

import logging
from datetime import datetime
from functools import wraps

def log_time(message="Function completed in"):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            logging.info(f"⏳ Starting: {func.__name__}")
            start_time = datetime.now()
            result = await func(*args, **kwargs)
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            logging.info(f"{message} {total_time:.3f} seconds")
            return result
        return wrapper
    return decorator