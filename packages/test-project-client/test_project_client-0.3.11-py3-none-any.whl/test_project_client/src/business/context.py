from dataclasses import dataclass
import logging
from src.config import Settings
from src.providers.openai.raw import OpenaiClient
from src.providers.middesk.raw import MiddeskClient
from src.providers.dome.raw import DomeClient
from src.providers.runpod.raw import RunpodClient
@dataclass
class ServiceContext:
    config: Settings
    logger: logging.Logger
    openai: OpenaiClient
    middesk: MiddeskClient
    dome: DomeClient
    runpod: RunpodClient