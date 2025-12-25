from typing import Optional

from pydantic import BaseModel


class Feedback(BaseModel):
    id: str
    created_at: str
    updated_at: str
    given_by: dict
    status: str
    feedback: str
    context: dict
    is_positive: Optional[bool] = None
    user_message: Optional[str] = None
    conversation_title: str


class FeedbackClassification(BaseModel):
    reason: str
    classification: str


class FeedbackClassificationResponse(BaseModel):
    feedback: Feedback
    feedback_classification: FeedbackClassification


class GroundTruthsFromFeedbacks(BaseModel):
    question: str
    groundtruth: str
    additional_notes: str


class GroundTruth(BaseModel):
    source_feedback_id: str
    query: str
    answer: str
    additional_notes: str
