"""
Highlighting for :class:`job widgets <upsies.uis.tui.widgets.JobWidget>`
"""

from prompt_toolkit import styles

# ruff started thinking E241 was not needed here ("RUF100 [*] Unused `noqa` directive (non-enabled:
# `E241`)") for some reason, so we ignore RUF100.
# flake8: noqa: E241, RUF100

# Remove defaults
styles.defaults.PROMPT_TOOLKIT_STYLE.clear()
styles.defaults.WIDGETS_STYLE.clear()

# https://python-prompt-toolkit.readthedocs.io/en/master/pages/advanced_topics/styling.html

style = styles.Style([
    ('default',                       ''),
    ('label',                         'bold'),

    ('output',                        ''),
    ('warning',                       'fg:#fe0 bold'),
    ('error',                         'fg:#f60 bold'),

    ('info',                          'bg:#222 fg:#dd5'),
    ('info.readout',                  'bg:#244 bold'),
    ('info.progressbar',              ''),
    ('info.progressbar.progress',     'reverse'),

    ('dialog',                        'bg:#222 fg:#5dd'),
    ('dialog.label',                  'bg:#222 fg:#ccc'),
    ('dialog.text',                   ''),

    ('dialog.choice',                 ''),
    ('dialog.choice.focused',         'reverse'),

    ('dialog.search',                 'bg:default'),
    ('dialog.search.label',           'bold underline'),
    ('dialog.search.query',           'bg:#222'),
    ('dialog.search.info',            'bg:#222'),
    ('dialog.search.results',         'bg:#222'),
    ('dialog.search.results.focused', 'reverse'),
])
