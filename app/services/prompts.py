"""Prompt templates and JSON schemas for every LegalLens AI feature.

Design ref: design.md §4.3

Each public function returns a fully-assembled prompt string ready to pass
directly to :func:`app.services.anthropic_client.generate_structured`, together
with the matching JSON schema dict that constrains the model's response shape.

Every prompt automatically includes the shared disclaimer block (FR-8) so no
feature implementation needs to remember to add it.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# FR-8: Shared legal-information disclaimer (injected into every prompt)
# ---------------------------------------------------------------------------
#
# Operationalises the hard requirement that the system must never provide legal
# *advice*, only legal *information*.  Included once per call — not repeated
# per section — to avoid wasting tokens while still enforcing the constraint.
#
LEGAL_DISCLAIMER_BLOCK: str = (
    "IMPORTANT INSTRUCTION (applies to this entire response):\n"
    "You provide legal information, not legal advice. "
    "Do not tell the user what to decide. "
    "Do not present any output as a definitive legal conclusion or recommendation. "
    "If asked for a definitive legal recommendation (e.g. 'should I sign this', "
    "'will I win in court'), explain the relevant facts from the document and "
    "explicitly recommend consulting a licensed attorney. "
    "Never claim to create, or imply the existence of, an attorney-client relationship."
)


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _with_disclaimer(body: str) -> str:
    """Prepend the shared disclaimer block to *body*."""
    return f"{LEGAL_DISCLAIMER_BLOCK}\n\n{body}"


# ---------------------------------------------------------------------------
# FR-2: Plain-language simplification
# ---------------------------------------------------------------------------

SIMPLIFY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "overview": {
            "type": "string",
            "description": (
                "A short 'in plain English, this document means...' paragraph "
                "that captures the top-level purpose and most important points."
            ),
        },
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "heading": {"type": "string"},
                    "original_excerpt_ref": {
                        "type": "string",
                        "description": "Brief quote or reference to the original clause.",
                    },
                    "plain_language": {
                        "type": "string",
                        "description": "Plain-English explanation of this clause.",
                    },
                },
                "required": ["heading", "original_excerpt_ref", "plain_language"],
            },
        },
    },
    "required": ["overview", "sections"],
}


def build_simplify_prompt(document_text: str) -> str:
    """Build the simplification prompt for *document_text*."""
    body = (
        "You are a legal document interpreter.\n"
        "Produce a plain-language explanation of the legal document below.\n"
        "Preserve all obligations, deadlines, monetary amounts, and termination conditions.\n"
        "Do not omit any materially important clause.\n"
        "Avoid legal jargon; where unavoidable, define the term inline.\n\n"
        "Return a JSON object matching the provided schema:\n"
        "- 'overview': a short top-level plain-English summary of the whole document.\n"
        "- 'sections': an array of objects, one per distinct clause/section, each with\n"
        "  'heading', 'original_excerpt_ref' (brief quote or reference), and\n"
        "  'plain_language' (your plain-English explanation).\n\n"
        f"DOCUMENT:\n{document_text}"
    )
    return _with_disclaimer(body)


# ---------------------------------------------------------------------------
# FR-5: Risk & clause highlighting
# ---------------------------------------------------------------------------

RISKS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "categories": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": (
                            "Topic category, e.g. Financial, Termination, Liability, "
                            "Privacy, Obligations, Auto-Renewal, Indemnification."
                        ),
                    },
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "clause_ref": {
                                    "type": "string",
                                    "description": "Reference to the clause/section/page.",
                                },
                                "severity": {
                                    "type": "string",
                                    "enum": ["high", "medium", "low", "info"],
                                },
                                "explanation": {
                                    "type": "string",
                                    "description": (
                                        "One-sentence plain-English explanation of why "
                                        "this clause may be worth reviewing."
                                    ),
                                },
                            },
                            "required": ["clause_ref", "severity", "explanation"],
                        },
                    },
                },
                "required": ["category", "items"],
            },
        },
    },
    "required": ["categories"],
}


def build_risks_prompt(document_text: str) -> str:
    """Build the risk-analysis prompt for *document_text*."""
    body = (
        "You are a legal document risk reviewer.\n"
        "Identify clauses in the document below that represent obligations, restrictions,\n"
        "deadlines, penalties, auto-renewals, liability, indemnification, or termination\n"
        "conditions.\n\n"
        "For each risk item:\n"
        "- Assign a severity: 'high', 'medium', 'low', or 'info'.\n"
        "- Write the explanation as 'This clause may be worth reviewing because...' — "
        "never as a definitive legal verdict.\n"
        "- Group items by category (Financial, Termination, Liability, Privacy, "
        "Obligations, Auto-Renewal, Indemnification, or Other).\n\n"
        f"DOCUMENT:\n{document_text}"
    )
    return _with_disclaimer(body)


# ---------------------------------------------------------------------------
# FR-6: Checklist / next-steps generator
# ---------------------------------------------------------------------------

CHECKLIST_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "ask_lawyer": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Questions and items to raise with a lawyer or the other party.",
        },
        "verify_yourself": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Things the user can check or verify on their own.",
        },
    },
    "required": ["ask_lawyer", "verify_yourself"],
}


def build_checklist_prompt(document_text: str) -> str:
    """Build the checklist prompt for *document_text*."""
    body = (
        "You are a legal document advisor.\n"
        "Based on the document below, generate an actionable checklist of items the user\n"
        "should address before signing or acting on this document.\n\n"
        "Separate items into two categories:\n"
        "- 'ask_lawyer': questions or items to raise with a licensed attorney or "
        "the other party.\n"
        "- 'verify_yourself': things the user can check or confirm on their own "
        "(e.g. dates, amounts, names match expectations).\n\n"
        f"DOCUMENT:\n{document_text}"
    )
    return _with_disclaimer(body)


# ---------------------------------------------------------------------------
# FR-3: Document comparison
# ---------------------------------------------------------------------------

COMPARE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "shared_topics": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "doc_a_position": {"type": "string"},
                    "doc_b_position": {"type": "string"},
                    "materially_different": {"type": "boolean"},
                    "why_it_matters": {"type": "string"},
                },
                "required": [
                    "topic",
                    "doc_a_position",
                    "doc_b_position",
                    "materially_different",
                    "why_it_matters",
                ],
            },
        },
        "only_in_a": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Clauses/topics present only in document A.",
        },
        "only_in_b": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Clauses/topics present only in document B.",
        },
    },
    "required": ["shared_topics", "only_in_a", "only_in_b"],
}


def build_compare_prompt(
    doc_a: str,
    doc_b: str,
    label_a: str = "Document A",
    label_b: str = "Document B",
) -> str:
    """Build the comparison prompt for *doc_a* and *doc_b*."""
    body = (
        "You are a legal document comparison specialist.\n"
        f"Compare `{label_a}` and `{label_b}` below.\n\n"
        "Identify:\n"
        "1. Topics that appear in both documents — for each, state what each document "
        "says, whether they are materially different, and why that difference may matter.\n"
        "2. Topics/clauses present only in one document.\n\n"
        "If the documents are structurally very different types (e.g. a lease vs. a loan "
        "agreement), still perform a best-effort comparison and note the structural "
        "difference in the relevant 'why_it_matters' fields.\n\n"
        f"--- `{label_a}` ---\n{doc_a}\n\n"
        f"--- `{label_b}` ---\n{doc_b}"
    )
    return _with_disclaimer(body)


# ---------------------------------------------------------------------------
# FR-4: Document-grounded Q&A
# ---------------------------------------------------------------------------

QA_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "answer": {
            "type": "string",
            "description": (
                "Plain-English answer grounded solely in the document. "
                "If the answer is not in the document, state that clearly."
            ),
        },
        "found_in_document": {
            "type": "boolean",
            "description": (
                "True if the document contains information that answers the question; "
                "false if the document does not address the question."
            ),
        },
        "supporting_clause_ref": {
            "type": ["string", "null"],
            "description": (
                "Reference to the relevant clause, section, or page. "
                "Null when found_in_document is false."
            ),
        },
    },
    "required": ["answer", "found_in_document", "supporting_clause_ref"],
}


def build_qa_prompt(
    document_text: str,
    question: str,
    history: list[dict[str, str]] | None = None,
) -> str:
    """Build the Q&A prompt for *question* grounded in *document_text*.

    Parameters
    ----------
    document_text:
        The full document text.
    question:
        The user's current question.
    history:
        Optional list of prior turns, each a dict with keys ``"role"``
        (``"user"`` or ``"assistant"``) and ``"content"``.
    """
    history_block = ""
    if history:
        turns = "\n".join(
            f"{turn['role'].capitalize()}: {turn['content']}" for turn in history
        )
        history_block = f"CONVERSATION HISTORY (for context):\n{turns}\n\n"

    body = (
        "You are a legal document assistant.\n"
        "Answer the user's question using ONLY the content of the document provided.\n"
        "Do NOT use outside legal knowledge to invent an answer.\n"
        "If the document does not contain information that answers the question:\n"
        "  - set 'found_in_document' to false\n"
        "  - set 'supporting_clause_ref' to null\n"
        "  - state clearly in 'answer' that the document does not address this point\n"
        "  - do NOT fabricate or guess an answer from general legal knowledge\n"
        "When found_in_document is true, always cite the relevant clause or page "
        "reference in 'supporting_clause_ref'.\n\n"
        f"{history_block}"
        f"DOCUMENT:\n{document_text}\n\n"
        f"QUESTION: {question}"
    )
    return _with_disclaimer(body)
