
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class FullLinkPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    def __init__(self, *args, **kwargs):
        """Allow view to override pagination settings"""
        super().__init__(*args, **kwargs)

    def paginate_queryset(self, queryset, request, view=None):
        """Override pagination settings from view if provided"""
        if view is not None:
            if hasattr(view, 'page_size'):
                self.page_size = view.page_size
            if hasattr(view, 'page_size_query_param'):
                self.page_size_query_param = view.page_size_query_param
            if hasattr(view, 'max_page_size'):
                self.max_page_size = view.max_page_size

        return super().paginate_queryset(queryset, request, view)

    def _build_full_url(self, page_number):
        """Build full URL for a specific page number"""
        request = self.request
        query_params = request.GET.copy()
        query_params["page"] = page_number
        return f"{request.build_absolute_uri(request.path)}?{query_params.urlencode()}"

    def get_paginated_response(self, data):
        """Return paginated response with full URLs"""
        current_page = self.page.number
        total_pages = self.page.paginator.num_pages

        first_link = self._build_full_url(1)
        last_link = self._build_full_url(total_pages)
        next_link = self.get_next_link()
        prev_link = self.get_previous_link()

        return Response({
            "count": self.page.paginator.count,
            "page": current_page,
            "pages": total_pages,
            "first": first_link,
            "last": last_link,
            "next": next_link,
            "previous": prev_link,
            "results": data
        })