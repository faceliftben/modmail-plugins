from collections import defaultdict
from datetime import datetime, timezone

import discord
from discord.ext import commands

from core import checks
from core.models import PermissionLevel
from core.time import UserFriendlyTime


class TopSupporters(commands.Cog):
    """Richtet den Top-Unterstützer-Befehl in Modmail Discord ein"""
    def __init__(self, bot):
        self.bot = bot

    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.command()
    async def topsupporters(self, ctx, *, dt: UserFriendlyTime):
        """Ruft Top-Unterstützer für den angegebenen Zeitraum ab"""
        async with ctx.typing():
            date = discord.utils.utcnow() - (dt.dt - discord.utils.utcnow())

            logs = await self.bot.api.logs.find({"open": False}).to_list(None)
            logs = filter(lambda x: isinstance(x['closed_at'], str) and datetime.fromisoformat(x['closed_at']) > date, logs)

            supporters = defaultdict(int)

            for l in logs:
                supporters_involved = set()
                for x in l['messages']:
                    if x.get('type') in ('anonymous', 'thread_message') and x['author']['mod']:
                        supporters_involved.add(x['author']['id'])
                for s in supporters_involved:
                    supporters[s] += 1

            supporters_keys = sorted(supporters.keys(), key=lambda x: supporters[x], reverse=True)

            fmt = ''

            n = 1
            for k in supporters_keys:
                u = self.bot.get_user(int(k))
                if u:
                    fmt += f'**{n}.** `{u}` - {supporters[k]}\n'
                    n += 1

            em = discord.Embed(title='Aktive Supporter', description=fmt, timestamp=date, color=0x7588da)
            em.set_footer(text='seit')
            await ctx.send(embed=em)


async def setup(bot):
    await bot.add_cog(TopSupporters(bot))
