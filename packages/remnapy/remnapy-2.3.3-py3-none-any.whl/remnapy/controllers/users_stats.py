from typing import Annotated, Union
from uuid import UUID

from rapid_api_client import Path, Query

from remnapy.models import GetUserUsageByRangeResponseDto
from remnapy.rapid import BaseController, get


class UsersStatsController(BaseController):
    @get(
        "/users/stats/usage/{uuid}/range",
        response_class=GetUserUsageByRangeResponseDto,
    )
    async def get_user_usage_by_range(
        self,
        uuid: Annotated[Union[str, UUID], Path(description="UUID of the user")],
        start: Annotated[str, Query(description="Start date in ISO format")],
        end: Annotated[str, Query(description="End date in ISO format")],
    ) -> GetUserUsageByRangeResponseDto:
        """Get User Usage By Range"""
        ...
