from altscore.comms.model.webhooks import WebhookSyncModule, WebhookAsyncModule


class CommsSync:
    def __init__(self, altscore_client):
        self.webhooks = WebhookSyncModule(altscore_client)

class CommsAsync:
    def __init__(self, altscore_client):
        self.webhooks = WebhookAsyncModule(altscore_client)
