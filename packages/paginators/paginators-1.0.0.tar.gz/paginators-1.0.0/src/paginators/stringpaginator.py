"""
Based on snippet 1364 by zain, posted 2009-03-10

This allows you to make two different alphabetical filters for a list of
objects, that is, browse by title.

These work with unicode, though an exception will currently be thrown if
any of the strings it is paginating on are blank.
"""
import unicodedata

from paginators import InvalidPage, EmptyPage, PageQueryStringMixin, DjangoPaginator, PageNotAnInteger


def issymbol(char):
    "Tests if the char is a symbol as defined by its unicode category"
    if not char:
        raise ValueError('No character to test')
    if unicodedata.category(char)[0] in ('L', 'N'):
        return False
    return True


class AbstractPaginator(object):
    """Base-class"""

    def _handle_non_alpha(self):
        numbers_page = LetterPage(self)
        symbols_page = LetterPage(self)
        for char in sorted(self._chunks):
            chunk = self._chunks[char]
            # combine numbers into a sublist
            if char.isdigit():
                numbers_page.add(chunk, char)
                del self._chunks[char]
                continue
            # combine symbols into a sublist
            if issymbol(char):
                symbols_page.add(chunk, char)
                del self._chunks[char]
                continue
        if numbers_page.count:
            self.pages.append(numbers_page)
        if symbols_page.count:
            self.pages.append(symbols_page)

    def __init__(self, object_list, on=None, request=None, allow_empty_first_page=True):
        self.object_list = object_list
        self.count = len(object_list)
        self.request = request
        self.allow_empty_first_page = allow_empty_first_page
        self.pages = []

        # chunk up the objects so we don't need to iterate over the whole list for each letter
        self._chunks = {}

        for obj in self.object_list:
            if on:
                obj_str = getattr(obj, on)
            else:
                obj_str = obj

            # problems wind up in their own chunk
            if not obj_str.strip():
                self._chunks.setdefault('', [].append(obj))
                continue

            char = obj_str[0].upper()

            self._chunks.setdefault(char, []).append(obj)

    def validate_number(self, number):
        "Validates the given 1-based page number."
        try:
            number = int(number)
        except ValueError:
            raise PageNotAnInteger('That page number is not an integer')
        if number < 1:
            raise EmptyPage('That page number is less than 1')
        if number > self.num_pages:
            if number == 1 and self.allow_empty_first_page:
                pass
            else:
                raise EmptyPage('That page contains no results')
        return number

    def page(self, number):
        """Returns a Page object for the given 1-based page number."""
        number = self.validate_number(number)
        if len(self.pages) == 0:
            return LetterPage(self)
        return self.pages[number-1]

    @property
    def num_pages(self):
        """Returns the total number of pages"""
        return len(self.pages)


class SingleLetterPaginator(AbstractPaginator):
    """SingleLetterPaginator makes one page per letter.

         A B C D E F G H I J K etc.

    SingleLetterPaginator works like Django's Paginator, except you only
    pass in a list of objects, and not how many objects you want per page.

    SingleLetterPaginator Arguments:
    --------------------------------

    object_list: A list, dictionary, QuerySet, or something similar.

    on: If you specified a QuerySet, this is the field it will
    paginate on. In the example below, we're paginating a list of
    Contact objects, but the Contact.email string is what will be
    used in filtering.
    """

    def __init__(self, object_list, on=None, request=None, *args, **kwargs):
        super(SingleLetterPaginator, self).__init__(object_list, on=on, request=request)
        # the process for assigning objects to each page

        for letter in sorted(self._chunks):
            # the items in object_list starting with this letter
            sub_list = self._chunks[letter]
            current_page = LetterPage(self)
            current_page.add(sub_list, letter)
            self.pages.append(current_page)


