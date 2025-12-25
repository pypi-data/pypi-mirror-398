"""
Standardized configuration and setup howto
"""

from ... import __project_name__, btclients, constants, utils


class Howto:
    def __init__(self, tracker_cls):
        self._tracker_cls = tracker_cls
        self._section = -1

    def join(self, *sections):
        return '\n'.join(sections).strip()

    @property
    def current_section(self):
        return self._section

    @property
    def next_section(self):
        self._section += 1
        return self._section

    @property
    def introduction(self):
        return utils.string.evaluate_fstring(
            self.join(
                (
                    '{howto.next_section}. How To Read This Howto\n'
                    '\n'
                    '   {howto.current_section}.1 Words in ALL_CAPS_AND_WITH_UNDERSCORES are placeholders.\n'
                    '   {howto.current_section}.2 Everything after "$" is a terminal command.\n'
                ),
                (
                    '{howto.next_section}. Configuration Defaults (Optional)\n'
                    '\n'
                    '    If you prefer, you can write all default values at once and then edit\n'
                    '    them in your favorite $EDITOR.\n'
                    '\n'
                    '    $ {executable} set --dump\n'
                    '    $ $EDITOR {tildify(constants.TRACKERS_FILEPATH)}\n'
                    '    $ $EDITOR {tildify(constants.IMGHOSTS_FILEPATH)}\n'
                    '    $ $EDITOR {tildify(constants.CLIENTS_FILEPATH)}\n'
                    '    $ $EDITOR {tildify(constants.CONFIG_FILEPATH)}\n'
                ),
            ),
            howto=self,
            executable=__project_name__,
            constants=constants,
            tildify=utils.fs.tildify_path,
        )

    @property
    def screenshots(self):
        def imagehost_names(tracker):
            return ', '.join(
                tracker.TrackerConfig.defaults['image_host'].item_type.options
            )

        return utils.string.evaluate_fstring(
            self.join(
                (
                    '{howto.next_section}. Screenshots (Optional)\n'
                    '\n'
                    '   {howto.current_section}.1 Specify how many screenshots to make.\n'
                    '       $ {executable} set trackers.{tracker.name}.screenshots_count NUMBER_OF_SCREENSHOTS\n'
                ),
                (
                    '   {howto.current_section}.2 Specify where screenshots should be uploaded to.\n'
                    '       $ {executable} set trackers.{tracker.name}.image_host IMAGE_HOST1,IMAGE_HOST2,...\n'
                    '       If IMAGE_HOST1 is down, try IMAGE_HOST2 and so on.\n'
                    '       Supported services: {imagehost_names(tracker)}\n'
                    '\n'
                    '   {howto.current_section}.3 Configure image hosting service.\n'
                    '       This usually means configuring an API key, which may not be necessary.\n'
                    '       $ {executable} upload-images IMAGE_HOST --help\n'
                ),
            ),
            howto=self,
            tracker=self._tracker_cls,
            executable=__project_name__,
            imagehost_names=imagehost_names,
        )

    @property
    def autoseed(self):
        return utils.string.evaluate_fstring(
            self.join(
                (
                    '{howto.next_section}. Add Uploaded Torrents To BitTorrent Client (Optional)\n'
                    '\n'
                    '   {howto.current_section}.1 Specify at least one client connection.\n'
                    '\n'
                    '       $ {executable} set clients.CLIENT_NAME.client CLIENT\n'
                    '       $ {executable} set clients.CLIENT_NAME.url URL\n'
                    '       $ {executable} set clients.CLIENT_NAME.username USERNAME\n'
                    '       $ {executable} set clients.CLIENT_NAME.password PASSWORD\n'
                    '\n'
                    '       CLIENT must be one of: {client_names}\n'
                    '\n'
                    '       CLIENT_NAME can by any string (within reason) that identifies the client,\n'
                    '       e.g. "nas" or "seedbox". If CLIENT_NAME and CLIENT are identical, you don\'t\n'
                    '       have to set clients.CLIENT_NAME.client.\n'
                    '\n'
                    '   {howto.current_section}.2 Specify client to which uploaded torrents should be added to.\n'
                    '       $ {executable} set trackers.{tracker.name}.add_to CLIENT_NAME\n'
                ),
                (
                    '{howto.next_section}. Copy Uploaded Torrents To Directory (Optional)\n'
                    '\n'
                    '   $ {executable} set trackers.{tracker.name}.copy_to /path/to/directory\n'
                ),
            ),
            howto=self,
            tracker=self._tracker_cls,
            executable=__project_name__,
            client_names=', '.join(btclients.client_names()),
        )

    @property
    def reuse_torrents(self):
        return utils.string.evaluate_fstring(
            self.join(
                (
                    '{howto.next_section}. Reuse Existing Torrents (Optional)\n'
                    '\n'
                    '    You can skip the hashing when creating a torrent by specifying directory paths\n'
                    '    that contain the torrents you are seeding. A matching torrent is found by searching\n'
                    '    each directory recursively for a torrent with the same size and file names. If such\n'
                    '    a torrent is found, a few pieces of each file are hashed to verify the match.\n'
                    '\n'
                    '    $ {executable} set config.torrent-create.reuse_torrent_paths TORRENT_DIRECTORY1 TORRENT_DIRECTORY2 ...\n'
                ),
            ),
            howto=self,
            executable=__project_name__,
        )

    @property
    def upload(self):
        return utils.string.evaluate_fstring(
            self.join(
                (
                    '{howto.next_section}. Upload\n'
                    '\n'
                    '   $ {executable} submit {tracker.name} --help\n'
                    '   $ {executable} submit {tracker.name} /path/to/content\n'
                ),
            ),
            howto=self,
            tracker=self._tracker_cls,
            executable=__project_name__,
        )
