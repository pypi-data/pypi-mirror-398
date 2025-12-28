from rest_framework.renderers import JSONRenderer


class StandardResponseRenderer(JSONRenderer):
    """
    Custom JSON renderer that wraps all responses in a standard format.
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render `data` into JSON, wrapping it in a standard response format.
        """
        if renderer_context is None:
            return super().render(data, accepted_media_type, renderer_context)

        response = renderer_context.get('response')
        view = renderer_context.get('view')

        if response is None:
            return super().render(data, accepted_media_type, renderer_context)

        status_code = response.status_code
        is_success = status_code < 400

        # Don't wrap if data is already wrapped
        if isinstance(data, dict) and 'success' in data:
            return super().render(data, accepted_media_type, renderer_context)

        # دریافت پیام سفارشی از response یا view
        if hasattr(response, 'custom_message'):
            custom_message = response.custom_message
        elif hasattr(view, 'success_message') and is_success:
            custom_message = view.success_message
        elif hasattr(view, 'error_message') and not is_success:
            custom_message = view.error_message
        else:
            custom_message = "Operation completed successfully." if is_success else "An error occurred."

        if is_success:
            wrapped_data = {
                "success": True,
                "message": custom_message,
                "data": data,
                "error": None,
            }
        else:
            wrapped_data = {
                "success": False,
                "message": custom_message,
                "data": None,
                "error": data,
            }

        return super().render(wrapped_data, accepted_media_type, renderer_context)