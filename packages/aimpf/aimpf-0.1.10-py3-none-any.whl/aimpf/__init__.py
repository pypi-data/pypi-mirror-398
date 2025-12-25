import os
import sys
# from pycarta import *
from .ui import AimpfCartaProfile

if sys.version_info[:2] >= (3, 8):
    from importlib.metadata import PackageNotFoundError, version  # pragma: no cover
else:
    from importlib_metadata import PackageNotFoundError, version  # pragma: no cover

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = __name__
    __version__ = version(dist_name)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"
finally:
    del version, PackageNotFoundError

# ##### Import customized modules ##### #
from . import (
    contrib as contrib,
    dispatcher as dispatcher,
    mqtt as mqtt,
)

# ##### Import pycarta submodules ##### #
from pycarta import (
    admin as admin,
    auth as auth,
    formsdb as formsdb,  # type: ignore[reportAttributeAccessIssue]
    fs as fs,  # type: ignore[reportAttributeAccessIssue]
    graph as graph,  # type: ignore[reportAttributeAccessIssue]
    # mqtt,  # This masks the aimpf.mqtt package.
    sbg as sbg,
    services as services,
    tablify as tablify,  # type: ignore[reportAttributeAccessIssue]
)


# ##### Top-level pycarta resources ##### #
from pycarta import (
    __CONTEXT as __CONTEXT,
    AuthenticationError as AuthenticationError,
    CartaAgent as CartaAgent,
    CartaLoginUI as CartaLoginUI,
    Group as Group,
    Profile as Profile,
    PycartaContext as PycartaContext,
    SbgLoginManager as SbgLoginManager,
    Singleton as Singleton,
    User as User,
    authorize as authorize,
    get_agent as get_agent,
    ioff as ioff,
    ion as ion,
    is_authenticated as is_authenticated,
    is_interactive as is_interactive,
    login as login,
    service as service,
    set_agent as set_agent,
)

from pycarta.admin.group import is_user_in_group as is_user_in_group


# ##### Manage Carta Environment and Setup ##### #
CARTA_PROFILE = os.environ.get('CARTA_PROFILE') or 'aimpf'


def set_profile():
    _ = AimpfCartaProfile(profile=CARTA_PROFILE)

# from pycarta import login
