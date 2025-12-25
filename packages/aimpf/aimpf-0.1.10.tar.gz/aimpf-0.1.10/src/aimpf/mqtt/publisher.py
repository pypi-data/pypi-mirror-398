import os
import logging
from enum import Enum
from typing import Sequence
from pycarta.admin.user import get_current_user
from pycarta.mqtt.credentials import TLSCredentials
from pycarta.mqtt.publisher import Publisher as BasePublisher
from .base import AimpfBase, Project
from .formatter import CamxFormatter
from .logger import AimpfLogger, LEVEL_MAP


logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())


class AimpfPublisher(BasePublisher, AimpfBase):
    CARTA_CREDENTIAL_PATH = os.environ.get("AIMPF_MQTT_PUBLISHER_CREDENTIALS", "/mqtt/aimpf/publisher.zip")

    def __init__(self,
                 project: str | Enum,
                 *,
                 node: str | None=None,    # pycarta
                 device: str | None=None,  # operator name
                 metric: str | None=None,  # function name
                 credentials: str | TLSCredentials | None=None,
                 cache: bool=True,
                 admin_credentials: str | TLSCredentials | None=None,
                 admin_levels: Sequence[str] | None = None,
                 admin_idle_timeout: float | None = None,
                 **kwargs):
        """
        Publishes data to the AMPF MQTT infrastructure. Credentials must be
        requested from Andy Dugenske (dugenske@gatech.edu) or Matt Kosmala
        (mkosmala3@gatech.edu). Once cached (the default), your credentials
        will be accessible to you, and only you, through Carta.

        You must be logged into Carta for this to work correctly. Be sure
        you've logged in using `aimpf.login`.

        Environment Variables
        ---------------------
        - AIMPF_MQTT_BROKER: This is set by the organization and should not be
        changed.
        - AIMPF_MQTT_PORT: This is set by the organization and should not be
        changed.
        - AIMPF_MQTT_PUBLISHER_CREDENTIALS: Where Carta should store your
        publisher credentials. You should only need to change this if you have
        multiple sets of publisher credentials. This is not common.
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
        **kwargs
            All other keyword arguments are passed to the MQTT Connection.

        Examples
        --------

            @publish(project=..., node=..., device=..., metric=..., credentials)
            def my_metric():
                return "Hello, world!"
        """
        proj_enum = (Project[project] if isinstance(project, str) else project)  # type: ignore[reportIndexIssue]
        self._proj_enum = proj_enum
        self.project = proj_enum.name
        self.node = node or "pycarta"
        self.device = device or get_current_user().name
        self.metric = metric or "unknown"
        # topic is inherited from BasePublisher
        super().__init__("",
                         host=AimpfPublisher.HOST,
                         port=AimpfPublisher.PORT,
                         credentials=AimpfPublisher._get_credentials(credentials, cache=cache),
                         formatter=CamxFormatter(projectLabel=self.project,
                                                 assetId=self.device,
                                                 dataItemId=self.metric,
                                                 operatorId=get_current_user().name),
                         **kwargs)

        self.loggers: list[AimpfLogger] = []
        if admin_levels:
            invalid = list(set(admin_levels) - set(LEVEL_MAP))
            if invalid:
                raise ValueError(
                    f"Invalid admin_levels {invalid}; must be one of {list(LEVEL_MAP)}"
                )
            if not admin_credentials:
                raise ValueError("`admin_credentials` must be provided when `admin_levels` is specified.")
            mlogger = AimpfLogger(
                project=self.project,
                node=self.node,
                device=self.device,
                levels=admin_levels,
                idle_timeout=admin_idle_timeout,
                credentials=AimpfPublisher._get_credentials(admin_credentials, cache=cache),
            ).start()
            self.loggers.append(mlogger)

    def set_topic(self) -> None:
        self.topic = f"spBv1.0/{self.project:s}/DDATA/{self.node}/{self.device}/{self.metric}"
        logger.debug("Topic: %s", self.topic)
    
    def __call__(self, fn) -> BasePublisher.Task | BasePublisher.AsyncTask:
        task = super().__call__(fn)
        if isinstance(fn, (BasePublisher.Task, BasePublisher.AsyncTask)):
            new_metric = self.metric or fn.fn.__name__
        else:
            new_metric = self.metric or fn.__name__
        self.metric = new_metric
        self.formatter.dataItemId = new_metric  # type: ignore[reportAttributeAccessIssue]
        self.set_topic()
        setattr(task, "loggers", self.loggers)
        return task
