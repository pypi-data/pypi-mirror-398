from .. import constants, utils


class MainConfig(utils.config.SubsectionBase):
    cache_directory: utils.config.fields.string(
        default=constants.DEFAULT_CACHE_DIRECTORY,
        description=(
            'Where to store generated files.\n'
            'WARNING: Files in this directory are automatically deleted until the '
            'whole directory is smaller than <max_cache_size> bytes.'
        ),
    )

    max_cache_size: utils.config.fields.custom(
        cls=utils.types.Bytes,
        default='100 MB',
        description=(
            'Maximum size of cache directory. '
            'Units like "kB" and "MiB" are interpreted.'
        ),
    )

    check_for_prerelease: utils.config.fields.boolean(
        default='no',
        description=(
            'Whether to notify you of new prereleases. '
            '(The version number of prereleases ends with "alpha".) '
            'If you are already running a prerelease, you will always '
            'get notified of new prereleases, and this option has no effect.'
        ),
    )


class IdConfig(utils.config.SubsectionBase):
    show_poster: utils.config.fields.boolean(
        default='no',
        description=(
            'Whether to display a poster for easier identification.'
        ),
    )


class ScreenshotsConfig(utils.config.SubsectionBase):
    optimize: utils.config.fields.choice(
        default='default',
        options=utils.image.optimization_levels,
        case_sensitive=False,
        description=(
            'How much CPU resources to put into screenshot size optimization.\n'
            'Valid values are: ' + ', '.join(utils.image.optimization_levels)
        ),
    )

    tonemap: utils.config.fields.boolean(
        default='no',
        description=(
            'Whether to apply the tonemap filter to HDR screenshots.'
        ),
    )


class TorrentCreateConfig(utils.config.SubsectionBase):
    reuse_torrent_paths: utils.config.fields.custom(
        cls=utils.types.ListOf(str),
        default=(),
        description=(
            'List of directories to search for a *.torrent file to get piece hashes '
            'from when creating a torrent.'
        ),
    )


class ConfigConfig(utils.config.SectionBase):
    main: MainConfig = MainConfig()
    torrent_create: TorrentCreateConfig = TorrentCreateConfig()
    screenshots: ScreenshotsConfig = ScreenshotsConfig()
    id: IdConfig = IdConfig()
