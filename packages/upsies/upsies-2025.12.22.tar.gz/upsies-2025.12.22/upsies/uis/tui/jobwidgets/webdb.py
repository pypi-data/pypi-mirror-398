import functools
import textwrap

from prompt_toolkit.filters import Condition
from prompt_toolkit.layout.containers import ConditionalContainer, DynamicContainer, HSplit, VSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.utils import get_cwidth

from ....utils import browser, webdbs
from .. import widgets
from . import JobWidgetBase

import logging  # isort:skip
_log = logging.getLogger(__name__)


class WebDbSearchJobWidget(JobWidgetBase):

    is_interactive = True
    total_width = 80
    left_column_width = 36
    right_column_width = total_width - left_column_width - 1
    total_height = 20

    def setup(self):
        self._query_exception = None
        self._at_least_one_search_was_done = False
        self._widgets = {
            # First row
            'id': widgets.TextField(width=15, style='class:dialog.search.info'),
            'query': widgets.InputField(
                style='class:dialog.search.query',
                text=str(self.job.query),
                on_accepted=self.handle_query,
            ),

            # Right column
            'search_results': _SearchResults(width=self.right_column_width),
            'title_original': widgets.TextField(
                style='class:dialog.search.info',
                width=self.right_column_width,
                height=1,
            ),
            'title_english': widgets.TextField(
                style='class:dialog.search.info',
                width=self.right_column_width,
                height=1,
            ),

            # Left column
            'summary': widgets.TextField(
                style='class:dialog.search.info',
                width=self.left_column_width,
                height=8,
            ),
            'genres': widgets.TextField(
                style='class:dialog.search.info',
                width=self.left_column_width,
                height=2,
            ),
            'directors': widgets.TextField(
                style='class:dialog.search.info',
                width=self.left_column_width,
                height=1,
            ),
            'cast': widgets.TextField(
                style='class:dialog.search.info',
                width=self.left_column_width,
                height=2,
            ),
            'countries': widgets.TextField(
                style='class:dialog.search.info',
                width=self.left_column_width,
                height=1,
            ),

            # Poster (rightmost column)
            'poster': widgets.Image(height=self.total_height),
        }

        self.set_query_text(self.job.query)

        self.job.signal.register('search_results', self.handle_search_results)
        self.job.signal.register('searching_status', self.handle_searching_status)
        self.job.signal.register('info_updating', self.handle_info_updating)
        self.job.signal.register('info_updated', self.handle_info_updated)
        self.job.signal.register('query_updated', self.handle_query_updated)

    def invalidate(self, *, warnings=False):
        super().invalidate()
        if warnings:
            try:
                # Invalidate cached warnings
                del self.warnings
            except AttributeError:
                # No warnings have been generated yet
                pass

    def handle_query(self, buffer):
        query_text = self._widgets['query'].text
        if query_text != self._old_query_text:
            try:
                self.job.search(webdbs.Query.from_string(query_text))
            except ValueError as e:
                self._query_exception = e
            else:
                self._query_exception = None
                self.set_query_text(self.job.query)

        else:
            # The same query was accepted twice without changing it.
            # Select focused search result.
            focused = self._widgets['search_results'].focused_result
            if focused is not None:
                self.job.result_selected(focused)
            else:
                self.job.result_selected(None)

            # Query exception is no longer valid
            self._query_exception = None

        # Invalidate warnings to include new self._query_exception
        self.invalidate(warnings=True)

    def handle_searching_status(self, is_searching):
        self._widgets['search_results'].is_searching = is_searching

    def handle_search_results(self, results):
        self._widgets['search_results'].results = results
        self._at_least_one_search_was_done = True
        # Invalidate warnings to display/remove no-result-search-hints
        self.invalidate(warnings=True)

    def handle_info_updating(self, attr):
        self._widgets[attr].is_loading = True
        self.invalidate()

    def handle_info_updated(self, attr, value):
        self._widgets[attr].is_loading = False
        if isinstance(value, (bytes, bytearray)):
            self._widgets[attr].text = value
        elif value:
            self._widgets[attr].text = str(value)
        else:
            self._widgets[attr].text = ''
        self.invalidate()

    def handle_query_updated(self, query):
        self.set_query_text(query)
        for attr in (
                'id',
                'title_original',
                'title_english',
                'summary',
                'genres',
                'directors',
                'cast',
                'countries',
                'poster',
        ):
            self._widgets[attr].text = ''
        self.invalidate()

    def set_query_text(self, text):
        self._widgets['query'].set_text(str(text), preserve_cursor_position=True)
        self._old_query_text = self._widgets['query'].text

    @functools.cached_property
    def warnings(self):
        """Note for the user to find results"""
        warnings = []

        # User entered invalid query
        if self._query_exception:
            warnings.append(str(self._query_exception))

        # No search results - provide some hints
        if (
                # Don't show hints if we are still starting up and the first
                # search is not yet happening.
                self._at_least_one_search_was_done
                # Don't show hints if we are currently searching.
                and not self.job.is_searching
                # Don't show hints if there are search results.
                and not self._widgets['search_results'].results
        ):
            # Generic hints
            warnings.append(
                textwrap.fill(
                    'Try removing or adjusting "year:…" or "type:…". '
                    'You can provide an exact ID by searching for "id:…".',
                    width=self.total_width,
                ),
            )

            # Search hints for this specific webdb
            if self.job.db.no_results_info:
                warnings.append(
                    textwrap.fill(
                        self.job.db.no_results_info,
                        width=self.total_width,
                    )
                )

            # Maybe provide no ID as a valid job result
            if self.job.no_id_ok:
                warnings.append(
                    textwrap.fill(
                        (
                            f'Press Enter to provide no {self.job.db.label} ID if you are sure '
                            f'"{self.job.query.title}" does not exist on {self.job.db.label}.'
                        ),
                        width=self.total_width,
                    )
                )

        return '\n\n'.join(warnings)

    @functools.cached_property
    def runtime_widget(self):
        w = self._widgets

        # Everything except for the poster on the very right.
        textfields = HSplit(
            children=[
                VSplit([
                    w['query'],
                    widgets.hspacer,
                    widgets.HLabel(
                        text='ID',
                        content=w['id'],
                        style='class:dialog.search.label',
                    ),
                ]),
                ConditionalContainer(
                    filter=Condition(lambda: self.warnings),
                    content=HSplit([
                        widgets.vspacer,
                        Window(
                            FormattedTextControl(
                                lambda: self.warnings,
                                style='class:warning',
                            ),
                        )
                    ]),
                ),
                VSplit([
                    HSplit([
                        widgets.VLabel('Results', w['search_results'], style='class:dialog.search.label'),
                        widgets.VLabel('Original Title', w['title_original'], style='class:dialog.search.label'),
                        widgets.VLabel('Also Known As', w['title_english'], style='class:dialog.search.label'),
                    ]),
                    widgets.hspacer,
                    HSplit([
                        widgets.VLabel('Summary', w['summary'], style='class:dialog.search.label'),
                        widgets.VLabel('Genres', w['genres'], style='class:dialog.search.label'),
                        widgets.VLabel('Director', w['directors'], style='class:dialog.search.label'),
                        widgets.VLabel('Cast', w['cast'], style='class:dialog.search.label'),
                        widgets.VLabel('Country', w['countries'], style='class:dialog.search.label'),
                    ]),
                ]),
            ],
            style='class:dialog.search',
        )

        # `textfields` and the poster.
        dialog = VSplit(
            children=[
                textfields,
                widgets.hspacer,
                w['poster'],
            ],
        )
        # Add a spacer below the whole form to get some breathing room.
        layout = HSplit(
            children=[
                dialog,
                widgets.hspacer,
            ],
        )

        @self.keybindings_local.add('down')
        @self.keybindings_local.add('c-n')
        @self.keybindings_local.add('tab')
        def _(_event):
            prev_focused = self._widgets['search_results'].focused_result
            self._widgets['search_results'].focus_next()
            now_focused = self._widgets['search_results'].focused_result
            if prev_focused != now_focused:
                self.job.result_focused(now_focused)

        @self.keybindings_local.add('up')
        @self.keybindings_local.add('c-p')
        @self.keybindings_local.add('s-tab')
        def _(_event):
            prev_focused = self._widgets['search_results'].focused_result
            self._widgets['search_results'].focus_previous()
            now_focused = self._widgets['search_results'].focused_result
            if prev_focused != now_focused:
                self.job.result_focused(now_focused)

        # Alt-Enter
        @self.keybindings_local.add('escape', 'enter')
        def _(_event):
            url = self._widgets['search_results'].focused_result.url
            browser.open(url)

        return layout


