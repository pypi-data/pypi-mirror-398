"""
Query online databases like IMDb
"""

import asyncio
import collections

from .. import errors
from ..utils import webdbs
from . import JobBase

import logging  # isort:skip
_log = logging.getLogger(__name__)


class WebDbSearchJob(JobBase):
    """
    Ask user to select a specific search result from an internet database

    This job adds the following signals to :attr:`~.JobBase.signal`:

        ``search_results``
            Emitted after new search results are available. Registered callbacks
            get a sequence of :class:`~.utils.webdbs.common.SearchResult`
            instances as a positional argument.

        ``searching_status``
            Emitted when a new search is started and when new results are
            available. Registered callbacks get `True` for "search started" or
            `False` for "search ended" as a positional argument.

        ``info_updating``
            Emitted when an attempt to fetch additional information is made.
            Registered callbacks get the name of an attribute of a
            :class:`~.utils.webdbs.common.SearchResult` object that returns a
            coroutine function as a positional argument.

        ``info_updated``
            Emitted when additional information is available. Registered
            callbacks are called for each piece of information and get ``key``
            and ``value`` as positional arguments. ``key`` is an attribute of a
            :class:`~.utils.webdbs.common.SearchResult` object that returns a
            coroutine function. ``value`` is the return value of that coroutine
            function.

        ``query_updated``
            Emitted after the :attr:`query` changed. Registered callbacks get
            the new query as a positional argument.

        ``selected``
            Emitted when :meth:`result_selected` is called. Registered callbacks
            get a :class:`dict` with the keys ``id``, ``title``, ``type``,
            ``url`` and ``year``.
    """

    @property
    def name(self):
        return f'{self._db.name}-id'

    @property
    def label(self):
        return f'{self._db.label} ID'

    @property
    def cache_id(self):
        """Database :attr:`~.WebDbApiBase.name` and :attr:`query`"""
        return self.query

    @property
    def db(self):
        """:class:`~.webdbs.base.WebDbApiBase` instance"""
        return self._db

    @property
    def query(self):
        """:class:`~.webdbs.common.Query` instance"""
        return self._query

    @property
    def no_id_ok(self):
        """Whether this job will finish gracefully if no ID is selected"""
        return self._no_id_ok

    @no_id_ok.setter
    def no_id_ok(self, value):
        self._no_id_ok = bool(value)

    @property
    def show_poster(self):
        """Whether to display a poster of the focused search result"""
        return self._show_poster

    @show_poster.setter
    def show_poster(self, value):
        self._show_poster = bool(value)

    def _get_show_poster(self):
        return self._show_poster

    @property
    def is_searching(self):
        """Whether a search request is currently being made"""
        return self._is_searching

    def initialize(self, *, db, query, autodetect=None, no_id_ok=False, show_poster=True):
        """
        Set internal state

        :param WebDbApiBase db: Return value of :func:`.utils.webdbs.webdb`
        :param query: Path of the release (doesn't have to exist) or
            :class:`~.webdbs.common.Query` instance
        :param autodetect: Coroutine function that takes no arguments and
            returns an ID or `None`

            If `autodetect` returns a valid ID it is automatically selected and
            the job is finished with no user interaction. Otherwise, the
            returned ID is inserted into the usual prompt and it's up to the
            user to fix it.
        :param no_id_ok: Whether this job may finish without error if no ID is
            selected
        :param show_poster: Whether to display a poster of the focused search
            result
        """
        assert isinstance(db, webdbs.WebDbApiBase), f'Not a WebDbApiBase: {db!r}'
        self._db = db
        if not isinstance(query, webdbs.Query):
            query = webdbs.Query.from_any(query)
        self._query = self._db.sanitize_query(query)
        self._autodetect = autodetect

        self.signal.add('search_results')
        self.signal.add('searching_status')
        self.signal.add('info_updating')
        self.signal.add('info_updated')
        self.signal.add('query_updated')
        self.signal.add('selected', record=True)

        # Call search() when `self.query` is changed externally, e.g. by another
        # job. This happens if we have multiple WebDbSearchJobs with different
        # WebDbs and we want to update the query of the second job with accurate
        # information from the first job. This means the user only has to fix a
        # potentially badly autodetected query once and not for each
        # WebDbSearchJob.
        self._query.signal.register('changed', self.search)

        # Hold some information about the selected search result.
        self._selected = {}
        self.signal.register('selected', self._selected.update)

        self.no_id_ok = no_id_ok
        self.show_poster = show_poster
        self._is_searching = False
        self._search_task = None
        self._info_callbacks_task = None
        self._info_callbacks = _InfoCallbacks(
            callbacks={
                'id': self._make_update_info_func('id'),
                'summary': self._make_update_info_func('summary'),
                'title_original': self._make_update_info_func('title_original'),
                'title_english': self._make_update_info_func('title_english'),
                'genres': self._make_update_info_func('genres'),
                'directors': self._make_update_info_func('directors'),
                'cast': self._make_update_info_func('cast'),
                'countries': self._make_update_info_func('countries'),
                'poster': self._make_update_info_func('poster', condition=self._get_show_poster),
            },
            error_callback=self.warn,
        )

    def _make_update_info_func(self, key, condition=lambda: True):
        def update_info_func(value):
            if condition():
                self._update_info_value(key, value)
        return update_info_func

    def _update_info_value(self, attr, value):
        if value is Ellipsis:
            # Indicate that we are updating `attr` by not providing a value.
            self.signal.emit('info_updating', attr)
        else:
            self.signal.emit('info_updated', attr, value)

    async def run(self):
        if self._autodetect is not None:
            id = await self._autodetect()
            _log.debug(f'Autodetected {self.db.name} ID from %r: %r', self._autodetect, id)
            if id:
                id = self._db.get_id_from_text(id)
                if id:
                    self.query.id = id
                    self.query.feeling_lucky = True

        # Trigger initial search. We must always search, even if an ID was
        # autodetected, to verify it's a valid ID.
        self.search(self.query)

        # Block until finalize() is called.
        await self.finalization()

    async def _search(self, query):
        self._set_state(is_searching=True, results=())

        try:
            # Get new search results
            results = await self._db.search(query)
            self._set_state(is_searching=False, results=results)

            if results:
                if query.feeling_lucky and len(results) == 1:
                    # Select single search result.
                    self.result_selected(results[0])
                else:
                    # Display details about the first search result.
                    self._run_info_callbacks(results[0])
            else:
                # Unset all details from previously selected search result.
                self._run_info_callbacks(None)

        except errors.RequestError as e:
            self.warn(e)

        finally:
            self._set_state(is_searching=False)
            # We no longer feel lucky. If the query was lucky, there is no next
            # query. If the query was unlucky, do not autoselect any new query.
            query.feeling_lucky = False

    def _set_state(self, *, is_searching=None, results=None):
        if is_searching is not None:
            self._is_searching = bool(is_searching)
            self.signal.emit('searching_status', self._is_searching)
        if results is not None:
            self.signal.emit('search_results', results)

    def _run_info_callbacks(self, result):
        if self._info_callbacks_task:
            self._info_callbacks_task.cancel()
        self._info_callbacks_task = self.add_task(
            self._info_callbacks(result),
            # Auto-remove reference to task when it is done.
            callback=self._unset_info_callbacks_task,
        )

    def _unset_info_callbacks_task(self, task_):
        self._info_callbacks_task = None

    def _cancel_tasks(self):
        for task_attr in ('_search_task', '_info_callbacks_task'):
            task = getattr(self, task_attr, None)
            if task:
                task.cancel()
                setattr(self, task_attr, None)

    def search(self, query):
        """
        Make new search request

        Any currently ongoing search is cancelled.

        :param str query: Query that is first passed through
            :meth:`~.webdbs.Query.from_any` and then
            :meth:`~.webdbs.WebDbApiBase.sanitize_query`
        """
        # Stop any ongoing requests. They are outdated.
        self._cancel_tasks()

        # Remove any warnings from previous requests (e.g. network issues).
        self.clear_warnings()

        # Update search query silently (without emitting any signals).
        new_query = self._db.sanitize_query(webdbs.Query.from_any(query))
        self.query.update(new_query, silent=True)
        self.signal.emit('query_updated', self.query)

        # Because this is not an asynchronous method, we have to do the actual searching in a
        # task. If we are called happens before this job is started, we cannot add any tasks yet,
        # but that's ok because we already updated our internal query, which will be used for the
        # initial search if this job is started.
        #
        # If `search()` is called or after this job is finished or termianted (e.g. because the job
        # was terminated due to an error), we the query doesn't matter and we can just not create
        # the asynchronous search task.
        if self.is_started and not self.is_terminated and not self.is_finished:
            # Initiate new search in a separate task so we can cancel it.
            self._search_task = self.add_task(
                self._search(new_query),
                # Auto-remove reference to task when it is done.
                callback=self._unset_search_task,
            )

    def _unset_search_task(self, task_):
        self._search_task = None

    def result_focused(self, result):
        """
        Must be called by the UI when the user focuses a different search result

        :param SearchResult result: Focused search result or `None` if there are
            no results
        """
        self._run_info_callbacks(result)

    def result_selected(self, result):
        """
        Must be called by the UI when the user accepts a search result

        :param SearchResult result: Focused search result or `None` if there are
            no results and the user accepted that (see :attr:`no_id_ok`)
        """
        if not self.is_searching:
            if result is not None:
                self.signal.emit('selected', {
                    'id': result.id,
                    'title': result.title,
                    'type': result.type,
                    'url': result.url,
                    'year': result.year,
                })
                self.add_output(result.id)

            if result is not None or self.no_id_ok:
                self._cancel_tasks()
                self.finalize()

    @property
    def selected(self):
        """
        Some more information about the selected search result

        This is a :class:`dict` that is empty before :meth:`result_selected`
        is called. After :meth:`result_selected` is called, it contains the
        following keys:

            - ``id``
            - ``title``
            - ``type``
            - ``url``
            - ``year``
        """
        return self._selected.copy()

    @property
    def exit_code(self):
        """`0` if job was successful, `> 0` otherwise, None while job is not finished"""
        exit_code = super().exit_code
        if exit_code is not None:
            if exit_code != 0 and self.no_id_ok:
                return 0
            else:
                return exit_code


