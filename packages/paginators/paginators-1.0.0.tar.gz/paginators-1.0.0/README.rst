=================
django-paginators
=================

A library collecting various paginators and pagination tools for Django.

Not locked to a Django version, the code was first designed for Django < 1.0
and Python < 2.7. It no longer supports Python 2.

Import what you need or add it as an app to use the template tag.

paginators.Paginator
====================

A thin shim around ``django.core.paginator.Paginator`` adding some helpful
methods.

paginators.Page
===============

Used by ``paginators.Paginator``, a thin shim around
``django.core.paginator.Page`` adding some helpful methods.

paginators.namepaginator.NamePaginator
======================================

The first paginator paging on strings instead of numbers.

paginators.namepaginator.NamePage
=================================

The page-object used by ``paginators.namepaginator.NamePaginator``.

paginators.stringpaginator.SingleLetterPaginator
================================================

Page on a single letter instead of a number: for for instance dictionaries.

paginators.stringpaginator.CombinedLetterPaginator
==================================================

Combine several letters into a single page: for for instance dictionaries.

paginators.stringpaginator.LetterPage
=====================================

Used by ``paginators.stringpaginator.SingleLetterPaginator`` and
``paginators.stringpaginator.CombinedLetterPaginator``.

The equivalent of ``django.core.paginator.Page`` but for letters.

paginators.templates
====================

The default template used by the template tag.

paginators.templatetags.paginator.paginator
===========================================

A template tag falling back to using the template in ``paginators.templates``
that prettily renders a paginator block.
