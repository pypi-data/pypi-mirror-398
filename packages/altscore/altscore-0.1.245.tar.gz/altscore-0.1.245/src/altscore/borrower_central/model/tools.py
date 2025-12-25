import httpx

from altscore.borrower_central.schemas.communications import MailBody
from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async
from altscore.borrower_central.helpers import build_headers


class ReportGeneratorSyncModule:
    def __init__(self, altscore_client):
        self.altscore_client = altscore_client

    def renew_token(self):
        self.altscore_client.renew_token()

    def build_headers(self):
        return build_headers(self)

    @retry_on_401
    def generate(self, report_request: dict) -> str:
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.post(
                "/v1/tools/generate-report",
                headers=self.build_headers(),
                json=report_request,
                timeout=120
            )
            raise_for_status_improved(response)
            return response.json()["url"]

class ReportGeneratorAsyncModule:
    def __init__(self, altscore_client):
        self.altscore_client = altscore_client

    def renew_token(self):
        self.altscore_client.renew_token()

    def build_headers(self):
        return build_headers(self)

    @retry_on_401_async
    async def generate(self, report_request: dict) -> str:
        with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.post(
                "/v1/tools/generate-report",
                headers=self.build_headers(),
                json=report_request,
                timeout=120
            )
            raise_for_status_improved(response)
            return response.json()["url"]

class CommunicationsSyncModule:
    def __init__(self, altscore_client):
        self.altscore_client = altscore_client

    def renew_token(self):
        self.altscore_client.renew_token()

    def build_headers(self):
        return build_headers(self)

    @retry_on_401
    def send_mail(self, mail_request: MailBody):
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.post(
                "/v1/tools/send-email",
                headers=self.build_headers(),
                json=mail_request.to_dict(),
                timeout=120
            )
            raise_for_status_improved(response)

class CommunicationsAsyncModule:
    def __init__(self, altscore_client):
        self.altscore_client = altscore_client

    def renew_token(self):
        self.altscore_client.renew_token()

    def build_headers(self):
        return build_headers(self)

    @retry_on_401_async
    async def send_mail(self, mail_request: MailBody):
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.post(
                "/v1/tools/send-email",
                headers=self.build_headers(),
                json=mail_request.to_dict(),
                timeout=120
            )
            raise_for_status_improved(response)