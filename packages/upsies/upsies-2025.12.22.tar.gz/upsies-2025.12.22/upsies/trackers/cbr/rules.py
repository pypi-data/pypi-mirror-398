from ... import errors
from .. import utils
from ..base import rules

import logging  # isort:skip
_log = logging.getLogger(__name__)


class CbrBannedGroup(rules.BannedGroup):
    # /wikis/28
    banned_groups = {
        '3LTON',
        '4yEo',
        'ADE',
        'AFG',
        'AniHLS',
        'AnimeRG',
        'AniURL',
        'AROMA',
        'ASM',
        'aXXo',
        'BLUDV',
        'CaNNIBal',
        'CHD',
        'CM8',
        'Comando',
        'CrEwSaDe',
        'd3g',
        'DeadFish',
        'DNL',
        'DragsterPS',
        'DRENAN',
        'ELiTE',
        'eSc',
        'FaNGDiNG0',
        'FGT',
        'Flights',
        'FRDS',
        'FUM',
        'HAiKU',
        'HD2DVD',
        'HDS',
        'HDTime',
        'Hi10',
        'Hiro360',
        'ION10',
        'iPlanet',
        'JIVE',
        'KiNGDOM',
        'Lapumia',
        'Leffe',
        'LEGi0N',
        'LOAD',
        'MACCAULAY',
        'MeGusta',
        'mHD',
        'mSD',
        'NhaNc3',
        'nHD',
        'nikt0',
        'NOIVTC',
        'nSD',
        'OFT',
        'Oj',
        'PiRaTeS',
        'PlaySD',
        'playXD',
        'PRODJi',
        'RAPiDCOWS',
        'RARBG',
        'RDN',
        'REsuRRecTioN',
        'RetroPeeps',
        'RMTeam',
        'S74Ll10n',
        'SANTi',
        'SicFoI',
        'SILVEIRATeam',
        'SPASM',
        'SPDVD',
        'STUTTERSHIT',
        'Telly',
        'TGx',
        'TM',
        'TRiToN',
        'UPiNSMOKE',
        'URANiME',
        'WAF',
        'x0r',
        'xRed',
        'XS',
        'YIFY',
        'ZKBL',
        'ZmN',
        'ZMNT',
    }


class CbrPortuguese(rules.TrackerRuleBase):
    """
    Check if has Portuguese audio or subtitles
    """

    async def _check(self):
        audio_languages = utils.mediainfo.audio.get_audio_languages(
            self.release_name.path,
            exclude_commentary=True,
        )
        subtitle_languages = utils.mediainfo.text.get_subtitles(self.release_name.path)

        _log.debug('Audio languages: %r', audio_languages)
        _log.debug('Subtitle languages: %r', subtitle_languages)

        valid_dub = any(
            language in ('pt', 'zx', 'un')
            for language in audio_languages
        )
        valid_sub = any(
            subtitle.language == 'pt'
            for subtitle in subtitle_languages
        )

        if not valid_dub and not valid_sub:
            raise errors.RuleBroken('Portuguese audio or subtitles is required')
