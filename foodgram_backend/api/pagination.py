from rest_framework.pagination import PageNumberPagination

from recipe.constants import PAGINATION_PAGE_SIZE


class Pagination(PageNumberPagination):
    """Пагинация."""

    page_size = PAGINATION_PAGE_SIZE
    page_size_query_param = 'limit'
