from ... import errors
from ..base import rules


class UhdHdOnly(rules.HdOnly):
    pass


class UhdNoEnglishDubs(rules.TrackerRuleBase):
    """Check if Dual Audio release"""

    async def _check(self):
        if self.release_name.has_dual_audio:
            raise errors.RuleBroken('No English dubs except for animated content')
