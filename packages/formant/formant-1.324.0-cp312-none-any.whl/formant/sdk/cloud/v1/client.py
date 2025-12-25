from typing import Optional, List, Dict  # noqa: F401
import ntpath
import os
import requests
import sys
import time
import datetime
from dateutil.tz import tzutc
import copy

FORMANT_REQUEST_ON_DEMAND_DATA_COMMAND_NAME = "formant.demand_data"


def get_current_isodate():
    """Gets current timestamp in ISO format.

    :return: Timestamp in ISO format.
    :rtype: ``datetime.datetime.now.isoformat()``
    """    
    return datetime.datetime.now(tz=tzutc()).isoformat()


def get_timestamp_str(
    dt,  # type: datetime.datetime
):
    """Converts ``datetime.datetime`` timestamp to string.

    :param dt: Timestamp to return as string.
    :type dt: ``datetime.datetime``
    :return: Timestamp string.
    :rtype: ``str``
    """    
    return str(int(dt.timestamp()))


def timestamp_to_datetime_utc(timestamp):
    """Converts timestamp to ISO UTC datetime string.

    :param timestamp: Timestamp to convert.
    :type timestamp: ``str``
    :return: ISO UTC formatted datetime.
    :rtype: ``str``
    """    
    try:
        my_time = datetime.datetime.fromtimestamp(
            float(timestamp),
            datetime.timezone.utc
        ).isoformat()
    except (ValueError, TypeError) as e:
        my_time = timestamp

    return my_time


class Client:
    """
    A client for interacting with the Formant Cloud. There are methods for:

    - Ingesting telemetry datapoints for device(s)

    - Query telemetry datapoints

    - Query stream(s) last known value

    - Create intervention requests

    - Create intervention responses

    To authenticate the Cloud SDK v1 client, set the following
    environment variables with valid Formant credentials:

    - ``FORMANT_EMAIL``

    - ``FORMANT_PASSWORD``

    .. admonition:: Return values

        All methods of the Cloud SDK v1 client return a Dictionary object
        which can be parsed for response values. 

    """

    def __init__(
        self,
        admin_api="https://api.formant.io/v1/admin",
        ingest_api="https://api.formant.io/v1/ingest",
        query_api="https://api.formant.io/v1/queries",
    ):
        self._admin_api = admin_api
        self._ingest_api = ingest_api
        self._query_api = query_api

        self._email = os.getenv("FORMANT_EMAIL")
        self._password = os.getenv("FORMANT_PASSWORD")
        if self._email is None:
            raise ValueError("Missing FORMANT_EMAIL environment variable")
        if self._password is None:
            raise ValueError("Missing FORMANT_PASSWORD environment variable")

        self._headers = {
            "Content-Type": "application/json",
            "App-ID": "formant/python-cloud-sdk",
        }

        self._token = None
        self._token_expiry = 0
        self._organization_id = None
        self._user_id = None

    def get_user_id(self):
        """Gets self user ID.

        :return: ID of this user.
        :rtype: ``str``
        """        
        if self._user_id is None:
            self._authenticate()
        return self._user_id

    def get_organization_id(self):
        """Gets this organization ID.

        :return: Organization ID.
        :rtype: ``str``
        """

        if self._organization_id is None:
            self._authenticate()
        return self._organization_id

    def ingest(self, params):
        """Ingests data to Formant.
        
        .. note:: 

            Administrator credentials required.

        .. note::
            For a complete syntax reference for the ``points`` parameter,
            see `our ingest example <https://github.com/FormantIO/formant/blob/master/examples/python/formant_module/cloud/ingest.py>`__.

        .. code-block:: python

            from formant.sdk.cloud.v1 import Client

            fclient = Client()

            params = { 
                "items": {[
                    "deviceId": "ced176ab-f223-4466-b958-ff8d35261529",
                    "name": "engine_temp",
                    "type": "numeric",
                    "tags": {"location":"sf"},
                    "points": [...],
                ]}
            }

            response = fclient.ingest(params)
        """

        def call(token):
            headers = self._headers.copy()
            headers["Authorization"] = "Bearer %s" % token
            response = requests.post(
                "%s/batch" % self._ingest_api, headers=headers, json=params
            )
            response.raise_for_status()

        self._authenticate_request(call)

    def get_organization(
        self,
    ):
        """Get this organization ID.
        """    
        def call(token):
            headers = self._headers.copy()
            headers["Authorization"] = "Bearer %s" % token
            response = requests.get(
                "%s/organizations/%s" % (self._admin_api, self.get_organization_id()),
                headers=headers,
            )
            response.raise_for_status()
            return response.json()

        return self._authenticate_request(call)

    def query(self, params):
        """Queries datapoints from the Formant cloud. For more information, see 
        `Cloud SDK: Querying telemetry data <https://docs.formant.io/reference/querying-telemetry-data>`__.

        .. code-block:: python

            from formant.sdk.cloud.v1 import Client

            fclient = Client()
                
            params = {
                start: "2021-01-01T01:00:00.000Z",
                end: "2021-01-01T02:00:00.000Z",
                deviceIds: ["99e8ee37-0a27-4a11-bba2-521facabefa3"],
                names: ["engine_temp"],
                types: ["numeric"],
                tags: {"location":["sf","la"]},
                notNames: ["speed"],
            }

            response = fclient.query(params)
        """

        def call(token):
            headers = self._headers.copy()
            headers["Authorization"] = "Bearer %s" % token
            # enable pagination by default
            # TODO: support for aggregate queries
            query = copy.deepcopy(params)
            nextToken = None if len(query.get("aggregate", "")) > 0 else "true"
            result = {"items": []}
            while True:
                if nextToken is not None:
                    query["next"] = nextToken
                response = requests.post(
                    "%s/queries" % self._query_api, headers=headers, json=query
                )
                response.raise_for_status()
                parsed = response.json()
                nextToken = parsed.get("next")
                result["items"] += parsed["items"]
                if nextToken is None:
                    break
            return result

        return self._authenticate_request(call)

    def query_devices(self, params):
        """Query devices in this organization. The full list of query parameters
        can be found here: `Device QUERY <https://docs.formant.io/reference/devicecontrollerquery>`__.

        :param params: Query parameters.
        :type params: object
        
        .. code-block:: python

            from formant.sdk.cloud.v1 import Client

            fclient = Client()

            params = {
                name: "model00.001",
                tags: {"location":["sf", "la"]},
            }

            response = fclient.query_devices(params)
        """

        def call(token):
            headers = self._headers.copy()
            headers["Authorization"] = "Bearer %s" % token
            response = requests.post(
                "%s/devices/query" % self._admin_api, headers=headers, json=params
            )
            response.raise_for_status()
            return response.json()

        return self._authenticate_request(call)

    def patch_device(self, device_id, params):
        """Update device configuration. Full parameters can be found here: 
        `Device PATCH <https://docs.formant.io/reference/devicecontrollerpatch>`__.

        :param device_id: ID of the device to update.
        :type device_id: ``str``
        :param params: Device configuration parameters to update.

        .. code-block:: python

            from formant.sdk.cloud.v1 import Client

            fclient = Client()

            device_id = 'abc-123'
            params = {
                "desiredConfiguration": 43
            }

            response = fclient.patch_device(device_id, params)
        """

        def call(token):
            headers = self._headers.copy()
            headers["Authorization"] = "Bearer %s" % token
            response = requests.patch(
                "%s/devices/%s" % (self._admin_api, device_id),
                headers=headers,
                json=params,
            )
            response.raise_for_status()
            return response.json()

        return self._authenticate_request(call)

    def query_task_summary_formats(self):
        """
        Get all task summary formants
        """
        def call(token):
            headers = self._headers.copy()
            headers["Authorization"] = "Bearer %s" % token
            response = requests.get(
                "%s/task-summary-formats/" % (self._admin_api),
                headers=headers,
            )
            response.raise_for_status()
            return response.json()

        return self._authenticate_request(call)

    def query_task_summaries(self, params):
        """
        Get all task summaries
        """

        def call(token):
            headers = self._headers.copy()
            headers["Authorization"] = "Bearer %s" % token
            params["eventTypes"] = ["task-summary"]
            response = requests.post(
                "%s/events/query" % self._admin_api,
                headers=headers,
                json=params,
            )
            response.raise_for_status()
            return response.json()

        return self._authenticate_request(call)

    def upload_task_summary_format(self, task_summary_format):
        """
        Upload a task summary format.

        Task summary format definition can be found here: `Task summary format POST <https://docs.formant.io/reference/tasksummaryformatcontrollerpost>`__.
        """

        def call(token):
            headers = self._headers.copy()
            headers["Authorization"] = "Bearer %s" % token
            response = requests.post(
                "%s/task-summary-formats/" % self._admin_api,
                headers=headers,
                json=task_summary_format,
            )
            response.raise_for_status()
            return response.json()

        return self._authenticate_request(call)

    def upload_task_summary(
        self,
        task_summary_format_id,
        report,
        device_id,
        tags=None,
        message=None,
    ):
        """
        Upload a task summary.

        Task summary definition can be found here: `Task summary POST <https://docs.formant.io/reference/tasksummarycontrollerpost>`__.
        """

        def call(token):
            # Try to get start and end time from report
            if "start_time" in report:
                start_time = report["start_time"]
            elif "startTime" in report:
                start_time = report["startTime"]
            else:
                start_time = get_current_isodate()
            if "end_time" in report:
                end_time = report["end_time"]
            elif "startTime" in report:
                end_time = report["endTime"]
            else:
                end_time = get_current_isodate()
            start_time = timestamp_to_datetime_utc(start_time)
            end_time = timestamp_to_datetime_utc(end_time)
            time_now = get_current_isodate()

            # Task summary API doesn't accept None values
            for key in report:
                value = report[key]
                if value is None:
                    raise ValueError("Missing value for key: %s" % key)

            task_summary = {
                "taskSummaryFormatId": task_summary_format_id,
                "report": report,
                "taskId": str(report["id"]),
                "generatedAt": time_now,
                "time": start_time,
                "endTime": end_time,
                "message": message,
                "deviceId": device_id,
                "tags": tags
            }

            headers = self._headers.copy()
            headers["Authorization"] = "Bearer %s" % token
            response = requests.post(
                "%s/task-summaries/" % self._admin_api,
                headers=headers,
                json=task_summary
            )
            response.raise_for_status()
            return response.json()

        return self._authenticate_request(call)

    def query_stream_current_value(self, params):
        """Get current value for streams which match query parameters.
        Full parameters can be found here: `Stream current value QUERY <https://docs.formant.io/reference/streamcurrentvaluecontrollerquery>`__

        .. code-block:: python

            from formant.sdk.cloud.v1 import Client

            fclient = Client()

            params = {
                start: "2021-01-01T01:00:00.000Z",
                end: "2021-01-01T02:00:00.000Z",
                deviceIds: ["99e8ee37-0a27-4a11-bba2-521facabefa3"],
                names: ["engine_temp"],
                types: ["numeric"],
                tags: {"location":["sf","la"]},
                notNames: ["speed"],
            }

            response = fclient.query_stream_current_value(params)
        """

        def call(token):
            headers = self._headers.copy()
            headers["Authorization"] = "Bearer %s" % token
            response = requests.post(
                "%s/stream-current-value" % self._query_api,
                headers=headers,
                json=params,
            )
            response.raise_for_status()
            return response.json()

        return self._authenticate_request(call)

    def upload_file(self, params):
        """
        Upload a file to the Formant cloud.

        .. code-block:: python

            from formant.sdk.cloud.v1 import Client

            fclient = Client()

            params = {
                path: "/tmp/model.dat"
            }

            response = fclient.upload_file(params)
        """

        file_name = ntpath.basename(params["path"])
        byte_size = os.path.getsize(params["path"])
        if not (byte_size > 0):
            raise ValueError("File is empty")

        def begin_upload(token):
            headers = self._headers.copy()
            headers["Authorization"] = "Bearer %s" % token
            response = requests.post(
                "%s/files/begin-upload" % self._admin_api,
                headers=headers,
                json={"fileName": file_name, "fileSize": byte_size},
            )
            response.raise_for_status()
            return response.json()

        begin_result = self._authenticate_request(begin_upload)
        part_size = begin_result["partSize"]

        etags = []
        part_index = 0
        with open(params["path"], "rb") as file_obj:
            for part_url in begin_result["partUrls"]:
                file_obj.seek(part_index * part_size)
                part_index = part_index + 1
                data = file_obj.read(part_size)
                response = requests.put(part_url, data=data)
                etags.append(response.headers["etag"])

        def complete_upload(token):
            headers = self._headers.copy()
            headers["Authorization"] = "Bearer %s" % token
            response = requests.post(
                "%s/files/complete-upload" % self._admin_api,
                headers=headers,
                json={
                    "fileId": begin_result["fileId"],
                    "uploadId": begin_result["uploadId"],
                    "eTags": etags,
                },
            )
            response.raise_for_status()

        self._authenticate_request(complete_upload)

        return {
            "file_id": begin_result["fileId"],
        }

    def create_command(self, params):
        """
        Create a command. Full parameters can be found here: 
        `Command template POST <https://docs.formant.io/reference/commandtemplatecontrollerpost>`__.

        .. code-block:: python

            from formant.sdk.cloud.v1 import Client

            fclient = Client()
            
            params = {
                deviceId: "abc-123"
                command: "return_to_charge_station"
                parameter: {
                    "scrubberTime": "2014-11-03T19:38:34.203Z",
                    "value": "A-2",
                    "files": [{
                        "id": "def-456",
                        "name": "optional_name1"
                    }]
                },
            }

            response = fclient.create_command(params)
        """

        def call(token):
            headers = self._headers.copy()
            headers["Authorization"] = "Bearer %s" % token
            response = requests.post(
                "%s/commands" % self._admin_api,
                headers=headers,
                json=params,
            )
            response.raise_for_status()
            return response.json()

        return self._authenticate_request(call)

    def demand_device_data(
        self,
        device_id,  # type: str
        start,  # type: datetime.datetime
        end,  # type: datetime.datetime
    ):
        params = {
            "deviceId": device_id,
            "command": FORMANT_REQUEST_ON_DEMAND_DATA_COMMAND_NAME,
            "organizationId": self.get_organization_id(),
            "parameter": {
                "meta": {
                    "start": get_timestamp_str(start),
                    "end": get_timestamp_str(end),
                },
                "scrubberTime": get_current_isodate(),
            },
        }
        return self.create_command(params)

    def query_commands(self, params):
        """
        Get undelivered commands by device ID.

        .. code-block:: python

            from formant.sdk.cloud.v1 import Client

            fclient = Client()

            params = {
            deviceId: "abc-123",
            }

            response = fclient.query_commands(params)
        """

        def call(token):
            headers = self._headers.copy()
            headers["Authorization"] = "Bearer %s" % token
            response = requests.post(
                "%s/commands/query" % self._admin_api,
                headers=headers,
                json=params,
            )
            response.raise_for_status()
            return response.json()

        return self._authenticate_request(call)

    def query_count(
        self,
        start,  # type: datetime.datetime
        end,  # type: datetime.date
        type,  # type: str
    ):
        def call(token):
            params = {
                "start": start.isoformat(),
                "end": end.isoformat(),
                "type": type,
                "organizationId": self.get_organization_id(),
            }
            headers = self._headers.copy()
            headers["Authorization"] = "Bearer %s" % token
            response = requests.post(
                "%s/counts/history" % self._query_api,
                headers=headers,
                json=params,
            )
            response.raise_for_status()
            return response.json()

        return self._authenticate_request(call)

    def active_devices(
        self,
        start,  # type: datetime.datetime
        end,  # type: datetime.datetime
    ):
        def call(token):
            params = {
                "start": start.isoformat(),
                "end": end.isoformat(),
                "type": "default",
                "organizationId": self.get_organization_id(),
            }
            headers = self._headers.copy()
            headers["Authorization"] = "Bearer %s" % token
            response = requests.post(
                "%s/counts/active-devices" % self._query_api,
                headers=headers,
                json=params,
            )
            response.raise_for_status()
            return response.json()

        return self._authenticate_request(call)

    def create_intervention_response(self, params):
        """Creates a response to an intervention request. Full parameters can be found here:
        `Intervention response POST <https://docs.formant.io/reference/interventionresponsecontrollerpost>`__.

        :param params: Intervention response parameters.

        .. code-block:: python

            from formant.sdk.cloud.v1 import Client

            fclient = Client()

            params = {
            "interventionId": "518e24fc-64ef-47bb-be5e-036a97aeafaa",
            "interventionType": "teleop",
            "data": {
                "state": "success",
                "notes": "looks good!"
                }
            }

            response = fclient.create_intervention_response(params)
        """

        def call(token):
            headers = self._headers.copy()
            headers["Authorization"] = "Bearer %s" % token
            response = requests.post(
                "%s/intervention-responses" % self._admin_api,
                headers=headers,
                json=params,
            )
            return response.json()

        return self._authenticate_request(call)

    def create_intervention_request(self, params):
        """Create an intervention request. Full parameters can be found here: 
        `Intervention request POST <https://docs.formant.io/reference/interventionrequestcontrollerpost>`__.

        :param params: Intervention request parameters.

        .. code-block:: python

            from formant.sdk.cloud.v1 import Client

            fclient = Client()

            params = {
                "message": "A teleop for a customer is requested",
                "interventionType": "teleop",
                "time": "2022-02-17T11:41:33.389-08:00",
                "deviceId": "b306de84-33ca-4917-9218-f686730e24e0",
                "tags": {},
                "data": {
                    "instruction": "Look at the users item on the table"
                }
            }

            response = fclient.create_intervention_request(params)
        """

        def call(token):
            headers = self._headers.copy()
            headers["Authorization"] = "Bearer %s" % token
            response = requests.post(
                "%s/intervention-requests" % self._admin_api,
                headers=headers,
                json=params,
            )
            return response.json()

        return self._authenticate_request(call)

    def create_adapter(self, params):
        """Create an adapter in your organization. Full parameters can be found here:
        `Adapter POST <https://docs.formant.io/reference/adaptercontrollerpost>`__.

        .. code-block:: python

            from formant.sdk.cloud.v1 import Client

            fclient = Client()

            params = {
                "execCommand": "./start.sh",
                "path": "/tmp/model.dat"
                "name": "adapters_name"
            }

            response = fclient.create_adapter(params)
        """

        def call(token):
            file_id = self.upload_file(params={"path": params["path"]})
            params["fileId"] = file_id["file_id"]
            del params["path"]
            headers = self._headers.copy()
            headers["Authorization"] = "Bearer %s" % token
            response = requests.post(
                "%s/adapters" % self._admin_api,
                headers=headers,
                json=params,
            )
            return response.json()

        return self._authenticate_request(call)

    def get_device(self, device_id):
        def call(token):
            headers = self._headers.copy()
            headers["Authorization"] = "Bearer %s" % token
            response = requests.get(
                "%s/devices/%s" % (self._admin_api, device_id), headers=headers
            )
            response.raise_for_status()
            return response.json()

        return self._authenticate_request(call)

    def get_device_configuration(self, device_id, desired_configuration_version):
        def call(token):
            headers = self._headers.copy()
            headers["Authorization"] = "Bearer %s" % token
            response = requests.get(
                "%s/devices/%s/configurations/%s"
                % (self._admin_api, device_id, desired_configuration_version),
                headers=headers,
            )
            response.raise_for_status()
            return response.json()

        return self._authenticate_request(call)

    def post_device_configuration(self, device_id, params):
        """Post a device configuration.

        .. code-block:: python

            from formant.sdk.cloud.v1 import Client

            fclient = Client()

            device_id = 'abc-123'
            params = {
                "document": {
                    adapter: [{
                        id: "84f98678-5f18-478d-aed8-631d9ea043a9",
                        name: "ROS-diagnostics",
                        "execCommand": "./start.sh"
                        }],
                    tags: {},
                    telemetry: {
                        streams: []
                    }
                }

            response = fclient.post_device_configuration(device_id, params)
        """

        def call(token):
            headers = self._headers.copy()
            headers["Authorization"] = "Bearer %s" % token
            response = requests.post(
                "%s/devices/%s/configurations" % (self._admin_api, device_id),
                headers=headers,
                json=params,
            )
            return response.json()

        return self._authenticate_request(call)

    def get_views(self):
        def call(token):
            headers = self._headers.copy()
            headers["Authorization"] = "Bearer %s" % token
            response = requests.get(
                "%s/views/" % self._admin_api,
                headers=headers,
            )
            return response.json()

        return self._authenticate_request(call)

    def get_view(self, view_id):
        def call(token):
            headers = self._headers.copy()
            headers["Authorization"] = "Bearer %s" % token
            response = requests.get(
                "%s/views/%s" % (self._admin_api, view_id),
                headers=headers,
            )
            return response.json()

        return self._authenticate_request(call)

    def patch_view(self, view_id, params):
        def call(token):
            headers = self._headers.copy()
            headers["Authorization"] = "Bearer %s" % token
            response = requests.patch(
                "%s/views/%s" % (self._admin_api, view_id),
                headers=headers,
                json=params,
            )
            return response.json()

        return self._authenticate_request(call)

    def get_annotation_templates(self):
        """Gets all annotation templates in this organization.
        """        

        def call(token):
            headers = self._headers.copy()
            headers["Authorization"] = "Bearer %s" % token
            response = requests.get(
                "%s/annotation-templates/" % self._admin_api,
                headers=headers,
            )
            return response.json()

        return self._authenticate_request(call)

    def post_annotation(self, params):
        def call(token):
            self._add_user_id_to_params(params)
            self._add_organization_id_to_params(params)
            params_stripped = _strip_none_values(params)
            headers = self._headers.copy()
            headers["Authorization"] = "Bearer %s" % token
            response = requests.post(
                "%s/annotations/" % (self._admin_api),
                headers=headers,
                json=params_stripped,
            )
            return response.json()

        return self._authenticate_request(call)

    def query_events(self, params):
        def call(token):
            headers = self._headers.copy()
            headers["Authorization"] = "Bearer %s" % token
            result = {"items": []}
            current_offset = 0
            while True:
                params["offset"] = current_offset
                response = requests.post(
                    "%s/events/query" % (self._admin_api),
                    headers=headers,
                    json=params,
                )
                response.raise_for_status()
                parsed = response.json()
                result["items"] += parsed["items"]
                current_offset += len(parsed["items"])
                if len(parsed["items"]) != 10000:
                    break
            return result

        return self._authenticate_request(call)

    def get_streams(self):
        def call(token):
            headers = self._headers.copy()
            headers["Authorization"] = "Bearer %s" % token
            response = requests.get(
                "%s/streams/" % self._admin_api,
                headers=headers,
            )
            return response.json()

        return self._authenticate_request(call)

    def delete_stream(self, stream_id):
        def call(token):
            headers = self._headers.copy()
            headers["Authorization"] = "Bearer %s" % token
            response = requests.delete(
                "%s/streams/%s" % (self._admin_api, stream_id), headers=headers
            )
            response.raise_for_status()

        return self._authenticate_request(call)

    def query_annotations(
        self,
        start_time=None,  # type: Optional[datetime.datetime]
        device_ids=None,  # type: Optional[List[str]]
        tags=None,  # type: Optional[Dict[str,List[str]]]
        annotation_template_ids=None,  # type: Optional[List[str]]
        message=None,  # type:str
        keyword=None,  # type: str
        end_time=None,  # type: Optional[datetime.datetime]
        params=None,  # type: Dict
    ):
        params = params if params is not None else {}

        params["tags"] = tags
        if start_time is not None:
            params["start"] = start_time.isoformat()
            if end_time is None:
                end_time = datetime.datetime.now(tz=tzutc())
        if end_time is not None:
            params["end"] = end_time.isoformat()
        params["deviceIds"] = device_ids
        params["annotationTemplateIds"] = annotation_template_ids
        params["message"] = message
        params["keyword"] = keyword
        params["eventTypes"] = ["annotation"]

        params_stripped = _strip_none_values(params)
        return self.query_events(params_stripped)

    def _add_user_id_to_params(self, params):
        params["userId"] = self.get_user_id()

    def _add_organization_id_to_params(self, params):
        params["organizationId"] = self.get_organization_id()

    def _authenticate(self):
        payload = {
            "email": self._email,
            "password": self._password,
            "tokenExpirationSeconds": 3600,
        }
        response = requests.post(
            "%s/auth/login" % self._admin_api,
            headers=self._headers,
            json=payload,
        )
        response.raise_for_status()
        result = response.json()
        if "authentication" not in result:
            raise ValueError("Authentication failed")
        self._token_expiry = int(time.time()) + 3530
        self._token = result["authentication"]["accessToken"]
        self._organization_id = result["authentication"]["organizationId"]
        self._user_id = result["authentication"]["userId"]
        self._headers["Org-ID"] = self._organization_id
        self._headers["User-ID"] = self._user_id

    def _authenticate_request(self, call):
        if self._token is None or self._token_expiry < int(time.time()):
            self._authenticate()
        try:
            return call(self._token)
        except requests.exceptions.HTTPError as error:
            if error.response.status_code == 401:
                self._authenticate()
                try:
                    return call(self._token)
                except requests.exceptions.HTTPError as error:
                    sys.stderr.write("%s\n" % error.response.text)
                    raise error
            else:
                sys.stderr.write("%s\n" % error.response.text)
                raise error

    def create_device(
        self,
        device_name,  # type: str
        publicKey="",  # type: str
        tags=None,  # type: Optional[Dict[str,List[str]]]
        params=None,  # type: Dict
    ):
        """Creates a new device.

        :param device_name: Device name.
        :type device_name: ``str``
        """    
        params = params if params is not None else {}
        params["tags"] = tags
        params["name"] = device_name
        params["publicKey"] = publicKey
        params["enabled"] = True
        params_stripped = _strip_none_values(params)

        def call(token):
            headers = self._headers.copy()
            headers["Authorization"] = "Bearer %s" % token
            response = requests.post(
                "%s/devices" % (self._admin_api),
                headers=headers,
                json=params_stripped,
            )
            response.raise_for_status()
            return response.json()

        return self._authenticate_request(call)

    def generate_provisioning_token(
        self,
        id,  # type: str
        params=None,  # type: Dict
    ):
        """Generates a provisioning token for a device.

        :param id: ID of the device to provision.
        :type id: ``str``
        """    
        params = params if params is not None else {}
        params["id"] = id

        def call(token):
            headers = self._headers.copy()
            headers["Authorization"] = "Bearer %s" % token
            response = requests.post(
                "%s/devices/%s/provisioning-token" % (self._admin_api, id),
                headers=headers,
                json=params,
            )
            response.raise_for_status()
            return response.json()

        return self._authenticate_request(call)

    def provision_device(
        self,
        provisioningToken,  # type: str
        publicKey,  # type: str
        params=None,  # type: Dict
    ):
        """Provision a device given an ID and a provisioning token.

        :param provisioningToken: Provisioning token from ``generate_provisioning_token``.
        :type provisioningToken: ``str``
        """

        params = params if params is not None else {}
        params["provisioningToken"] = provisioningToken
        params["publicKey"] = publicKey
        params_stripped = _strip_none_values(params)

        def call(token):
            headers = self._headers.copy()
            headers["Authorization"] = "Bearer %s" % token
            response = requests.post(
                "%s/devices/provision" % (self._admin_api),
                headers=headers,
                json=params_stripped,
            )
            response.raise_for_status()
            return response.json()

        return self._authenticate_request(call)


def _strip_none_values(dict):
    return {k: v for k, v in dict.items() if v is not None}
