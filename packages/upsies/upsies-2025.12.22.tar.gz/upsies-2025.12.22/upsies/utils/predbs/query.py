"""
Query scene release
"""

import re

from ... import utils

import logging  # isort:skip
_log = logging.getLogger(__name__)

natsort = utils.LazyModule(module='natsort', namespace=globals())


class SceneQuery:
    """
    Search query for scene release databases

    :param keywords: Search keywords
    :param group: Release group name
    :param episodes: :class:`~.release.Episodes`-like mapping

    .. note: `episodes` is only used to extract the actually wanted episodes
        from the search results. Season packs (e.g. "S03") is removed from
        `keywords`.

        PreDBs usually don't allow us to search for season packes or multiple
        episodes (or even multiple season packs), which we can do with this
        approach.
    """

    @classmethod
    def from_string(cls, string):
        """
        Create query from `string`

        :param string: Release name or path to release content

        `string` is passed to :class:`~.release.ReleaseInfo` and the result is
        passed to :meth:`from_release`.
        """
        release = utils.release.ReleaseInfo(string, strict=False)
        return cls.from_release(release)

    @classmethod
    def from_release(cls, release):
        """
        Create query from :class:`dict`-like object

        :param release: :class:`~.release.ReleaseName` or
            :class:`~.release.ReleaseInfo` instance or any :class:`dict`-like
            object with the keys ``type``, ``title``, ``year``, ``episodes``,
            ``resolution``, ``source``, ``video_codec`` and ``group``.
        """
        if isinstance(release, utils.release.ReleaseName):
            release = release.release_info

        original_release = release.copy()

        # Replace H.264/5 with H264/5
        release['video_codec'] = re.sub(r'\.', '', release.get('video_codec', ''))

        # Replace WEB-DL with WEB
        if release.get('source') == 'WEB-DL':
            release['source'] = 'WEB'

        # Group and episodes are handled separately from the other keywords. We
        # don't include episodes in the keywords. Instead, we get all episodes
        # of all seasons in one query and filter out the episodes we want when
        # postprocessing the results (see
        # PredbApiBase._postprocess_search_results()). This allows us to search
        # for multiple seasons ("S01S02") and multiple episodes
        # ("S01E01S02E02E03"). It also means we don't have to wait 40 seconds
        # per episode when querying srrdb for a season pack.
        needed_keys = utils.predbs.common.get_needed_keys(
            release,
            exclude=('group', 'episodes'),
        )

        # Some `release` values may be sequence of multiple values, e.g. "edition".
        keywords = []
        for key in needed_keys:
            if utils.is_sequence(release[key]):
                keywords.extend(release[key])
            else:
                keywords.append(release[key])

        # Casefold all keywords to normalize them.
        keywords = [kw.casefold() for kw in keywords]

        query = cls(
            *keywords,
            group=release.get('group', ''),
            episodes=release.get('episodes', {}),
            release_info=original_release,
        )
        return query

    def __init__(self, *keywords, group='', episodes={}, release_info=None):
        # Split each keyword at spaces
        kws = (k.strip()
               for kw in keywords
               for k in str(kw).split())

        # Remove season packs (keep "SxxEyy" but not "Sxx") because scene
        # releases are not season packs and we don't find anything if we look
        # for "S05". For season packs, we try to find all episodes of all
        # seasons and extract the relevant episodes in _handle_results().
        def exclude_season_pack(kw):
            if utils.release.Episodes.is_episodes_info(kw):
                episodes = utils.release.Episodes.from_string(kw)
                for season in tuple(episodes):
                    if not episodes[season]:
                        del episodes[season]
                return str(episodes)
            else:
                return kw

        kws = (exclude_season_pack(kw) for kw in kws)

        # Remove empty keywords
        # (I forgot why "-" is removed. Please explain if you know!)
        kws = (kw for kw in kws
               if kw and kw != '-')

        self._keywords = tuple(kws)
        self._group = str(group) if group else None
        self._episodes = episodes
        self._release_info = release_info

    @property
    def keywords(self):
        """Sequence of search terms"""
        return self._keywords

    @property
    def group(self):
        """Release group name"""
        return self._group

    @property
    def episodes(self):
        """:class:`~.release.Episodes`-like mapping"""
        return self._episodes

    @property
    def release_info(self):
        """:class:`~.ReleaseInfo` object this query was created from or `None`"""
        return self._release_info

    def __repr__(self):
        args = []
        if self.keywords:
            args.append(', '.join(repr(kw) for kw in self.keywords))
        if self.group:
            args.append(f'group={self.group!r}')
        if self.episodes:
            args.append(f'episodes={self.episodes!r}')
        args_str = ', '.join(args)
        return f'{type(self).__name__}({args_str})'

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return (
                self.keywords == other.keywords
                and self.group == other.group
                and self.episodes == other.episodes
            )
        else:
            return NotImplemented
