"""
Helper functions for generating BBcode
"""

from .. import utils


def screenshots_grid(screenshots, columns=2, horizontal_spacer='  ', vertical_spacer='\n'):
    """
    Return BBcode for thumbnailed screenshots in a grid layout

    :param screenshots: Sequence of :class:`~.imagehosts.common.UploadedImage` objects (URLs with a
        ``thumbnail_url`` attribute)

    :param int columns: How many columns to split screenshots into

        `columns` may also be a sequence of acceptable values to automatically find the best number
        of columns for the number of screenshots.

        For example, for 9 screenshots and columns=(2, 3, 4), the best number of columns would be 3,
        for 8 screenshots it would be 4, and for 2 screenshots it would be 2 columns.

    :param str horizontal_spacer: String between columns
    :param str vertical_spacer: String between rows

    :raise RuntimeError: if any screenshot doesn't have a thumbnail
    """
    if isinstance(columns, int):
        columns = (columns,)

    groups = utils.as_groups(
        screenshots,
        group_sizes=columns,
        default=None,
    )

    rows = []
    for screenshots in groups:
        cells = []
        for screenshot in screenshots:
            # `screenshot` is `None` at the end if the number of screenshots is not perfectly
            # divisible by `columns`.
            if screenshot is not None:
                if screenshot.thumbnail_url is None:
                    raise RuntimeError(f'No thumbnail for {screenshot}')
                cells.append(f'[url={screenshot}][img]{screenshot.thumbnail_url}[/img][/url]')

        # Join cells horizontally.
        rows.append(horizontal_spacer.join(cells))

    # Join rows vertically.
    return vertical_spacer.join(rows)
