# -*- coding: utf-8 -*-
from django.contrib.admin.widgets import AdminSplitDateTime, AdminDateWidget, AdminTimeWidget
from django import forms
from django.conf import settings
from django.templatetags.static import static
from django.forms.utils import to_current_timezone
from django.utils.html import format_html
from jdatetime import GregorianToJalali

try:
    from django.utils.translation import gettext as _  
except ImportError:
    from django.utils.translation import ugettext as _ 


class AdminJalaliDateWidget(AdminDateWidget):
    @property
    def media(self):
        js = settings.JALALI_DATE_DEFAULTS['Static']['js']
        css = settings.JALALI_DATE_DEFAULTS['Static']['css']
        return forms.Media(js=[static(path) for path in js], css=css)

    def __init__(self, attrs=None, format=None):
        final_attrs = {
            'class': 'jalali_date-date border border-base-200 bg-white font-medium min-w-20 placeholder-base-400 rounded-default shadow-xs text-font-default-light text-sm focus:outline-2 focus:-outline-offset-2 focus:outline-primary-600 group-[.errors]:border-red-600 focus:group-[.errors]:outline-red-600 dark:bg-base-900 dark:border-base-700 dark:text-font-default-dark dark:group-[.errors]:border-red-500 dark:focus:group-[.errors]:outline-red-500 dark:scheme-dark group-[.primary]:border-transparent disabled:!bg-base-50 dark:disabled:!bg-base-800 px-3 py-2 w-full min-w-52',
            'data-jdp': {},
            'data-jdp-only-date': {}
        }
        if attrs is not None:
            final_attrs.update(attrs)
        super(AdminJalaliDateWidget, self).__init__(attrs=final_attrs, format=format)


class AdminTimeWidgetStyled(AdminTimeWidget):
    def __init__(self, attrs=None, format=None):
        final_attrs = {
            'class': 'border border-base-200 bg-white font-medium min-w-20 placeholder-base-400 rounded-default shadow-xs text-font-default-light text-sm focus:outline-2 focus:-outline-offset-2 focus:outline-primary-600 group-[.errors]:border-red-600 focus:group-[.errors]:outline-red-600 dark:bg-base-900 dark:border-base-700 dark:text-font-default-dark dark:group-[.errors]:border-red-500 dark:focus:group-[.errors]:outline-red-500 dark:scheme-dark group-[.primary]:border-transparent disabled:!bg-base-50 dark:disabled:!bg-base-800 px-3 py-2 w-full min-w-52'
        }
        if attrs is not None:
            final_attrs.update(attrs)
        super(AdminTimeWidgetStyled, self).__init__(attrs=final_attrs, format=format)


class AdminSplitJalaliDateTime(AdminSplitDateTime):
    template_name = 'admin/widgets/jalali_split_datetime.html'  # for django >= 1.11

    def __init__(self, attrs=None):
        widgets = [AdminJalaliDateWidget, AdminTimeWidgetStyled]
        # Note that we're calling MultiWidget, not SplitDateTimeWidget, because
        # we want to define widgets.
        forms.MultiWidget.__init__(self, widgets, attrs)

    def decompress(self, value):
        if value:
            value = to_current_timezone(value)
            j_date_obj = GregorianToJalali(gyear=value.year, gmonth=value.month, gday=value.day)
            date_str = '%d-%.2d-%.2d' % (j_date_obj.jyear, j_date_obj.jmonth, j_date_obj.jday)
            return [date_str, value.time().replace(microsecond=0)]
        return [None, None]

    def format_output(self, rendered_widgets):  # for django < 1.11
        return format_html(
            u'<p class="datetime">{} {} {} {}</p>', _('Date:'), rendered_widgets[0], _('Time:'), rendered_widgets[1]
        )
