import os
import logging
from enum import Enum
from pycarta.admin.user import get_current_user
from pycarta.mqtt.credentials import TLSCredentials
from pycarta.mqtt.subscriber import Subscriber as BaseSubscriber
from .base import AimpfBase, Project
from .formatter import CamxFormatter


logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())


class AimpfSubscriber(BaseSubscriber, AimpfBase):
    CARTA_CREDENTIAL_PATH = os.environ.get("AIMPF_MQTT_SUBSCRIBER_CREDENTIALS", "/mqtt/aimpf/subscriber.zip")

    def __init__(self,
                 project: str | Enum,
                 *,
                 node: str="+",
                 device: str="+",  # operator name
                 metric: str="+",  # function name
                 credentials: str | TLSCredentials | None=None,
                 cache: bool=True,
                 qos: int=0,
                 options=None,
                 properties=None,
                 **kwargs):
        """
        Subscribes to a channel in the AMPF MQTT infrastructure. Credentials
        must be requested from Andy Dugenske (dugenske@gatech.edu) or Matt
        Kosmala (mkosmala3@gatech.edu). Once cached (the default), your
        credentials will be accessible to you, and only you, through Carta.

        You must be logged into Carta for this to work correctly. Be sure
        you've logged in using `aimpf.login`.

        Environment Variables
        ---------------------
        - AIMPF_MQTT_BROKER: This is set by the organization and should not be
        changed.
        - AIMPF_MQTT_PORT: This is set by the organization and should not be
        changed.
        - AIMPF_MQTT_SUBSCRIBER_CREDENTIALS: Where Carta should store your
        subscriber credentials. As before, you should only need to change this
        if you have multiple sets of subscriber credentials. Note: this is
        different than being able to subscribe to multiple topics. It is common
        for one set of credentials to be allowed to access multiple topics.

        Parameters
        ----------
        project : str
            The project to which the data should be published. This is
            required and must match a known project. (Use
            `aimpf.mqtt.project.get_projects` to get a list of active
            projects.)
        node : str | None
            The compute environment from which the data originates. Default:
            pycarta.
        device : str | None
            The entity that creates the data. Default: you -- your username.
        metric : str | None
            A name for the measurement/calculation. Default: the name of the
            function used to create the value.
        credentials : str | TLSCredentials | None
            The MQTT credentials you received from Andy Dugenske. If None
            (default), this looks in Carta for your credentials. You can
            provide a filename of the zipped credentials. TLSCredentials
            provides other options, if neither of these work for you.
        cache : bool
            Cache your credentials in Carta. Default: True.
        qos : int
            MQTT quality of service
        **kwargs
            All other keyword arguments are passed to the MQTT Connection.
        """
        self.project = (Project[project] if isinstance(project, str) else project).name
        self.node = node
        self.device = device
        self.metric = metric

        self.formatter = kwargs.pop("formatter", None) or \
            CamxFormatter(
                projectLabel=project,
                assetId=self.device,
                dataItemId=self.metric,
                operatorId=get_current_user().name,
            )

        # topic is inherited from BasePublisher
        super().__init__(topic=None,
                         host=AimpfSubscriber.HOST,
                         port=AimpfSubscriber.PORT,
                         credentials=AimpfSubscriber._get_credentials(credentials, cache=cache),
                         qos=qos,
                         options=options,
                         properties=properties,
                         formatter=self.formatter,
                         **kwargs)

    def set_topic(self):
        self.topic = f"spBv1.0/{self.project:s}/DDATA/{self.node}/{self.device}/{self.metric}"
        self.kwargs["topic"] = self.topic
        logger.debug("Topic: %s", self.topic)
    
    def __call__(self, fn) -> BaseSubscriber.Task | BaseSubscriber.AsyncTask:
        task = super().__call__(fn)
        self.metric = self.metric or task.fn.__name__
        self.set_topic()
        return task