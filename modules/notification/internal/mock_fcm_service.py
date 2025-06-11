from modules.notification.types import FCMResponse

class MockFCMService:
    @staticmethod
    def send_notification(params):
        return FCMResponse(
            success_count=len(params.recipient_tokens),
            failure_count=0,
            failed_tokens=[]
        )