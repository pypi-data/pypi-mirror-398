"""
Dummy tracker for testing and debugging
"""

import asyncio
import functools
import os
import random
import string

from .. import errors, jobs, uis, utils
from . import base

import logging  # isort:skip
_log = logging.getLogger(__name__)


if utils.is_running_in_development_environment():

    DummyImagehost = utils.types.Imagehost(allowed=('dummy',))


    class DummyTrackerConfig(base.TrackerConfigBase):
        base_url: base.config.base_url('http://localhost')
        username: base.config.username('')
        password: base.config.password('')
        tfa: utils.config.fields.boolean(
            default='no',
            description='Whether to ask for 2FA one-time password for each login.',
        )

        image_host: base.config.image_host(
            DummyImagehost,
            default=('dummy',),
        )

        exclude: base.config.exclude()

        source: utils.config.fields.string(
            default='DMY',
            description='"source" field in generated torrents.',
        )


    cli_arguments = {
        'submit': {
            ('--imdb', '--im'): {
                'help': 'IMDb ID or URL',
                'type': utils.argtypes.webdb_id('imdb'),
            },
            ('--tmdb', '--tm'): {
                'help': 'TMDb ID or URL',
                'type': utils.argtypes.webdb_id('tmdb'),
            },
            ('--skip-category', '-C'): {
                'help': 'Do not ask for category',
                'action': 'store_true',
            },
            ('--screenshots-count', '--ssc'): {
                'help': 'How many screenshots to make',
                'type': utils.argtypes.make_integer(min=3, max=10),
            },
            ('--screenshots', '--ss'): {
                'help': (
                    'Path(s) to created screenshot file(s)\n'
                    'Directories are searched recursively.\n'
                    'More screenshots are created if necessary.'
                ),
                'nargs': '+',
                'action': 'extend',
                'type': utils.argtypes.files_with_extension('png'),
            },
            ('--delay', '-d'): {
                'help': 'Number of seconds login, upload and logout take each',
                'type': float,
                'default': 1.0,
            },
            ('--get-announce-from-website'): {
                'help': 'Whether to act like we are getting the announce URL from the website ',
                'action': 'store_true',
            },
            ('--get-torrent-from-website'): {
                'help': 'Whether to download the torrent from the website instead of adding our own ',
                'action': 'store_true',
            },
            ('--poster'): {
                'help': 'Poster file or URL ',
            },
        },
        'torrent-create': {
            ('--delay', '-d'): {
                'help': 'Number of seconds login and logout take each',
                'type': float,
                'default': 0.0,
            },
            ('--get-announce-from-website'): {
                'help': 'Whether to act like we are getting the announce URL from the website ',
                'action': 'store_true',
            },
        },
    }


    class DummyTrackerJobs(base.TrackerJobsBase):

        release_name_separator = '_'

        @functools.cached_property
        def jobs_before_upload(self):
            return (
                self.login_job,

                # Interactive jobs
                self.playlists_job,
                self.tmdb_job,
                self.imdb_job,
                self.release_name_job,
                self.category_job,
                self.scene_check_job,

                # Background jobs
                self.create_torrent_job,
                self.screenshots_job,
                self.upload_screenshots_job,
                self.poster_job,
                self.mediainfo_job,

                # Silly jobs
                self.random_string_job,
                self.stupid_question_job,
                self.say_something_job,
                self.rules_job,
            )

        @functools.cached_property
        def random_string_job(self):
            return jobs.custom.CustomJob(
                name=self.get_job_name('random-string'),
                label='Random String',
                precondition=self.make_precondition('random_string_job'),
                worker=self.generate_random_string,
                catch=(
                    errors.RequestError,
                ),
                **self.common_job_args(ignore_cache=True),
            )

        async def generate_random_string(self, job):
            # await asyncio.sleep(3)
            # self.random_string_job.warn('Watch out!')

            await asyncio.sleep(1)

            # raise errors.RequestError('foo :(')
            # raise RuntimeError('foo D:')

            return ''.join(
                random.choice(string.ascii_lowercase)
                for _ in range(30)
            )

        @functools.cached_property
        def stupid_question_job(self):
            return jobs.dialog.ChoiceJob(
                name=self.get_job_name('stupid-question'),
                label='Stupid Question',
                precondition=self.make_precondition('stupid_question_job'),
                prejobs=(
                    self.random_string_job,
                ),
                autodetect=self.autodetect_stupid_answer,
                question='Is the random string random enough?',
                options=(
                    'Possibly',
                    'Maybe',
                    'Perhaps',
                ),
                multichoice=True,
                validate=self._validate_chosen,
                callbacks={
                    'finished': lambda job: job.clear_warnings(),
                },
                **self.common_job_args(),
            )

        def _validate_chosen(self, chosen):
            labels = [option[0] for option in chosen]
            if 'Perhaps' in labels:
                raise ValueError('I have decided that "Perhaps" is not an option after all.')
            elif len(labels) < 2:
                raise ValueError('Pick at least 2 options.')

        async def autodetect_stupid_answer(self, job):
            assert self.random_string_job.is_finished

            # raise RuntimeError('How would I know?')

            random_string = self.random_string_job.output[0]
            if all(character in random_string for character in 'abc'):
                return 'Maybe'
            else:
                self.stupid_question_job.add_prompt(
                    uis.prompts.RadioListPrompt(
                        question='Is this job too stupid?',
                        options=('Yes', 'No'),
                        callbacks=(
                            self.prompt_stupid_answer_callback,
                        ),
                    )
                )
                self.stupid_question_job.add_prompt(
                    uis.prompts.CheckListPrompt(
                        question='Are you sure?',
                        options=('Yes', 'No', 'Maybe?'),
                        callbacks=(
                            self.prompt_stupid_answer_callback_2,
                        ),
                    )
                )
                self.stupid_question_job.add_prompt(
                    uis.prompts.RadioListPrompt(
                        options=('Foo', 'Bar'),
                        callbacks=(),
                    )
                )

        def prompt_stupid_answer_callback(self, result):
            if result == 'Yes':
                self.stupid_question_job.error('This job is too stupid.')
            else:
                self.stupid_question_job.warn('Choose wisely!')

        def prompt_stupid_answer_callback_2(self, result):
            if 'Yes' in result and 'No' in result:
                self.stupid_question_job.error('Yes and No? Be more decisive!')
            elif 'Maybe?' in result:
                self.stupid_question_job.warn('Okay?')
            elif 'Yes' not in result:
                self.stupid_question_job.error('This job may be too stupid after all!')

        @functools.cached_property
        def say_something_job(self):
            return jobs.dialog.TextFieldJob(
                name=self.get_job_name('say-something'),
                label='Something',
                precondition=self.make_precondition('say_something_job'),
                prejobs=(
                    self.random_string_job,
                ),
                warn_exceptions=(
                    ValueError,
                ),
                text=self.generate_something,
                **self.common_job_args(),
            )

        async def generate_something(self):
            assert self.random_string_job.is_finished
            word = self.random_string_job.output[0]

            await asyncio.sleep(6)
            self.say_something_job.warn('Still thinking...')
            await asyncio.sleep(6)

            self.say_something_job.clear_warnings()
            if 'x' in word:
                raise ValueError(f'There is an "x" in "{word}"! Yuck!')
            elif 'a' in word:
                return 'Avocado!'
            else:
                return f'This is a completely original random string: {word}'

        @functools.cached_property
        def category_job(self):
            if not self.options['skip_category']:
                return jobs.dialog.ChoiceJob(
                    name=self.get_job_name('category'),
                    label='Category',
                    precondition=self.make_precondition('category_job'),
                    options=(
                        (str(typ).capitalize(), typ)
                        for typ in utils.types.ReleaseType if typ
                    ),
                    autodetected=self.release_name.type,
                    **self.common_job_args(),
                )


    class DummyHdOnly(base.rules.HdOnly):
        message = 'This is not HD!'

        async def _check(self):
            await super()._check()


    class DummyBannedGroup(base.rules.BannedGroup):
        banned_groups = {
            'FoO',
            'BAR',
        }

        async def _check_custom(self):
            if (
                    self.is_group('BAZ')
                    and 'Remux' in self.release_name.source
            ):
                raise errors.BannedGroup('BAZ', additional_info='No remuxes')


    class DummyNoEpisodes(base.rules.TrackerRuleBase):
        required_jobs = ('category_job', 'say_something_job', 'imdb_job')

        async def _check(self):
            _log.debug('################# CHECKING CATEGORY: %r', self.tracker_jobs.category_job.choice)
            await super()._check()
            if self.tracker_jobs.category_job.choice is utils.types.ReleaseType.episode:
                raise errors.RuleBroken('No episodes allowed')


    class DummyTracker(base.TrackerBase):
        name = 'dummy'
        label = 'DuMmY'

        cli_arguments = cli_arguments
        rules = (
            DummyBannedGroup,
            DummyHdOnly,
            DummyNoEpisodes,
        )

        @property
        def torrent_source_field(self):
            return self.options['source']

        setup_howto_template = (
            'This is just a no-op tracker for testing and demonstration.'
        )

        TrackerJobs = DummyTrackerJobs
        TrackerConfig = DummyTrackerConfig

        async def _login(self, tfa_otp=None):
            username, password = self.options['username'], self.options['password']
            _log.debug('%s: Logging in as %s (password=%s, OTP=%s)', self.name, username, password, tfa_otp)
            if self.options['tfa'] and not tfa_otp:
                raise errors.TfaRequired('I need a a second factor.')

            await asyncio.sleep(self.options['delay'])

            # Simulate wrong OTP.
            if tfa_otp and not all(c in '1234567890' for c in tfa_otp):
                raise errors.RequestError('Your OTP looks weird.')

            # Simulate wrong username/password combination.
            if self.options['password'] == self.options['username']:
                raise errors.RequestError('Your username and password are identical, dummy!')

            _log.debug('%s: Logged in as %s (password=%s, OTP=%s)', self.name, username, password, tfa_otp)

        async def confirm_logged_in(self):
            _log.debug('%s: Confirming logged in', self.name)

        async def _logout(self):
            _log.debug('%s: Logging out', self.name)
            await asyncio.sleep(self.options['delay'])
            # raise errors.RequestError('You shall not logout!')
            _log.debug('%s: Logged out', self.name)

        async def get_announce_url(self):
            if self.options['get_announce_from_website']:
                _log.debug('%s: Getting announce URL from website', self.name)
                await asyncio.sleep(1)
            else:
                _log.debug('%s: Getting announce URL from config file', self.name)
            return 'http://localhost:123/f1dd15718/announce'

        async def upload(self, tracker_jobs):
            if tracker_jobs.create_torrent_job.output:
                torrent_file = tracker_jobs.create_torrent_job.output[0]
            else:
                raise errors.RequestError('Torrent file was not created.')
            _log.debug('%s: Uploading %s', self.name, torrent_file)
            await asyncio.sleep(self.options['delay'])

            if self.options['get_torrent_from_website']:
                torrent_url = 'http://localhost:1234/my_altered_torrent.torrent'
                _log.debug('%s: Downloading %s', self.name, torrent_url)
                await tracker_jobs.create_torrent_job.download_torrent(torrent_url)

            return f'http://localhost/{os.path.basename(torrent_file)}'
