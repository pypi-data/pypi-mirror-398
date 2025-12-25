from enum import Enum


class GetFeaturesResponseFeaturesItem(str, Enum):
    TELEMETRY = "telemetry"
    INTERNALTELEMETRY = "internalTelemetry"
    TELEOP = "teleop"
    SSH = "ssh"
    CUSTOMEVENTS = "customEvents"
    TRIGGEREDEVENTS = "triggeredEvents"
    PORTFORWARDING = "portForwarding"
    COMMANDS = "commands"
    INTERVENTIONS = "interventions"
    ONDEMAND = "onDemand"
    APPCONFIG = "appConfig"
    BLOBSTORAGE = "blobStorage"
    EVENTS = "events"
    ANNOTATIONS = "annotations"
    OBSERVABILITY = "observability"
    DIAGNOSTICS = "diagnostics"
    ADVANCEDCONFIGURATION = "advancedConfiguration"
    DATAEXPORT = "dataExport"
    SHARE = "share"
    ADAPTERS = "adapters"
    S3EXPORT = "s3Export"
    FILESTORAGE = "fileStorage"
    ROLEVIEWER = "roleViewer"
    TEAMS = "teams"
    SCHEDULES = "schedules"
    TELEOP2_0 = "teleop2.0"
    BILLING = "billing"
    TASKSUMMARIES = "taskSummaries"

    def __str__(self) -> str:
        return str(self.value)
