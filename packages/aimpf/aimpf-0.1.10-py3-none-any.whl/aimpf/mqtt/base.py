import os
import logging
from pycarta.mqtt.credentials import TLSCredentials
from .projects import ProjectEnumFactory


logger = logging.getLogger(__name__)


Project = ProjectEnumFactory()


class AimpfBase:
    HOST = os.environ.get("AIMPF_MQTT_BROKER") or "aop63bhe1nwsr-ats.iot.us-east-1.amazonaws.com"
    PORT = int(os.environ.get("AIMPF_MQTT_PORT") or 8883)
    CARTA_CREDENTIAL_PATH = os.environ.get("AIMPF_MQTT_PUBLISHER_CREDENTIALS") or "/mqtt/aimpf/credentials.zip"

    @classmethod
    def _get_credentials(cls, credentials: str | TLSCredentials | None=None, *, cache: bool=True) -> TLSCredentials:
        if isinstance(credentials, TLSCredentials):
            logger.debug("[aimpf.mqtt] Using provided TLS credentials.")
            cred = credentials
        elif isinstance(credentials, str):
            logger.debug("[aimpf.mqtt] Reading local TLS credentials from %s", credentials)
            try:
                cred = TLSCredentials().local.read(credentials)
            except:
                raise ValueError(f"Could not read TLS credentials from "
                                 f"{credentials}. Provide a path to a local "
                                 f"file to set credentials.")
        elif credentials is None:
            logger.debug("[aimpf.mqtt] Reading Carta TLS credentials.")
            try:
                cred = TLSCredentials().carta.read(cls.CARTA_CREDENTIAL_PATH)
            except:
                raise ValueError("No TLS credentials provided. Provide a path "
                                 "to a local file to set credentials.")
        else:
            raise ValueError(f"{type(credentials)} is not a recognized credential. "
                              "Please pass TLS credentials, local credential path or None.")
        # Store these credentials in Carta
        if cache:
            logger.debug("[aimpf.mqtt] Caching credentials in Carta.")
            cred.carta.write(cls.CARTA_CREDENTIAL_PATH)

        return cred # type: ignore[reportReturnType]
