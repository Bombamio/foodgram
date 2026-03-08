from django.conf import settings
from rest_framework.pagination import PageNumberPagination


class RecipePagination(PageNumberPagination):
    page_size = settings.PAGE_SIZE
    max_page_size = settings.MAX_PAGE_SIZE
    page_size_query_param = 'limit'
