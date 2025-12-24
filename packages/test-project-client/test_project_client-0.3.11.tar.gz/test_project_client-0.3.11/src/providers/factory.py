from functools import lru_cache
import logging
from src.config import Settings
from src.business.context import ServiceContext
from src.providers.openai.raw import OpenaiClient
from src.providers.middesk.raw import MiddeskClient
from src.providers.dome.raw import DomeClient
from src.providers.runpod.raw import RunpodClient
class ProviderFactory:
    def __init__(self, settings: Settings):
        self.settings = settings

    def create_context(self) -> ServiceContext:
        return ServiceContext(
            config=self.settings,
            logger=logging.getLogger("platform"),
            openai=self._create_openai_client(),
            middesk=self._create_middesk_client(),
            dome=self._create_dome_client(),
            runpod=self._create_runpod_client(),        )

    def _create_openai_client(self) -> OpenaiClient:
        return OpenaiClient(
            base_url=self.settings.OPENAI_BASE_URL,
            token=self.settings.OPENAI_API_KEY
        )

    def _create_middesk_client(self) -> MiddeskClient:
        return MiddeskClient(
            base_url=self.settings.MIDDESK_BASE_URL,
            token=self.settings.MIDDESK_API_KEY
        )

    def _create_dome_client(self) -> DomeClient:
        return DomeClient(
            base_url=self.settings.DOME_BASE_URL,
            token=self.settings.DOME_API_KEY
        )

    def _create_runpod_client(self) -> RunpodClient:
        return RunpodClient(
            base_url=self.settings.RUNPOD_BASE_URL,
            token=self.settings.RUNPOD_API_KEY
        )