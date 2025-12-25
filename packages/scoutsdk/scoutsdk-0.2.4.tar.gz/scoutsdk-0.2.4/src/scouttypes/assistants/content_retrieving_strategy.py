from typing import Optional
from pydantic import BaseModel, ConfigDict


class ContentRetrievingStrategy(BaseModel):
    model_config = ConfigDict(extra="allow")
    keyword_search_count: Optional[int] = None
    filter_results: Optional[bool] = None
    min_score: Optional[float] = None
    max_result_count: Optional[int] = None


__all__ = ["ContentRetrievingStrategy"]
