from abc import ABC

from pygeai.core.base.session import get_session, Session
from pygeai.core.common.exceptions import MissingRequirementException
from pygeai.core.services.rest import ApiService


class BaseClient(ABC):

    def __init__(self, api_key: str = None, base_url: str = None, alias: str = None):
        """
        If commont settings are not specified, they're retrieved from default Session, based on the
        credential files.
        :param api_key: GEAI API KEY to access services
        :param base_url: URL for GEAI instance to be used
        """
        if not (api_key and base_url) and alias:
            self.__session = get_session(alias)
            if not self.__session:
                raise MissingRequirementException("API KEY and BASE URL must be defined in order to use this functionality")
        elif api_key and base_url:
            self.__session = Session(api_key=api_key, base_url=base_url)
        else:
            self.__session = get_session()

        if self.session is None:
            raise MissingRequirementException("Cannot access this functionality without setting API_KEY and BASE_URL")

        self.__api_service = ApiService(base_url=self.session.base_url, token=self.session.api_key)

    @property
    def session(self):
        return self.__session

    @session.setter
    def session(self, session: Session):
        self.__session = session

    @property
    def api_service(self):
        return self.__api_service

    @api_service.setter
    def api_service(self, api_service: ApiService):
        self.__api_service = api_service

