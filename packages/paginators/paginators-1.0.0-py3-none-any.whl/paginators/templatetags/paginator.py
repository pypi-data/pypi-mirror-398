"""
Snippet 1388 by myself, posted on 2009-03-21

This is a Paginator Tag for 1.x. Since the context is less
overfull, the template, paginator.html, needs more logic.

Put the tag in your templatetags and the template at the root of
a template-directory.

The tag will work out of the box in a generic view, other views
must provide is_paginated set to True, page_obj, and paginator.
You can get the object_list from the page_obj:
page_obj.object_list. See the pagination documentation. 

Example template:
-----------------

    {% if is_paginated %}
    <div class="pagination">
        <span>
            {% ifnotequal page_obj.first page_obj.number %}
            <b><a href="?page={{ page_obj.first }}">|&lt;</a></b>
            {% endifnotequal %}
            {% if page_obj.has_previous %}
            <b><a href="?page={{ page_obj.previous_page_number }}">&lt;</a></b>
            {% endif %}
            {% for p in page_obj.paginator.pages %}
            {% ifequal p page_obj %}
            <b class="selected">{{ page_obj }}</b>
            {% else %}
            <b><a href="?page={{ p.number }}">{{ p }}</a></b>
            {% endifequal %}
            {% endfor %}
            {% if page_obj.has_next %}
            <b><a href="?page={{ page_obj.next_page_number }}">&gt;</a></b>
            {% endif %}
            {% ifnotequal page_obj.last page_obj.number %}
            <b><a href="?page={{ page_obj.last }}">&gt;|</a></b>
            {% endifnotequal %}
        </span>
    </div>
    {% endif %}
"""

from django import template

register = template.Library()


@register.inclusion_tag('paginators/paginator.html', takes_context=True)
def paginator(context):
    return {
            'page_obj': context['page_obj'],
            'paginator': context['paginator'],
            'is_paginated': context['is_paginated'],
            'object_list': context['object_list'],
            }
