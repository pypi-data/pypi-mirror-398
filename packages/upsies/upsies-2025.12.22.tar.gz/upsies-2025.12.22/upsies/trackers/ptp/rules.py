from ... import errors
from ..base import rules


class PtpBannedGroup(rules.BannedGroup):
    banned_groups = {
        'aXXo',
        'BMDRu',
        'BRrip',
        'CM8',
        'CrEwSaDe',
        'CTFOH',
        'd3g',
        'DNL',
        'FaNGDiNG0',
        'HD2DVD',
        'HDT',
        'HDTime',
        'ION10',
        'iPlanet',
        'KiNGDOM',
        'LAMA',
        'mHD',
        'mSD',
        'NhaNc3',
        'nHD',
        'nikt0',
        'nSD',
        'OFT',
        'PRODJi',
        'SANTi',
        'SasukeducK',
        'SPiRiT',
        'STUTTERSHIT',
        'ViSION',
        'VXT',
        'WAF',
        'WORLD',
        'x0r',
        'YIFY',
    }

    async def _check_custom(self):
        # No EVO encodes. WEB-DLs are fine.
        if (
                self.is_group('EVO')
                and 'WEB' not in self.release_name.source
        ):
            raise errors.BannedGroup('EVO', additional_info='No encodes, only WEB-DL')
