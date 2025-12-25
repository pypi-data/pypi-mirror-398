"""
Concrete :class:`~.TrackerJobsBase` subclass for ANT
"""

import functools
import re

from ... import errors, jobs, utils
from ..base import TrackerJobsBase

import logging  # isort:skip
_log = logging.getLogger(__name__)


class AntTrackerJobs(TrackerJobsBase):

    @functools.cached_property
    def jobs_before_upload(self):
        return (
            # Interactive jobs
            self.playlists_job,
            self.tmdb_job,
            self.source_job,
            self.scene_check_job,

            # Background jobs
            self.create_torrent_job,
            self.group_job,
            self.mediainfo_job,
            self.bdinfo_job,
            self.resolution_job,
            self.flags_job,
            self.anonymous_job,
            self.description_job,
            self.rules_job,
        )

    @functools.cached_property
    def source_job(self):
        return jobs.dialog.ChoiceJob(
            name=self.get_job_name('source'),
            label='Source',
            precondition=self.make_precondition('source_job'),
            options=(
                ('Blu-ray', 'Blu-ray'),
                ('DVD', 'DVD'),
                ('WEB', 'WEB'),
                ('HD-DVD', 'HD-DVD'),
                ('HDTV', 'HDTV'),
                ('VHS', 'VHS'),
                ('TV', 'TV'),
                ('LaserDisc', 'LaserDisc'),
                ('Unknown', 'Unknown'),
            ),
            autodetect=self.autodetect_source,
            autofinish=True,
            **self.common_job_args(),
        )

    _autodetect_source_map = {
        'Blu-ray': lambda release_name: 'BluRay' in release_name.source,
        'HD-DVD': lambda release_name: 'HD-DVD' in release_name.source,
        'HDTV': lambda release_name: 'HDTV' in release_name.source,
        'DVD': lambda release_name: 'DVD' in release_name.source,
        'WEB': lambda release_name: 'WEB' in release_name.source,
        'VHS': lambda release_name: 'VHS' in release_name.source,
        'TV': lambda release_name: 'TV' in release_name.source,
        # 'LaserDisc': lambda release_name: ...,  # Not supported by ReleaseName
    }

    async def autodetect_source(self, job_):
        for option, autodetect in self._autodetect_source_map.items():
            if autodetect(self.release_name):
                return option

    @functools.cached_property
    def group_job(self):
        return jobs.dialog.TextFieldJob(
            name=self.get_job_name('group'),
            label='Group',
            precondition=self.make_precondition('group_job'),
            text=self.autodetect_group,
            validator=self.validate_group,
            finish_on_success=True,
            **self.common_job_args(),
        )

    # When uploading a group with "-" in it, ANT says: "Release group must be alphanumeric only."
    _release_group_regex = re.compile(r'^[a-zA-Z0-9]*$')

    async def autodetect_group(self):
        group = self.release_name.group
        if self._release_group_regex.search(group):
            return group
        else:
            self.group_job.set_text(group)
            self.group_job.warn('Leave empty if there is no group.')

    def validate_group(self, group):
        if not self._release_group_regex.search(group):
            raise ValueError('Release group must only contain alphanumeric characters (a-z, A-Z, 0-9)')

    @functools.cached_property
    def resolution_job(self):
        return jobs.dialog.ChoiceJob(
            name=self.get_job_name('resolution'),
            label='Resolution',
            precondition=self.make_precondition('resolution_job'),
            options=(
                'SD',
                '720p',
                '1080i',
                '1080p',
                '2160p',
            ),
            autodetect=self.autodetect_resolution,
            autofinish=True,
            **self.common_job_args(ignore_cache=True),
        )

    async def autodetect_resolution(self, job):
        resolution = utils.mediainfo.video.get_resolution_int(self.content_path)
        _log.debug('AUTODETECTED HEIGHT: %r', resolution)
        if resolution >= 2160:
            return '2160p'
        elif resolution >= 1080:
            scan_type = utils.mediainfo.video.get_scan_type(self.content_path)
            return f'1080{scan_type}'
        elif resolution >= 720:
            return '720p'
        else:
            return 'SD'

    @functools.cached_property
    def flags_job(self):
        return jobs.custom.CustomJob(
            name=self.get_job_name('flags'),
            label='Flags',
            precondition=self.make_precondition('flags_job'),
            worker=self.autodetect_flags,
            no_output_is_ok=True,
            **self.common_job_args(ignore_cache=True),
        )

    async def autodetect_flags(self, job):
        # supported flags: Directors, Extended, Uncut, IMAX, Unrated, HDR10, DV,
        # 4KRemaster, Atmos, DualAudio, Commentary, Remux, 3D, Criterion

        flags = []
        rn = self.release_name

        if "Director's Cut" in rn.edition:
            flags.append('Directors')
        if 'Extended Cut' in rn.edition:
            flags.append('Extended')
        if 'Uncut' in rn.edition:
            flags.append('Uncut')
        if 'Unrated' in rn.edition:
            flags.append('Unrated')
        if 'Criterion Collection' in rn.edition:
            flags.append('Criterion')
        if 'IMAX' in rn.edition:
            flags.append('IMAX')
        if '4k Remastered' in rn.edition:
            flags.append('4KRemaster')
        if 'Dual Audio' in rn.edition:
            flags.append('DualAudio')

        if 'Remux' in rn.source:
            flags.append('Remux')

        hdr_formats = utils.mediainfo.video.get_hdr_formats(self.content_path, default=())
        if 'DV' in hdr_formats:
            flags.append('DV')
        if 'HDR10' in hdr_formats or 'HDR10+' in hdr_formats:
            flags.append('HDR10')

        if 'Atmos' in rn.audio_format:
            flags.append('Atmos')

        if self.release_name.has_commentary:
            flags.append('Commentary')

        return flags

    @functools.cached_property
    def anonymous_job(self):
        return jobs.dialog.ChoiceJob(
            name=self.get_job_name('anonymous'),
            label='Anonymous',
            precondition=self.make_precondition('anonymous_job'),
            options=(
                ('No', False),
                ('Yes', True),
            ),
            autodetect=self.autodetect_anonymous,
            autofinish=True,
            **self.common_job_args(ignore_cache=True),
        )

    async def autodetect_anonymous(self, job):
        return self.options.get('anonymous', False)

    @functools.cached_property
    def description_job(self):
        return jobs.dialog.TextFieldJob(
            name=self.get_job_name('description'),
            label='Description',
            precondition=self.make_precondition('description_job'),
            prejobs=(
                self.mediainfo_job,
                self.bdinfo_job,
            ),
            text=self.generate_description,
            error_exceptions=(
                errors.ContentError,  # Raised by read_nfo()
            ),
            hidden=True,
            finish_on_success=True,
            read_only=True,
            **self.common_job_args(ignore_cache=True),
        )

    def generate_description(self):
        parts = []

        # FIXME [2024-08-17] NFOs are currently interpreted as BBcode and/or Markdown even inside
        #                    [pre] tags, wich messes up everything.
        # nfo = self.generate_description_nfo()
        # if nfo:
        #     parts.append(nfo)

        if mediainfo := self.generate_description_mediainfo():
            parts.append(mediainfo)

        if bdinfo := self.generate_description_bdinfo():
            parts.append(bdinfo)

        if promo := self.generate_promotion_bbcode():
            if parts:
                parts.append(f'\n{promo}')
            else:
                parts.append(promo)

        return '\n'.join(part for part in parts if part)

    def generate_description_bdinfo(self):
        # BDInfo is not generated if we're submitting non-BDMV release.
        if self.bdinfo_job.is_enabled:
            assert self.bdinfo_job.is_finished
            bdinfos_by_file = tuple(self.bdinfo_job.reports_by_file.items())
            if bdinfos_by_file:
                bdinfos_bbcode = []
                for video_filepath, bdinfo in bdinfos_by_file:
                    filetitle = self.get_relative_file_path(video_filepath)
                    bdinfos_bbcode.append(f'[spoiler={filetitle}]{bdinfo.quick_summary}[/spoiler]')
                return '\n'.join(bdinfos_bbcode)

    def generate_description_mediainfo(self):
        # For VIDEO_TS releases, 2 mediainfo reports are generted, one for an .IFO file and one for
        # a .VOB. Because the "mediainfo" in the POST request has only room for one report, we
        # include both reports in the description as well.
        if self.mediainfo_job.is_enabled:
            assert self.mediainfo_job.is_finished
            mediainfos_by_file = tuple(self.mediainfo_job.reports_by_file.items())
            if len(mediainfos_by_file) >= 2:
                mediainfos_bbcode = []
                for video_filepath, mediainfo in mediainfos_by_file:
                    filetitle = self.get_relative_file_path(video_filepath)
                    mediainfos_bbcode.append(f'[spoiler={filetitle}]{mediainfo}[/spoiler]')
                return '\n'.join(mediainfos_bbcode)

    def generate_description_nfo(self):
        nfo = self.read_nfo(strip=True)
        if nfo:
            return (
                '[spoiler=NFO]'
                + '[pre]'
                + nfo
                + '[/pre]'
                + '[/spoiler]'
            )

    # Mediainfo is provided normally and BDInfo is added to the description.
    mediainfo_required_for_bdmv = True

    @property
    def post_data(self):
        return {
            'api_key': self._tracker.apikey,
            'action': 'upload',
            # type=0 for "Feature Film". Miniseries and short films probably don't work.
            'type': '0',
            'tmdbid': self.get_job_output(self.tmdb_job, slice=0).replace('movie/', ''),
            'mediainfo': self.get_job_output(self.mediainfo_job, slice=0),
            'release_desc': self.get_job_output(self.description_job, slice=0) or None,
            'flags[]': self.get_job_output(self.flags_job),
            # Scene release? (I don't know why it's called "censored".)
            'censored': '1' if self.get_job_attribute(self.scene_check_job, 'is_scene_release') else None,
            'anonymous': '1' if self.get_job_attribute(self.anonymous_job, 'choice') else None,
            'media': self.get_job_attribute(self.source_job, 'choice'),
            'ressel': self.get_job_attribute(self.resolution_job, 'choice'),
            **self._post_data_release_group,
        }

    @property
    def _post_data_release_group(self):
        group = self.get_job_output(self.group_job, slice=0)
        if group.lower() in ('nogroup', 'nogrp', ''):
            # Default value of <input type="checkbox"> is "on":
            # https://developer.mozilla.org/en-US/docs/Web/HTML/Element/Input/checkbox
            return {'noreleasegroup': 'on'}
        else:
            return {'releasegroup': group}

    @property
    def post_files(self):
        return {
            'file_input': {
                'file': self.torrent_filepath,
                'mimetype': 'application/x-bittorrent',
            },
        }
