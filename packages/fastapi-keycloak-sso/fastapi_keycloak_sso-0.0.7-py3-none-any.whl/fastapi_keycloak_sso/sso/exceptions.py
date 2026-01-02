from fastapi import HTTPException

class SSOUserNotFound(HTTPException):
    def __init__(self, user_id: str):
        super().__init__(
            status_code=400,
            detail={"error": "User not found in SSO", "user_id": user_id}
        )
