import logging
from abc import ABC
# from pycarta.auth import CartaAgent
from pycarta.auth import CartaAgent

logger = logging.getLogger(__name__)

__all__ = ["Dispatcher"]


class Dispatcher(ABC):
    """
    Base class for dispatchers.
    """
    def __init__(
        self,
        auth: CartaAgent,
        *,
        namespace: None | str=None,
        service: None | str=None,
        host: None | str=None
    ):
        """
        :param auth:
            The authorization agent to use.
        :param namespace:
            The Carta namespace to use. Required if `host` is not specified.
        :param service:
            The Carta service to use. Required if `host` is not specified.
        :param host:
            The URL of the dispatcher. This is used for Dispatchers that have
            not been registered as a Carta service.
        """
        if namespace is not None and service is not None:
            if auth.host is None:
                raise ValueError("Auth agent must have a host defined when using namespace/service.")
            self._auth: CartaAgent = CartaAgent(
                token=auth.token,
                host=auth.host + f"/service/{namespace}/{service}")
        elif host is not None:
            self._auth: CartaAgent = CartaAgent(
                token=auth.token,
                host=str(host))
            self._auth._session.headers.update({"X_CARTA_TOKEN": f"Bearer {self._auth.token}"})
        else:
            raise ValueError(
                "If registered as a Carta service, specify 'namespace' and "
                "'service'. If not, specify 'host'.")
        
    @property
    def auth(self):
        """
        The authorization agent.
        """
        return self._auth
        
    @property
    def url(self):
        """
        The URL of the dispatcher.
        """
        return self.auth.url
    
    @url.setter
    def url(self, value: str):
        """
        Set the URL of the dispatcher.
        """
        self.auth.url = value
