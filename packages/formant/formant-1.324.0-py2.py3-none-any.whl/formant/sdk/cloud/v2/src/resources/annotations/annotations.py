
from formant.sdk.cloud.v2.src.resources.resources import Resources
from . import Annotation, AnnotationTemplate, AnnotationTemplateListResponse, Response, annotation_controller_post, annotation_template_controller_get_one, annotation_template_controller_list

class Annotations(Resources):

    def list_templates(self):
        'List all annotations'
        client = self._get_client()
        response: Response[AnnotationTemplateListResponse] = annotation_template_controller_list.sync_detailed(client=client)
        return response

    async def list_templates_async(self):
        'List all annotations'
        client = self._get_client()
        response: Response[AnnotationTemplateListResponse] = (await annotation_template_controller_list.asyncio_detailed(client=client))
        return response

    def get_template(self, id: str):
        'Get an annotation'
        client = self._get_client()
        response: Response[AnnotationTemplate] = annotation_template_controller_get_one.sync_detailed(client=client, id=id)
        return response

    async def get_template_async(self, id: str):
        'Get an annotation'
        client = self._get_client()
        response: Response[AnnotationTemplate] = (await annotation_template_controller_get_one.asyncio_detailed(client=client, id=id))
        return response

    def post(self, annotation: Annotation):
        'Creates an annotation'
        client = self._get_client()
        response: Response[Annotation] = annotation_controller_post.sync_detailed(client=client, json_body=annotation)
        return response

    async def post_async(self, annotation: Annotation):
        'Creates an annotation'
        client = self._get_client()
        response: Response[Annotation] = (await annotation_controller_post.asyncio_detailed(client=client, json_body=annotation))
        return response
