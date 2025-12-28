import sys
from typing import Optional

from pygeai import logger
from pygeai.core.common.config import get_settings
from pygeai.core.common.exceptions import MissingRequirementException
from pygeai.core.singleton import Singleton

settings = get_settings()


_session = None


class Session(metaclass=Singleton):
    """
    A session to store configuration state required to interact with different resources.

    :param api_key: str - API key to interact with GEAI
    :param base_url: str - Base URL of the GEAI instance
    :param eval_url: Optional[str] - Optional evaluation endpoint URL
    :return: Session - Instance of the Session class
    :raises: ValueError - If required parameters are missing or invalid
    """

    def __init__(
            self,
            api_key: str = None,
            base_url: str = None,
            eval_url: Optional[str] = None,
    ):
        if not api_key or not base_url:
            logger.warning("Cannot instantiate session without api_key and base_url")

        self.__api_key = api_key
        self.__base_url = base_url
        self.__eval_url = eval_url

        global _session
        _session = self

    @property
    def api_key(self):
        return self.__api_key

    @api_key.setter
    def api_key(self, api_key: str):
        self.__api_key = api_key

    @property
    def base_url(self):
        return self.__base_url

    @base_url.setter
    def base_url(self, base_url: str):
        self.__base_url = base_url

    @property
    def eval_url(self):
        return self.__eval_url

    @eval_url.setter
    def eval_url(self, eval_url: str):
        self.__eval_url = eval_url


def get_session(alias: str = None) -> Session:
    """
    Session is a singleton object:
    On the first invocation, returns Session configured with the API KEY and BASE URL corresponding to the
    alias provided. On the following invocations, it returns the first object instantiated.
    """
    try:
        global _session
        if _session is None:
            if not alias:
                alias = "default"

            _session = Session(
                api_key=settings.get_api_key(alias),
                base_url=settings.get_base_url(alias),
                eval_url=settings.get_eval_url(alias),
            )
        elif _session is not None and alias:
            new_api_key = settings.get_api_key(alias)
            if new_api_key != _session.api_key:
                _session.api_key = new_api_key
                _session.base_url = settings.get_base_url(alias)
                _session.eval_url = settings.get_eval_url(alias)

        if alias:
            logger.debug(f"Alias: {alias}")
            logger.debug(f"Base URL: {_session.base_url}")

        return _session
    except ValueError as e:
        logger.warning(f"Warning: API_KEY and/or BASE_URL not set. {e}")
        sys.stdout.write("Warning: API_KEY and/or BASE_URL not set. Please run geai configure to set them up.\n")
