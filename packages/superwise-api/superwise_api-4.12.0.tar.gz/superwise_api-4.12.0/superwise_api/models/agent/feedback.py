from uuid import UUID, uuid4

from superwise_api.models import SuperwiseEntity


class EventFeedbackData(SuperwiseEntity):
    answer_id: UUID
    question: str
    answer: str
    is_positive: bool
    negative_feedback_category_harmful: bool
    negative_feedback_category_untrue: bool
    negative_feedback_category_unhelpful: bool
    negative_feedback_category_other: bool
    feedback_description: str
    agent_id: str


def create_event_feedback(
    agent_id: str,
    question: str,
    answer: str,
    is_positive: bool = True,
    negative_feedback_category_harmful: bool = False,
    negative_feedback_category_untrue: bool = False,
    negative_feedback_category_unhelpful: bool = False,
    negative_feedback_category_other: bool = False,
    feedback_description: str = "",
) -> EventFeedbackData:
    return EventFeedbackData(
        agent_id=agent_id,
        answer_id=uuid4(),
        question=question,
        answer=answer,
        is_positive=is_positive,
        negative_feedback_category_harmful=negative_feedback_category_harmful,
        negative_feedback_category_untrue=negative_feedback_category_untrue,
        negative_feedback_category_unhelpful=negative_feedback_category_unhelpful,
        negative_feedback_category_other=negative_feedback_category_other,
        feedback_description=feedback_description,
    )
