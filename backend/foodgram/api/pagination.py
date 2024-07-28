from rest_framework.pagination import LimitOffsetPagination


class PageLimitPagination(LimitOffsetPagination):
    default_limit = 6
    limit_query_param = 'limit'
