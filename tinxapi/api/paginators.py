from rest_framework.pagination import LimitOffsetPagination


class RestrictedPagination(LimitOffsetPagination):
  default_limit = 10
  max_limit = 50