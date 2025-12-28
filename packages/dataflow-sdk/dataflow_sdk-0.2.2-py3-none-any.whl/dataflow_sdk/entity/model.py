from datetime import datetime
from enum import Enum
from typing import Optional, Any, Dict

from pydantic import BaseModel, Field


class CrawlSource(Enum):
    PC = 0
    ANDROID = 1
    MINI = 2
    IOS = 3


class CrawlType(Enum):
    ITEM = 0  # 清洗好的数据
    LIST = 1  # 列表数据
    LOG = 2  # 日志数据
    COMMENT = 3  # 评论数据
    PROFILE = 4  # 用户


class Record(BaseModel):
    crawl_source: CrawlSource = Field(default=CrawlSource.PC, description='crawl source')
    crawl_type: CrawlType = Field(default=CrawlType.ITEM, description='crawl type')
    crawl_url: str = Field(default=None, description='crawl url')
    crawl_time: Optional[str] = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    data: Optional[Any]
    metadata: Optional[Dict[str, Any]] = Field(default=None)
