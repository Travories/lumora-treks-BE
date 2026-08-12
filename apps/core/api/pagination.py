from rest_framework.pagination import LimitOffsetPagination


class LumoraPagination(LimitOffsetPagination):
    """Mirrors the Wagtail API shape: {meta: {total_count}, items: [...]}"""

    default_limit = 20
    max_limit = 200

    def get_paginated_response(self, data):
        from rest_framework.response import Response

        return Response(
            {
                "meta": {
                    "total_count": self.count,
                    "limit": self.limit,
                    "offset": self.offset,
                },
                "items": data,
            }
        )
