"""
Pydantic models for structured crawl results
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class EntityData(BaseModel):
    """Entity extraction data"""

    emails: List[str] = Field(default_factory=list)
    phones: List[str] = Field(default_factory=list)
    usernames: List[str] = Field(default_factory=list)
    domains: List[str] = Field(default_factory=list)


class TechStackData(BaseModel):
    """Technology stack data"""

    frameworks: List[str] = Field(default_factory=list)
    cms: List[str] = Field(default_factory=list)
    servers: List[str] = Field(default_factory=list)
    libraries: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)


class PageData(BaseModel):
    """Page data model"""

    url: str
    title: Optional[str] = None
    content: Optional[str] = None
    html: Optional[str] = None
    status_code: int = 200
    page_type: Optional[str] = None
    page_type_confidence: Optional[Dict[str, float]] = None
    entities: Optional[EntityData] = None
    tech_stack: Optional[TechStackData] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CrawlResult(BaseModel):
    """Complete crawl result"""

    pages: List[PageData] = Field(default_factory=list)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
