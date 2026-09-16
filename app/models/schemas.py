"""Pydantic request/response models for LegalLens AI endpoints."""

from __future__ import annotations

from enum import Enum
from typing import List

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# FR-1: Document ingestion
# ---------------------------------------------------------------------------

class ExtractTextRequest(BaseModel):
    """Request body when the caller sends pasted text (no file upload)."""

    text: str = Field(..., min_length=1, description="Raw document text pasted by the user.")


class ExtractResponse(BaseModel):
    """Successful response from POST /api/documents/extract."""

    text: str = Field(..., description="Full extracted (or passed-through) document text.")
    word_count: int = Field(..., ge=0, description="Number of whitespace-delimited words.")
    page_count: int = Field(
        ...,
        ge=0,
        description="Number of pages in the source PDF, or 0 for pasted text.",
    )


# ---------------------------------------------------------------------------
# Shared error envelope
# ---------------------------------------------------------------------------

class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    """Uniform error body for all 4xx / 5xx responses."""

    error: ErrorDetail


# ---------------------------------------------------------------------------
# FR-2: Plain-language simplification
# ---------------------------------------------------------------------------

class SimplifyRequest(BaseModel):
    """Request body for POST /api/analyze/simplify."""

    text: str = Field(..., min_length=1, description="Raw document text to simplify.")


class SimplifySection(BaseModel):
    """A single clause/section in the simplification output."""

    heading: str = Field(..., description="Section or clause heading.")
    original_excerpt_ref: str = Field(
        ..., description="Brief quote or reference to the original clause."
    )
    plain_language: str = Field(
        ..., description="Plain-English explanation of this clause."
    )


class SimplifyResponse(BaseModel):
    """Successful response from POST /api/analyze/simplify."""

    overview: str = Field(
        ...,
        description=(
            "A short 'in plain English, this document means...' paragraph "
            "capturing the top-level purpose and most important points."
        ),
    )
    sections: List[SimplifySection] = Field(
        ..., description="One entry per distinct clause/section."
    )


# ---------------------------------------------------------------------------
# FR-5: Risk & clause highlighting
# ---------------------------------------------------------------------------

class Severity(str, Enum):
    """Severity levels for risk items."""
    high = "high"
    medium = "medium"
    low = "low"
    info = "info"


class RisksRequest(BaseModel):
    """Request body for POST /api/analyze/risks."""

    text: str = Field(..., min_length=1, description="Raw document text to analyse for risks.")


class RiskItem(BaseModel):
    """A single risk clause item within a category."""

    clause_ref: str = Field(..., description="Reference to the clause, section, or page.")
    severity: Severity = Field(..., description="Severity level: high, medium, low, or info.")
    explanation: str = Field(
        ..., description="Plain-English explanation of why this clause may be worth reviewing."
    )


class RiskCategory(BaseModel):
    """A group of risk items sharing the same topic category."""

    category: str = Field(
        ...,
        description=(
            "Topic category, e.g. Financial, Termination, Liability, "
            "Privacy, Obligations, Auto-Renewal, Indemnification."
        ),
    )
    items: List[RiskItem] = Field(..., description="Risk items belonging to this category.")


class RisksResponse(BaseModel):
    """Successful response from POST /api/analyze/risks."""

    categories: List[RiskCategory] = Field(
        ..., description="Risk items grouped by topic category."
    )


# ---------------------------------------------------------------------------
# FR-6: Checklist / next-steps generator
# ---------------------------------------------------------------------------

class ChecklistRequest(BaseModel):
    """Request body for POST /api/analyze/checklist."""

    text: str = Field(..., min_length=1, description="Raw document text to generate a checklist for.")


class ChecklistResponse(BaseModel):
    """Successful response from POST /api/analyze/checklist."""

    ask_lawyer: List[str] = Field(
        ..., description="Questions and items to raise with a licensed attorney or the other party."
    )
    verify_yourself: List[str] = Field(
        ..., description="Things the user can check or verify on their own."
    )


# ---------------------------------------------------------------------------
# FR-3: Document comparison
# ---------------------------------------------------------------------------

class CompareRequest(BaseModel):
    """Request body for POST /api/analyze/compare."""

    doc_a: str = Field(..., min_length=1, description="Full text of the first document.")
    doc_b: str = Field(..., min_length=1, description="Full text of the second document.")
    label_a: str = Field(
        default="Document A",
        max_length=200,
        description="Human-readable label for the first document.",
    )
    label_b: str = Field(
        default="Document B",
        max_length=200,
        description="Human-readable label for the second document.",
    )


class SharedTopic(BaseModel):
    """A topic that appears in both documents being compared."""

    topic: str = Field(..., description="Short name for the shared topic or clause.")
    doc_a_position: str = Field(
        ..., description="What the first document says about this topic."
    )
    doc_b_position: str = Field(
        ..., description="What the second document says about this topic."
    )
    materially_different: bool = Field(
        ...,
        description="True if the two positions represent a material difference.",
    )
    why_it_matters: str = Field(
        ...,
        description=(
            "Plain-English explanation of why the difference (or similarity) is significant. "
            "When the documents are very different types, this field carries the structural note."
        ),
    )


class CompareResponse(BaseModel):
    """Successful response from POST /api/analyze/compare."""

    shared_topics: List[SharedTopic] = Field(
        ...,
        description=(
            "Topics/clauses that appear in both documents, with each document's position. "
            "When the documents are of very different types, the why_it_matters field of "
            "each entry notes the structural difference."
        ),
    )
    only_in_a: List[str] = Field(
        ..., description="Clauses/topics present only in the first document."
    )
    only_in_b: List[str] = Field(
        ..., description="Clauses/topics present only in the second document."
    )


# ---------------------------------------------------------------------------
# FR-4: Document-grounded Q&A
# ---------------------------------------------------------------------------

class HistoryItem(BaseModel):
    """A single conversational turn (prior Q&A exchange)."""

    role: str = Field(
        ...,
        description="Speaker role: 'user' or 'assistant'.",
    )
    content: str = Field(
        ...,
        description="The text of this conversational turn.",
    )


class QARequest(BaseModel):
    """Request body for POST /api/analyze/qa."""

    text: str = Field(..., min_length=1, description="Raw document text to query against.")
    question: str = Field(..., min_length=1, max_length=2000, description="The user's question about the document.")
    history: List[HistoryItem] = Field(
        default_factory=list,
        description=(
            "Optional list of prior conversation turns for follow-up questions. "
            "Each item has 'role' ('user' or 'assistant') and 'content'."
        ),
    )


class QAResponse(BaseModel):
    """Successful response from POST /api/analyze/qa."""

    answer: str = Field(
        ...,
        description=(
            "Plain-English answer grounded solely in the document. "
            "States clearly that the document doesn't address the point when "
            "found_in_document is false."
        ),
    )
    found_in_document: bool = Field(
        ...,
        description=(
            "True if the document contains information that answers the question; "
            "false if the document does not address the question."
        ),
    )
    supporting_clause_ref: str | None = Field(
        ...,
        description=(
            "Reference to the relevant clause, section, or page. "
            "Null when found_in_document is false."
        ),
    )
