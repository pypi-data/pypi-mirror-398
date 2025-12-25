import re

from ... import errors, utils
from ..base import rules


class MtvBannedGroup(rules.BannedGroup):
    banned_groups = {
        '3LTON',
        '[Oj]',
        'aXXo',
        'BDP',
        'BRrip',
        'CM8',
        'CMCT',
        'CrEwSaDe',
        'DeadFish',
        'DNL',
        'ELiTE',
        'FaNGDiNG0',
        'FRDS',
        'FUM',
        'h65',
        'HD2DVD',
        'HDTime',
        'ION10',
        'iPlanet',
        'JIVE',
        'KiNGDOM',
        'Leffe',
        'LOAD',
        'mHD',
        'mRS',
        'mSD',
        'NhaNc3',
        'nHD',
        'nikt0',
        'nSD',
        'PandaRG',
        'PRODJi',
        'QxR',
        'RARBG',
        'RDN',
        'SANTi',
        'STUTTERSHIT',
        'TERMiNAL',
        'TM',
        'WAF',
        'x0r',
        'XS',
        'YIFY',
        'ZKBL',
        'ZmN',
    }

    async def _check_custom(self):
        # No EVO encodes. WEB-DLs are fine.
        if (
                self.is_group('EVO')
                and 'WEB' not in self.release_name.source
        ):
            raise errors.BannedGroup('EVO', additional_info='No encodes, only WEB-DL (Rule 2.2.1)')

        # No XviD encodes from ViSiON.
        if (
                self.is_group('ViSiON')
                and 'XviD' in self.release_name.video_format
        ):
            raise errors.BannedGroup('ViSiON', additional_info='No XviD encodes')


class MtvBannedContainerFormat(rules.TrackerRuleBase):
    _banned_file_extensions = {
        '3ivx',
        'asf',
        'f4v',
        'flv',
        'mov',
        'ogg',
        'qt',
        'rm',
        'rmv',
        'wmv',
    }

    async def _check(self):
        for file in utils.fs.file_list(self.release_name.path):
            file_extension = utils.fs.file_extension(file)
            if file_extension.casefold() in self._banned_file_extensions:
                raise errors.RuleBroken(f'Banned container format: {file_extension}: {file}')


class MtvHevcUhdOnly(rules.TrackerRuleBase):
    """HEVC (H.265) is only allowed for UHD (2160p), except for some anime groups"""

    _exempt_groups = {
        'AC',
        'Aergia',
        'ARC',
        'Arid',
        'Baws',
        'Chihiro',
        'Commie',
        'Crow',
        'CsS',
        'Dae',
        'Datte13',
        'Drag',
        'FLE',
        'GJM',
        'GJM-Kaleido',
        'hchcsen',
        'iKaos',
        'JySzE',
        'Kaleido-Subs',
        'Legion',
        'LostYears',
        'MTBB',
        'Netaro',
        'Noyr',
        'Okay-Subs',
        'OZR',
        'Reza',
        'sam',
        'Spirale',
        'Thighs',
        'TTGA',
        'UDF',
        'UQW',
        'Vanilla',
        'WSE',
    }

    async def _check(self):
        is_h265 = bool(re.search(r'(?:(?:H\.|x)265|HEVC)', self.release_name.video_format))
        resolution = utils.mediainfo.video.get_resolution_int(self.release_name.path)

        # H.265 is always OK for 2160p.
        if is_h265 and resolution < 2160:
            release_name_group = self.release_name.group.casefold()
            group_is_exempt = any(
                group.casefold() == release_name_group
                for group in self._exempt_groups
            )

            # For all non-exempt groups, H.265 is only allowed for UHD.
            if not group_is_exempt:
                raise errors.RuleBroken('HEVC is only allowed for UHD')

            # For some groups, H.265 is allowed, but only for HD.
            elif resolution < 720:
                raise errors.RuleBroken('HEVC is only allowed for HD')
