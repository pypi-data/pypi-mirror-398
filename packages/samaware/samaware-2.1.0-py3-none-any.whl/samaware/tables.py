import django_tables2
from django.urls import reverse
from django.utils.formats import date_format
from django.utils.html import format_html, format_html_join
from django.utils.timezone import localtime
from django.utils.translation import gettext_lazy as _
from pretalx.schedule.models import TalkSlot

from . import models


def _get_talk_overview_link(record):

    return reverse('plugins:samaware:talk_overview', kwargs={
        'event': record.submission.event.slug,
        'code': record.submission.code
    })


class SpeakersColumn(django_tables2.TemplateColumn):
    """
    TemplateColumn that uses the "speakers.html" template and includes speaker profiles for the event in its
    context. For this to work, the profiles must be available as the "event_profiles" property of the table
    using the column.
    """

    def __init__(self, **kwargs):
        super().__init__(template_name='samaware/table_cols/speakers.html', **kwargs)

    def render(self, record, table, value, bound_column, **kwargs):
        self.extra_context['talk_url'] = _get_talk_overview_link(record)
        self.extra_context['event_profiles'] = table.event_profiles
        return super().render(record, table, value, bound_column, **kwargs)


class MissingSpeakersTable(django_tables2.Table):

    track = django_tables2.TemplateColumn(
        accessor='submission__track',
        verbose_name='',
        template_name='samaware/table_cols/track.html'
    )
    submission = django_tables2.Column(
        accessor='submission__title',
        verbose_name=_('Title'),
        linkify=_get_talk_overview_link
    )
    speakers = SpeakersColumn(
        accessor='submission__speakers__all',
        verbose_name=_('Speakers'),
        orderable=False
    )

    class Meta:
        model = TalkSlot
        fields = ('track', 'submission', 'speakers', 'start', 'room')
        order_by = 'start'

    def __init__(self, *args, event_profiles, **kwargs):
        super().__init__(*args, **kwargs)
        self.event_profiles = event_profiles

    def before_render(self, request):
        if not request.event.get_feature_flag('use_tracks'):
            self.columns.hide('track')


class NoRecordingTable(django_tables2.Table):

    track = django_tables2.TemplateColumn(
        accessor='submission__track',
        verbose_name='',
        template_name='samaware/table_cols/track.html'
    )
    submission = django_tables2.Column(
        accessor='submission__title',
        verbose_name=_('Title'),
        linkify=_get_talk_overview_link
    )

    class Meta:
        model = TalkSlot
        fields = ('track', 'submission', 'start', 'room')
        order_by = 'start'

    def before_render(self, request):
        if not request.event.get_feature_flag('use_tracks'):
            self.columns.hide('track')


def _get_tech_rider_link(record):

    return reverse('plugins:samaware:tech_rider_update', kwargs={
        'event': record.submission.event.slug,
        'pk': record.submission.tech_rider.pk
    })


class TechRiderTable(django_tables2.Table):

    submission = django_tables2.Column(
        accessor='submission__title',
        verbose_name=_('Talk'),
        linkify=_get_tech_rider_link
    )
    updated = django_tables2.DateTimeColumn(
        accessor = 'submission__tech_rider__updated',
        verbose_name=_('Updated')
    )
    text = django_tables2.TemplateColumn(
        accessor='submission__tech_rider__text',
        orderable=False,
        linkify=_get_tech_rider_link,
        template_name='samaware/table_cols/truncate_text.html'
    )

    class Meta:
        model = TalkSlot
        fields = ('submission', 'start', 'room', 'updated', 'text')
        order_by = 'submission'


class CareMessageTable(django_tables2.Table):

    speaker = django_tables2.Column(
        accessor='speaker__name'
    )
    text = django_tables2.TemplateColumn(
        accessor='text',
        orderable=False,
        linkify=True,
        template_name='samaware/table_cols/truncate_text.html'
    )
    talks = django_tables2.Column(
        verbose_name=_('Talks'),
        orderable=False,
        # Prevent django-tables2 from considering all values empty, actual values get set
        # through render_talks()
        empty_values=()
    )
    first_start = django_tables2.DateTimeColumn(
        verbose_name=_('1st Talk Start'),
        # Prevent django-tables2 from considering all values empty, actual values get set
        # through render_first_start()
        empty_values=()
    )

    class Meta:
        model = models.SpeakerCareMessage
        fields = ('speaker', 'text', 'talks', 'first_start')
        order_by = 'speaker'

    def __init__(self, *args, speaker_talks, speaker_first_slots, **kwargs):
        super().__init__(*args, **kwargs)
        self.speaker_talks = speaker_talks
        self.speaker_first_slots = speaker_first_slots

    def render_talks(self, record):
        def get_link(talk):
            url = reverse('plugins:samaware:talk_overview', kwargs={'event': talk.event.slug,
                                                                    'code': talk.code})
            return format_html('<a href="{}">{}</a>', url, talk.title)

        talks = self.speaker_talks[record.speaker]
        return format_html_join(', ', '{}', ([get_link(t)] for t in talks))

    def render_first_start(self, record):
        slot = self.speaker_first_slots[record.speaker]
        return date_format(localtime(slot.start), 'SHORT_DATETIME_FORMAT')

    def order_first_start(self, queryset, is_descending):
        ordered = sorted(queryset, key=lambda m: self.speaker_first_slots[m.speaker].start,
                         reverse=is_descending)
        return (ordered, True)
