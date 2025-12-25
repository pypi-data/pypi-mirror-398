from altscore.altdata.model.batch import BatchSyncModule, BatchAsyncModule
from altscore.altdata.model.data_request import RequestSyncModule, RequestAsyncModule


class AltDataSync:

    def __init__(self, altscore_client):
        self.batches = BatchSyncModule(altscore_client)
        self.requests = RequestSyncModule(altscore_client)


class AltDataAsync:

    def __init__(self, altscore_client):
        self.batches = BatchAsyncModule(altscore_client)
        self.requests = RequestAsyncModule(altscore_client)
