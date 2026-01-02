"Some missing paginators for Django"

from django.core.paginator import Paginator as DjangoPaginator
from django.core.paginator import Page as DjangoPage
from django.core.paginator import InvalidPage, EmptyPage
from django.core.paginator import PageNotAnInteger

__version__ = "1.0.0"

class PageQueryStringMixin(object):

    def first(self):
        return 1

    def last(self):
        return self.paginator.num_pages

    # From ticket #10941: http://code.djangoproject.com/ticket/10941
    def _other_page_querystring(self, page_number):
        """
        Returns a query string for the given page, preserving any
        GET parameters present.

        """
        try:
            querydict = self.paginator.request.GET.copy()
            querydict['page'] = page_number
            querystring = querydict.urlencode()
        except AttributeError:
            querystring = 'page=%s' % page_number
        return querystring

    def number_querystring(self):
        return self._other_page_querystring(self.number)

    def next_page_querystring(self):
        return self._other_page_querystring(self.next_page_number())

    def previous_page_querystring(self):
        return self._other_page_querystring(self.previous_page_number())

    def first_querystring(self):
        return self._other_page_querystring(self.first())

    def last_querystring(self):
        return self._other_page_querystring(self.last())


class Paginator(DjangoPaginator):

    def __init__(self, object_list, request, per_page=20, orphans=0, allow_empty_first_page=True):
        super(Paginator, self).__init__(object_list, per_page, orphans=orphans, allow_empty_first_page=allow_empty_first_page)
        self.per_page = int(self.per_page)
        self.request = request

    def _get_bottom_top(self, number):
        number = int(self.validate_number(number))
        bottom = (number - 1) * self.per_page
        top = bottom + self.per_page
        if top + self.orphans >= self.count:
            top = self.count
        return bottom, top

    def _get_slice(self, number):
        bottom, top = self._get_bottom_top(number)
        return self.object_list[bottom:top]

    def page(self, number):
        "Returns a Page object for the given 1-based page number."
        #bottom, top = self._get_bottom_top(number)
        return Page(self._get_slice(number), number, self)

    @property
    def pages(self):
        return [Page(self._get_slice(pagenum), pagenum, self) for pagenum in self.page_range]


class Page(DjangoPage, PageQueryStringMixin):

    def __str__(self):
        return str(self.number)

    def __repr__(self):
        return str(self.number)
