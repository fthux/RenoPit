"""
Analysis Schemas — 分析结果的 Pydantic 响应模型
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field


class BBox(BaseModel):
    """AI 返回的 bbox 坐标"""
    x: float
    y: float
    width: float
    height: float


class ProblemItem(BaseModel):
    """单个问题详情"""
    bbox: BBox
    title: str = Field(description="问题标题")
    location: str = Field(description="位置描述，如 '客厅电视背景墙'")
    critique: str = Field(description="批判分析，具体分析设计的问题")
    trap_explanation: str = Field(description="套路揭露，指出常见的行业套路")
    alternative: str = Field(description="替代方案，给出更好的设计建议")


class AnalysisResponse(BaseModel):
    """分析结果响应"""
    id: str
    project_id: str
    status: str = "pending"
    problems_count: int = 0
    result_json: Optional[Dict[str, Any]] = None
    raw_result_json: Optional[Dict[str, Any]] = Field(
        default=None,
        description="AI 返回的完整 JSON 结果，顶层含 problems 数组",
    )
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalysisSummary(BaseModel):
    """分析结果摘要（含 problems 列表）"""
    total_problems: int = 0
    problems: List[ProblemItem] = Field(default_factory=list)