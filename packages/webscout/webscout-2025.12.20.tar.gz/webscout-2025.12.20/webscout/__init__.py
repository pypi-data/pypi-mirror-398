# webscout/__init__.py

from .search import *
from .version import __version__
from .Provider import *
from .AIauto import *
from .Provider.TTI import *
from .Provider.TTS import *
from .Provider.AISEARCH import *
from .Provider.STT import *
from .Extra import *
from .optimizers import *
from .swiftcli import *
from .litagent import LitAgent
from .client import Client
from .scout import *
from .zeroart import *
from .AIutel import *

useragent = LitAgent()
# Add update checker
from .update_checker import check_for_updates
try:
    update_message = check_for_updates()
    if update_message:
        print(update_message)
except Exception as e:
    pass
# Import models for easy access
from .models import model