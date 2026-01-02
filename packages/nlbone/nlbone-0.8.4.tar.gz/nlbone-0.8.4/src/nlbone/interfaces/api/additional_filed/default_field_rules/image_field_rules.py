from nlbone.interfaces.api.additional_filed import FieldRule


def get_image(entity, file_service):
    image_id = entity.image_id
    if image_id:
        try:
            return file_service.get_file(image_id)
        except Exception:
            return None


IMAGE_FILED_RULE = FieldRule(default=True, name="image", loader=get_image)