class CombinedLetterPaginator(AbstractPaginator):
    """CombinedLetterPaginator combines several letters on one page.

        A-G H-N O-Z

    See the entry in Yahoo's design pattern library for more info:

    https://web.archive.org/web/20090701094129/http://developer.yahoo.com/ypatterns/pattern.php?pattern=alphafilterlinks

    (originally:
    http://developer.yahoo.com/ypatterns/pattern.php?pattern=alphafilterlinks)

    This paginator works like Django's Paginator. You pass in a list of
    objects and how many you want per letter range ("page"). Then, it will
    dynamically generate the "pages" so that there are approximately
    per_page objects per page.

    By dynamically generating the letter ranges, you avoid having
    too many objects in some letter ranges and too few in some. If
    your list is heavy on one end of the letter range, there will be
    more pages for that range.

    It splits the pages on letter boundaries, so not all the pages
    will have exactly per_page objects. However, it will decide to
    overflow or underflow depending on which is closer to per_page.

    CombinedLetterPaginator Arguments:
    ----------------------------------

    object_list: A list, dictionary, QuerySet, or something similar.

    on: If you specified a QuerySet, this is the field it will
    paginate on. In the example below, we're paginating a list of
    Contact objects, but the Contact.email string is what will be
    used in filtering.

    per_page: How many items you want per page.

    Examples:
    ---------

        >>> paginator = CombinedLetterPaginator(Contacts.objects.all(), \
        ... on="email", per_page=10)

        >>> paginator.num_pages
        4
        >>> paginator.pages
        [A, B-R, S-T, U-Z]
        >>> paginator.count
        36

        >>> page = paginator.page(2)
        >>> page
        'B-R'
        >>> page.start_letter
        'B'
        >>> page.end_letter
        'R'
        >>> page.number
        2
        >>> page.count
        8

    In your view, you have something like:

        contact_list = Contacts.objects.all()
        paginator = CombinedLetterPaginator(contact_list, \
            on="first_name", per_page=25)

        try:
            page = int(request.GET.get('page', '1'))
        except ValueError:
            page = 1

        try:
            page = paginator.page(page)
        except (InvalidPage):
            page = paginator.page(paginator.num_pages)

        return render(request, 'list.html', {"page": page})

    In your template, have something like:

        {% for object in page.object_list %}
        ...
        {% endfor %}

        <div class="pagination">
            Browse by title:
            {% for p in page.paginator.pages %}

              {% ifequal p page %}
                  <span class="selected">{{ page }}</span>
              {% else %}
                  <a href="?page={{ page.number }}">
                      {{ page }}
                  </a>
              {% endifequal %}

            {% endfor %}
        </div>
    """

    def __init__(self, object_list, on=None, per_page=25, request=None):
        super(CombinedLetterPaginator, self).__init__(object_list, on=on, request=request)

        # Symbols and digits get their own pages
        self._handle_non_alpha()

        # the process for assigning objects to each page
        current_page = LetterPage(self)

        # the remaining chars are letters
        for letter in sorted(self._chunks):

            # the items in object_list starting with this letter
            sub_list = self._chunks[letter]

            new_page_count = len(sub_list) + current_page.count
            # first, check to see if sub_list will fit or it
            # needs to go onto a new page. if assigning this
            # list will cause the page to overflow... and an
            # underflow is closer to per_page than an
            # overflow... and the page isn't empty (which
            # means len(sub_list) > per_page)...
            if new_page_count > per_page and \
                    abs(per_page - current_page.count) < abs(per_page - new_page_count) and \
                    current_page.count > 0:
                # make a new page
                self.pages.append(current_page)
                current_page = LetterPage(self)

            current_page.add(sub_list, letter)

        # if we finished the for loop with a page that isn't empty, add it
        if current_page.count > 0:
            self.pages.append(current_page)


class LetterPage(PageQueryStringMixin):

    def __init__(self, paginator):
        self.paginator = paginator
        self.object_list = []
        self.letters = []

    @property
    def count(self):
        return len(self.object_list)

    @property
    def start_letter(self):
        if len(self.letters) > 0:
            self.letters.sort(key=str.upper)
            return self.letters[0]
        else: return None

    @property
    def end_letter(self):
        if len(self.letters) > 0:
            self.letters.sort(key=str.upper)
            return self.letters[-1]
        else: return None

    @property
    def number(self):
        return self.paginator.pages.index(self) + 1

    def add(self, new_list, letter=None):
        if len(new_list) > 0:
            self.object_list = self.object_list + new_list
        if letter:
            self.letters.append(letter)

    def __str__(self):
        if self.start_letter == self.end_letter:
            return self.start_letter
        else:
            if self.start_letter.isdigit():
                return '0-9'
            if issymbol(self.start_letter):
                return 'Symbols'
            return '%s-%s' % (self.start_letter, self.end_letter)
    __unicode__ = __str__

    @property
    def page_range(self):
        return list(range(1, len(self.letters) + 1))

    def has_next(self):
        return self.number < self.paginator.num_pages

    def has_previous(self):
        return self.number > 1

    def has_other_pages(self):
        return self.has_previous() or self.has_next()

    def next_page_number(self):
        return self.number + 1

    def previous_page_number(self):
        return self.number - 1
