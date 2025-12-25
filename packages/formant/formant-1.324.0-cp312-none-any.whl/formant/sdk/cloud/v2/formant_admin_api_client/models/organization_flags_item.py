from enum import Enum


class OrganizationFlagsItem(str, Enum):
    SETTINGS_ROLE = "settings.role"
    SETTINGS_USER = "settings.user"
    SETTINGS_DEVICE = "settings.device"
    SETTINGS_TEAM = "settings.team"
    SETTINGS_GROUP = "settings.group"
    SETTINGS_CONFIG_TEMPLATE = "settings.config_template"
    SETTINGS_EVENT = "settings.event"
    SETTINGS_VIEW = "settings.view"
    SETTINGS_COMMAND = "settings.command"
    SETTINGS_SCHEDULE = "settings.schedule"
    SETTINGS_ANNOTATION = "settings.annotation"
    SETTINGS_SHARE = "settings.share"
    SETTINGS_STREAM = "settings.stream"
    SETTINGS_TAG = "settings.tag"
    SETTINGS_INTEGRATION = "settings.integration"
    SETTINGS_FILE_STORAGE = "settings.file_storage"
    SETTINGS_ADAPTER = "settings.adapter"
    SETTINGS_MODULE = "settings.module"
    SETTINGS_ORGANIZATION = "settings.organization"

    def __str__(self) -> str:
        return str(self.value)
