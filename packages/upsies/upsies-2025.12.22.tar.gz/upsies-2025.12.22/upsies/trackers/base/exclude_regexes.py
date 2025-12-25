import os
import re

# Regular expressions are matched against file paths.

# Path separator must be escaped in case we're running on Windows.
sep = re.escape(os.sep)

checksums = r'\.(?i:sfv|md5)$'

extras = (
    r'(?i:'
    # Directory named "extras".
    rf'{sep}extras{sep}'
    r'|'
    # Anything with the word "extras" with another word in front of it. This
    # should exclude the show "Extras".
    rf'{sep}.+[\. ]extras[\. ]'
    r'|'
    # Numbered extras (e.g. "Foo.S01.Extra1.mkv", "Foo.S01.Extra.2.mkv", .etc)
    rf'{sep}.+[\. ]extra[\. ]?\d+[\.]'
    r')'
)

images = (
    r'(?i:'
    # Directory is not a DISC
    rf'^(?!.*{sep}(BDMV|VIDEO_TS){sep}).*'
    # Ends with image types
    r'\.(png|jpg|jpeg)$'
    r')'
)

nfo = r'\.(?i:nfo)$'

samples = (
    r'(?i:'
    # Sample directory
    rf'{sep}[!_0-]?sample{sep}'
    r'|'
    # Sample file name starts with release name
    rf'[^{sep}][\.\-_ ]sample\.mkv'
    r'|'
    # Sample file name ends with release name
    rf'{sep}sample[\!\-_].+\.mkv'
    r'|'
    # Sample file name starts with release name and ends with "sample-RLSGRP.mkv"
    r'[\.\-_!]?sample-[a-zA-Z0-9]+\.mkv'
    r'|'
    # Sample file name starts with "<characters that top-sort>sample"
    rf'{sep}[!#$%&*+\-\.]?sample\.mkv'
    r')'
)

subtitles = r'\.(?i:srt|idx|sub)$'

garbage = (
    f'{sep}(?:'
    + '|'.join((
        # Linux
        r'\.fuse_hidden\d+',     # Opened + removed file on FUSE
        rf'\.Trash{sep}.*',      # Deleted files
        rf'\.Trash-\d+{sep}.*',  # Deleted files

        # MacOS
        r'\.DS_Store',         # Folder options
        rf'\.Trashes{sep}.*',  # Deleted files

        # Windows
        r'desktop\.ini',  # Folder options
        r'Thumbs\.db',    # Thumbnails

        # Synology
        rf'@eaDir{sep}.*',
        r'.*@SynoEAStream',
        r'.*@SynoResource',

        # Other software
        r'.*\.miniso',    # DVDFab
        r'.*dvdid\.xml',  # AnyDVD

        # Usenet
        r'.*\.nzb',
        r'.*\.par2',

        # srrDB
        r'.*\.srr',
        r'.*\.srs',

        # Miscellaneous
        r'.*\.torrent',
    ))
    + ')$'
)
