
import discord
from discord.ext import commands

from core import checks
from core.checks import PermissionLevel


class ClaimThread(commands.Cog):
    """Ermöglicht es Unterstützern, einen Thread zu beanspruchen, indem sie einen Anspruch im Threadkanal senden"""
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.plugin_db.get_partition(self)
        check_reply.fail_msg = 'Dieser Thread wurde von einem anderen Benutzer beansprucht.'
        self.bot.get_command('reply').add_check(check_reply)
        self.bot.get_command('areply').add_check(check_reply)
        self.bot.get_command('fareply').add_check(check_reply)
        self.bot.get_command('freply').add_check(check_reply)

    @checks.has_permissions(PermissionLevel.SUPPORTER)
    @checks.thread_only()
    @commands.command()
    async def claim(self, ctx):
        thread = await self.db.find_one({'thread_id': str(ctx.thread.channel.id)})
        if thread is None:
            await self.db.insert_one({'thread_id': str(ctx.thread.channel.id), 'claimers': [str(ctx.author.id)]})
            await ctx.send("Ticket wurde übernommen")
        else:
            await ctx.send('Ticket ist bereits übernommen worden')

    @checks.has_permissions(PermissionLevel.SUPPORTER)
    @checks.thread_only()
    @commands.command()
    async def addclaim(self, ctx, *, member: discord.Member):
        """Fügt einen weiteren Benutzer zu den Ticket-Beanspruchern hinzu"""
        thread = await self.db.find_one({'thread_id': str(ctx.thread.channel.id)})
        if thread and str(ctx.author.id) in thread['claimers']:
            await self.db.find_one_and_update({'thread_id': str(ctx.thread.channel.id)}, {'$addToSet': {'claimers': str(member.id)}})
            await ctx.send('Zu Anspruchstellern hinzugefügt')

    @checks.has_permissions(PermissionLevel.SUPPORTER)
    @checks.thread_only()
    @commands.command()
    async def removeclaim(self, ctx, *, member: discord.Member):
        """Entfernt einen Benutzer aus den Ticket-Beanspruchern"""
        thread = await self.db.find_one({'thread_id': str(ctx.thread.channel.id)})
        if thread and str(ctx.author.id) in thread['claimers']:
            await self.db.find_one_and_update({'thread_id': str(ctx.thread.channel.id)}, {'$pull': {'claimers': str(member.id)}})
            await ctx.send('Von Anspruchstellern entfernt')

    @checks.has_permissions(PermissionLevel.SUPPORTER)
    @checks.thread_only()
    @commands.command()
    async def transferclaim(self, ctx, *, member: discord.Member):
        """Entfernt alle Benutzer von Anspruchstellern und gibt einem anderen Mitglied die gesamte Kontrolle über das Ticket"""
        thread = await self.db.find_one({'thread_id': str(ctx.thread.channel.id)})
        if thread and str(ctx.author.id) in thread['claimers']:
            await self.db.find_one_and_update({'thread_id': str(ctx.thread.channel.id)}, {'$set': {'claimers': [str(member.id)]}})
            await ctx.send('Zu Anspruchstellern hinzugefügt')

    @checks.has_permissions(PermissionLevel.MODERATOR)
    @checks.thread_only()
    @commands.command()
    async def overrideaddclaim(self, ctx, *, member: discord.Member):
        """Allow mods to bypass claim thread check in add"""
        thread = await self.db.find_one({'thread_id': str(ctx.thread.channel.id)})
        if thread:
            await self.db.find_one_and_update({'thread_id': str(ctx.thread.channel.id)}, {'$addToSet': {'claimers': str(member.id)}})
            await ctx.send('Added to claimers')

    @checks.has_permissions(PermissionLevel.MODERATOR)
    @checks.thread_only()
    @commands.command()
    async def overridereply(self, ctx, *, msg: str=""):
        """Erlaube Mods, die Anspruchs-Thread-Prüfung als Antwort zu umgehen"""
        await ctx.invoke(self.bot.get_command('reply'), msg=msg)


async def check_reply(ctx):
    thread = await ctx.bot.get_cog('ClaimThread').db.find_one({'thread_id': str(ctx.thread.channel.id)})
    if thread:
        return ctx.author.bot or str(ctx.author.id) in thread['claimers']
    return True


async def setup(bot):
    await bot.add_cog(ClaimThread(bot))
