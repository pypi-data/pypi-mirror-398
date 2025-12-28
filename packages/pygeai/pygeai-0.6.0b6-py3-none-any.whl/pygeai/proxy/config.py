from pygeai.core.common.config import SettingsManager
from typing import Optional
import uuid
import os

class ProxySettingsManager(SettingsManager):
    """
    Settings manager for the GEAI proxy.
    Extends the base SettingsManager with proxy-specific settings.

    :param DEFAULT_ALIAS: str - Default alias for proxy settings
    """
    
    DEFAULT_ALIAS = "default"
   
    def __init__(self):
        super().__init__()
        self._current_alias = self.DEFAULT_ALIAS

    def get_current_alias(self) -> str:
        return self._current_alias

    def set_current_alias(self, alias: str):
        self._current_alias = alias

    def get_proxy_id(self, alias: str = DEFAULT_ALIAS) -> Optional[uuid.UUID]:
        """
        Get the proxy ID for a specific alias.

        :param alias: str - Alias for the settings section. Defaults to DEFAULT_ALIAS.
        :return: Optional[uuid.UUID] - Proxy ID if set, None otherwise
        """
        id_str = self.get_setting_value("PROXY_ID", alias)
        return uuid.UUID(id_str) if id_str else None

    def set_proxy_id(self, proxy_id: uuid.UUID, alias: str = DEFAULT_ALIAS):
        """
        Set the proxy ID for a specific alias.

        :param proxy_id: uuid.UUID - Proxy ID to set
        :param alias: str - Alias for the settings section. Defaults to DEFAULT_ALIAS.
        """
        self.set_setting_value("PROXY_ID", str(proxy_id), alias)

    def get_proxy_name(self, alias: str = DEFAULT_ALIAS) -> Optional[str]:
        """
        Get the proxy name for a specific alias.

        :param alias: str - Alias for the settings section. Defaults to DEFAULT_ALIAS.
        :return: Optional[str] - Proxy name if set, None otherwise
        """
        return self.get_setting_value("PROXY_NAME", alias)

    def set_proxy_name(self, name: str, alias: str = DEFAULT_ALIAS):
        """
        Set the proxy name for a specific alias.

        :param name: str - Proxy name to set
        :param alias: str - Alias for the settings section. Defaults to DEFAULT_ALIAS.
        """
        self.set_setting_value("PROXY_NAME", name, alias)

    def get_proxy_description(self, alias: str = DEFAULT_ALIAS) -> Optional[str]:
        """
        Get the proxy description for a specific alias.

        :param alias: str - Alias for the settings section. Defaults to DEFAULT_ALIAS.
        :return: Optional[str] - Proxy description if set, None otherwise
        """
        return self.get_setting_value("PROXY_DESCRIPTION", alias)

    def set_proxy_description(self, description: str, alias: str = DEFAULT_ALIAS):
        """
        Set the proxy description for a specific alias.

        :param description: str - Proxy description to set
        :param alias: str - Alias for the settings section. Defaults to DEFAULT_ALIAS.
        """
        self.set_setting_value("PROXY_DESCRIPTION", description, alias)

    def get_proxy_affinity(self, alias: str = DEFAULT_ALIAS) -> Optional[uuid.UUID]:
        """
        Get the proxy affinity for a specific alias.

        :param alias: str - Alias for the settings section. Defaults to DEFAULT_ALIAS.
        :return: Optional[uuid.UUID] - Proxy affinity if set, None otherwise
        """
        default_affinity = uuid.UUID(int=0)
        if not self.has_value("PROXY_AFFINITY", alias):
            return default_affinity
        affinity_str = self.get_setting_value("PROXY_AFFINITY", alias)
        return uuid.UUID(affinity_str) if affinity_str else default_affinity

    def set_proxy_affinity(self, affinity: uuid.UUID, alias: str = DEFAULT_ALIAS):
        """
        Set the proxy affinity for a specific alias.

        :param affinity: uuid.UUID - Proxy affinity to set
        :param alias: str - Alias for the settings section. Defaults to DEFAULT_ALIAS.
        """
        self.set_setting_value("PROXY_AFFINITY", str(affinity), alias)

    def get_setting_value(self, setting_key: str, alias: str):
        """
        Get the value of a specific setting for a specific alias.

        :param setting_key: str - Key of the setting to get
        :param alias: str - Alias for the settings section. Defaults to DEFAULT_ALIAS.
        """
        env_var_name = setting_key.upper()
        if os.getenv(env_var_name) and alias == self.DEFAULT_ALIAS:
            return os.getenv(env_var_name)
        else:
            return super().get_setting_value(setting_key, alias)
    
    def get_proxy_config(self, alias: str = DEFAULT_ALIAS) -> dict:
        """
        Get the complete proxy configuration for a specific alias.

        :param alias: str - Alias for the settings section. Defaults to DEFAULT_ALIAS.
        :return: dict - Dictionary containing proxy configuration
        """
        return {
            "id": str(self.get_proxy_id(alias)) if self.get_proxy_id(alias) else None,
            "name": self.get_proxy_name(alias),
            "description": self.get_proxy_description(alias),
            "affinity": str(self.get_proxy_affinity(alias)) if self.get_proxy_affinity(alias) else None
        }
