from rest_framework.pagination import LimitOffsetPagination


class LumoraPagination(LimitOffsetPagination):
    """Mirrors the Wagtail API shape: {meta: {total_count}, items: [...]}"""

    default_limit = 20
    max_limit = 200

    def get_paginated_response(self, data, extra=None):
        from rest_framework.response import Response

        payload = {
            "meta": {
                "total_count": self.count,
                "limit": self.limit,
                "offset": self.offset,
            },
            "items": data,
        }
        if extra:
            payload.update(extra)
        return Response(payload)
