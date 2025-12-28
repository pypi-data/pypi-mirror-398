from pygeai.assistant.managers import AssistantManager
from pygeai.core.feedback.models import FeedbackRequest

feedback_request = FeedbackRequest(
    request_id="28adc1a4-8a21-4d3b-94e2-201534408528",
    origin="user-feedback",
    answer_score=1,
    comments="Great response!"
)

assistant_manager = AssistantManager()

response = assistant_manager.send_feedback(feedback_request=feedback_request)
print(response)