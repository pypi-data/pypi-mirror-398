from ... import errors
from ..base import rules


class BhdHdOnly(rules.HdOnly):
    message = 'Not an HD release (ignore if there is no HD release available)'


class BhdBannedGroup(rules.BannedGroup):

    banned_groups = {
        '4K4U',
        'AOC',
        'BiTOR',
        'C4K',
        'CRUCiBLE',
        'd3g',
        'EASports',
        'FGT',  # Unless no other encode is available.
        'Flights',  # Existing uploads are grandfathered in as long as they do not break any rules
        'iVy',
        'MeGusta',
        'MezRips',
        'nikt0',
        'ProRes',
        'QxR',
        'RARBG',
        'ReaLHD',
        'SasukeducK',
        'Sicario',
        'SyncUP',
        'TEKNO3D',  # They have requested their torrents are not shared off site.
        'Telly',
        'tigole',
        'TOMMY',
        'WKS',
        'x0r',
        'YIFY',
    }

    async def _check_custom(self):
        # No iFT remuxes.
        if (
                self.is_group('iFT')
                and 'Remux' in self.release_name.source
        ):
            raise errors.BannedGroup('iFT', additional_info='No remuxes from iFT')

        # No EVO encodes. WEB-DLs are fine.
        if (
                self.is_group('EVO')
                and 'WEB' not in self.release_name.source
        ):
            raise errors.BannedGroup('EVO', additional_info='No encodes, only WEB-DL')
