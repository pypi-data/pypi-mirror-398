"""
Upload images to image hosting service
"""

import functools

from .... import imagehosts, jobs, utils
from .base import CommandBase


class upload_images(CommandBase):
    """Upload images to image hosting service"""

    names = ('upload-images', 'ui')

    cli_arguments = {}

    subcommand_name = 'IMAGE_HOST'
    subcommands = {
        imagehost.name: {
            'description': imagehost.description,
            'cli': {
                # Default arguments for all image hosts
                'IMAGE': {
                    'nargs': '+',
                    'help': 'Path to image file',
                },
                ('--thumb-width', '-t'): {
                    'help': 'Thumbnail width in pixels',
                    'type': utils.argtypes.integer,
                    'default': None,
                },
                # Custom arguments defined by image host
                **imagehost.cli_arguments,
            },
        }
        for imagehost in imagehosts.imagehost_classes()
    }

    @functools.cached_property
    def imagehost_name(self):
        """Lower-case image host name"""
        return self.args.subcommand.lower()

    @functools.cached_property
    def imagehost_config(self):
        """
        Relevant section in image host configuration file combined with CLI
        arguments where CLI arguments take precedence unless their value is
        `None`
        """
        config = dict(self.config['imghosts'][self.imagehost_name])
        if self.args.thumb_width is not None:
            config['thumb_width'] = self.args.thumb_width
        return config

    @functools.cached_property
    def jobs(self):
        return (
            jobs.imagehost.ImagehostJob(
                home_directory=self.home_directory,
                cache_directory=self.cache_directory,
                ignore_cache=self.args.ignore_cache,
                image_paths=self.args.IMAGE,
                imagehosts=(
                    imagehosts.imagehost(
                        name=self.imagehost_name,
                        config=self.imagehost_config,
                    ),
                ),
            ),
        )
