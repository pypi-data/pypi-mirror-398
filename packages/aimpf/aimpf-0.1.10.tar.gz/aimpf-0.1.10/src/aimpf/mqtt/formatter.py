from datetime import datetime, timezone
from typing import Any
from pycarta.mqtt.formatter import Formatter
from shortuuid import uuid
import json


class CamxFormatter(Formatter):
    def __init__(self,
                 *,
                 projectLabel,
                 assetId: str,
                 dataItemId: str,
                 operatorId: str):
        self.projectLabel = str(projectLabel)
        self.assetId = str(assetId)
        self.dateTime = None
        self.dataItemId = str(dataItemId)
        self.operatorId = str(operatorId)

    def pack(self, data: Any) -> bytes:
        return json.dumps({
                "projectLabel": self.projectLabel,
                "assetId": self.assetId,
                "dateTime": datetime.now(timezone.utc).isoformat(),
                "dataItemId": self.dataItemId,
                "value": data,
                "operatorId": self.operatorId,
                "messageId": uuid()
            }).encode("utf-8")
    
    def unpack(self, data: bytes) -> Any:
        # Modifies formatter settings based on content read.
        content = json.loads(data.decode("utf-8"))
        self.projectLabel = content["projectLabel"]
        self.assetId = content["assetId"]
        self.dateTime = datetime.fromisoformat(content["dateTime"])
        self.dataItemId = content["dataItemId"]
        self.operatorId = content["operatorId"]
        return content["value"]
