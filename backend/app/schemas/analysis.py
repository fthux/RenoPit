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


class DocumentRisk(BaseModel):
    """合同/报价单分析中的单个风险项"""
    id: str = Field(description="风险 ID")
    category: str = Field(description="类别: billing_trap, contract_clause, extra_item")
    title: str = Field(description="问题标题")
    original_text: str = Field(description="文档原文引用")
    critique: str = Field(description="批判分析")
    financial_consequence: str = Field(description="可能的财务后果")
    suggested_fix: str = Field(description="建议的修改方案")


# Alias — DocumentRiskItem is used in API responses and frontend types
DocumentRiskItem = DocumentRisk


class DocumentAnalysisResponse(BaseModel):
    """文档分析结果响应"""
    id: str
    project_id: str
    project_file_id: Optional[str] = None
    status: str = "pending"
    doc_type: str = "unknown"
    confidence: float = 0.0
    summary: str = ""
    total_estimated_risk: str = ""
    risks_count: int = 0
    risks: List[DocumentRisk] = Field(default_factory=list)
    classifications: Optional[Dict[str, Any]] = None
    extra_item_prediction: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentAnalysisListResponse(BaseModel):
    """文档分析列表响应"""
    items: List[DocumentAnalysisResponse] = Field(default_factory=list)
    total: int = 0


class PredictedItem(BaseModel):
    """增项预测中的单个预测项"""
    name: str = Field(description="预测增项名称")
    probability: str = Field(description="发生概率，如 '极高 (95%)'")
    estimated_amount: List[float] = Field(description="估算金额范围，如 [8000, 15000]")
    trigger_phase: str = Field(description="触发阶段，如 '水电阶段'")
    reason: str = Field(description="预测理由，基于报价单分析结果")
    prevention: str = Field(description="预防建议")


class ExtraItemPrediction(BaseModel):
    """增项预测与总花费估算"""
    quoted_total: float = Field(description="报价单表面总价")
    predicted_actual_total: float = Field(description="预测实际总花费")
    confidence_range: List[float] = Field(description="置信区间，如 [160000, 190000]")
    risk_level: str = Field(description="风险等级: low / medium / high")
    predicted_items: List[PredictedItem] = Field(default_factory=list, description="预测增项列表，按概率从高到低排列")


class AnalysisFrontendResponse(BaseModel):
    """前端使用的分析结果格式：
    - summary: AnalysisSummary 对象（含 total_pitfalls, score 等数字统计）
    - pitfalls: 扁平化的 ProblemItem 列表（含 id, severity, category, description, suggestion 等）
    """
    id: str
    project_id: str
    status: str
    summary: Dict[str, Any] = Field(
        default_factory=lambda: {
            "total_pitfalls": 0,
            "critical_count": 0,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0,
            "score": 0,
            "summary_text": "",
        },
        description="前端 summary 对象，包含统计数字和评分",
    )
    pitfalls: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="前端 pitfalls 列表，每个元素包含 id, category, description, severity, location, suggestion",
    )
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime