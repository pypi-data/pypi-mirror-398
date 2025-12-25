from typing import Dict, Optional
import datetime
from dateutil.tz import tzutc
from .annotation_template import AnnotationTemplate


class Annotation:

    @classmethod
    def from_template(
        cls,
        annotation_template,  # type: AnnotationTemplate
        device_id,  # type: str
        note,  # type: str
        tags=None,  # type: Optional[Dict[str,str]]
        start_time=datetime.datetime.now(
            tz=tzutc()
        ),  # type: datetime.datetime
        end_time=None,  # type: Optional[datetime.datetime]
        duration=None,  # type:Optional[float]
    ):
        return cls(
            device_id,
            note,
            annotation_template.name,
            tags=tags,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            annotation_template_id=annotation_template.id
        )

    def __init__(
        self,
        device_id,  # type: str
        note,  # type: str
        message,  # type: str
        tags=None,  # type: Optional[Dict[str,str]]
        start_time=datetime.datetime.now(
            tz=tzutc()
        ),  # type: datetime.datetime
        end_time=None,  # type: Optional[datetime.datetime]
        duration=None,  # type:Optional[float]
        annotation_template_id=None,  # type: Optional[str]   
    ):
        self.device_id = device_id
        self.note = note
        self.message = message
        self.tags = tags if tags is not None else {}
        self.start_time = start_time
        self.end_time = end_time
        self.duration = duration
        self.annotation_template_id = annotation_template_id

    def set_start_time(
        self, start_time  # type: datetime.datetime
    ):
        self.start_time = start_time

    def set_duration(
        self, duration  # type: float
    ):
        self.duration = duration

    def set_end_time(
        self, end_time  # type: datetime.datetime
    ):
        self.end_time = end_time

    def set_tag(self, key, value):
        self.tags[key] = value

    def get_request_params(self):
        end_time = None
        if self.duration is not None:
            end_time = self.start_time + datetime.timedelta(minutes=self.duration)
        if self.end_time is not None:
            end_time = self.end_time
        return {
            "type": "annotation",
            "deviceId": self.device_id,
            "annotationTemplateId": self.annotation_template_id,
            "note": self.note,
            "message": self.message,
            "time": self.start_time.isoformat(),
            "endTime": end_time.isoformat(),
            "tags": self.tags,
        }