class _SearchResults(DynamicContainer):
    def __init__(self, results=(), width=40):
        self.results = results
        self._year_width = 4
        self._type_width = 6
        self._title_width = width - self._year_width - self._type_width - 2
        self._activity_indicator = widgets.ActivityIndicator()
        super().__init__(
            lambda: Window(
                content=FormattedTextControl(self._get_text_fragments, focusable=False),
                width=width,
                height=14,
                style='class:dialog.search.results',
            )
        )

    @property
    def is_searching(self):
        return self._activity_indicator.active

    @is_searching.setter
    def is_searching(self, value):
        self._activity_indicator.active = bool(value)

    @property
    def results(self):
        return self._results

    @results.setter
    def results(self, results):
        self._results = tuple(results)
        self._focused_index = 0

    @property
    def focused_result(self):
        if self._results:
            return self._results[self._focused_index]
        else:
            return None

    def focus_next(self):
        if self._focused_index < len(self._results) - 1:
            self._focused_index += 1

    def focus_previous(self):
        if self._focused_index > 0:
            self._focused_index -= 1

    def focus_first(self):
        self._focused_index = 0

    def focus_last(self):
        self._focused_index = len(self._results) - 1

    def _get_text_fragments(self):
        if self.is_searching:
            return [('class:dialog.search.results', self._activity_indicator.text)]
        elif not self._results:
            return 'No results'

        frags = []
        for i, result in enumerate(self._results):
            if i == self._focused_index:
                title_style = 'class:dialog.search.results.focused'
                frags.append(('[SetCursorPosition]', ''))
                self._focused_result = result
            else:
                title_style = 'class:dialog.search.results'

            if get_cwidth(result.title) > self._title_width:
                title = result.title[:self._title_width - 1] + '…'
            else:
                title = result.title
            frags.append((title_style, title.ljust(self._title_width)))

            frags.append(('', (
                ' '
                f'{str(result.year or "").rjust(4)}'
                ' '
                f'{str(result.type).rjust(6)}'
            )))

            frags.append(('', '\n'))
        frags.pop()  # Remove last newline
        return frags