class _InfoCallbacks:
    def __init__(self, callbacks, error_callback):
        # `callbacks` maps names of SearchResult attributes to callbacks that
        # get the value of each attribute.
        #
        # For example, {"title": handle_title} means: Get the "title" attribute
        # from a search result and pass it to handle_title().
        #
        # Values of SearchResult attributes may also be coroutine functions that
        # return the value. In that case, call
        # handle_title(await search_result.title()).
        self._callbacks = callbacks
        self._error_callback = error_callback

    async def __call__(self, result):
        if not result:
            for callback in self._callbacks.values():
                callback('')
        else:
            self._update_text_values(result)
            await self._update_awaitable_values(result)

    def _update_text_values(self, result):
        # Update plain, non-callable values first before awaiting coroutines.
        for attr, callback in self._callbacks.items():
            value = getattr(result, attr)
            if not callable(value):
                callback(self._convert_value(value))

    async def _update_awaitable_values(self, result):
        # Update values that are coroutine functions that return the value.
        tasks = []
        for attr, callback in self._callbacks.items():
            value = getattr(result, attr)
            if callable(value):
                tasks.append(self._call_callback(
                    value_getter=value,
                    callback=callback,
                    cache_key=(result.id, attr),
                ))
        # Get all values concurrently
        await asyncio.gather(*tasks)

    _cache = {}
    _delay_between_updates = 0.5

    async def _call_callback(self, value_getter, callback, cache_key):
        cached_value = self._cache.get(cache_key, None)
        if cached_value is not None:
            callback(cached_value)
        else:
            # Wait for a bit before starting to load info. If the user rapidly
            # focuses different search results, we don't want to start lots of
            # requests every few fractions of a second.
            callback(Ellipsis)
            await asyncio.sleep(self._delay_between_updates)

            # Get attribute value from from search result
            try:
                value = await value_getter()
            except errors.RequestError as e:
                callback('')
                self._error_callback(e)
            else:
                value_converted = self._convert_value(value)
                self._cache[cache_key] = value_converted
                callback(value_converted)

    @staticmethod
    def _convert_value(value):
        if (
                isinstance(value, collections.abc.Iterable)
                and not isinstance(value, (str, bytes, bytearray))
        ):
            return ', '.join(str(v) for v in value)
        else:
            return value
