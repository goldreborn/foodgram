from rest_framework.pagination import LimitOffsetPagination


class PageLimitPagination(LimitOffsetPagination):
    default_limit = 6
