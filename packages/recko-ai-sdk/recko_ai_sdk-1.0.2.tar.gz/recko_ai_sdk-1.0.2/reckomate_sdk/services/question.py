from typing import Dict

from ..client import ReckomateClient
from ..exceptions import ReckomateAPIError


class QuestionService:
    """
    Question SDK Service

    Handles:
    - Question generation (MCQ / descriptive)
    """

    def __init__(self, client: ReckomateClient):
        self.client = client

    # ============================================================
    # GENERATE QUESTIONS
    # ============================================================

    def generate(self, payload: Dict) -> Dict:
        """
        Generate questions for a user.

        Backend:
            POST /questions/generate

        Payload example:
        {
            "file_id": "...",
            "num_questions": 5,
            "difficulty": "medium",
            "language": "English",
            "question_type": "MCQ",
            "num_choices": 4,
            "timer": 60
        }
        """

        response = self.client.post(
            "/questions/generate",
            json=payload
        )

        return self._handle_response(response)

    # ============================================================
    # INTERNAL RESPONSE HANDLER
    # ============================================================

    def _handle_response(self, response):
        try:
            data = response.json()
        except Exception:
            raise ReckomateAPIError(
                status_code=response.status_code,
                message="Invalid JSON response from server"
            )

        if response.status_code >= 400:
            raise ReckomateAPIError(
                status_code=response.status_code,
                message=data.get("detail")
                or data.get("message")
                or "Question generation API error",
                payload=data
            )

        return data
