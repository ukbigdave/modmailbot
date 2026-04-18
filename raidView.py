import asyncio
from datetime import datetime
import discord


class JoinRaidButton(discord.ui.Button):
    def __init__(self, main_user: discord.Member, main_message: discord.Message, embed: discord.Embed, thread: discord.Thread, members: list, thread_message: discord.Message):
        super().__init__(label="Join Raid", style=discord.ButtonStyle.green)
        self.main_user = main_user
        self.main_message = main_message
        self.embed = embed
        self.members = members
        self.thread = thread
        self.thread_message = thread_message

    async def callback(self, interaction: discord.Interaction):
        if interaction.user == self.main_user:
            await interaction.response.send_message("You are the raid leader.", ephemeral=True)
            return

        if interaction.user.mention in self.embed.fields[1].value:
            await interaction.response.send_message("You have already joined this raid.", ephemeral=True)
            return
        field = self.embed.fields[1]
        split_field_name = field.name.split(" ")
        max_number_of_members = int(split_field_name[1].split("/")[1])
        number_of_members = len(self.members) + 1
        self.members.append(interaction.user)
        self.embed.add_field(name=f"Participants {number_of_members}/{max_number_of_members}",
                             value="\n".join([i.mention for i in self.members]), inline=False)
        self.embed.remove_field(1)
        await interaction.response.send_message("You have joined this raid.", ephemeral=True)

        if number_of_members == max_number_of_members:
            self.embed.add_field(name="THIS RAID LOBBY IS NOW FULL",
                                 value="\nPlease wait until a new raid is posted. Thank you for your patience!\n\n**Please wait until the host officially starts this raid.**", inline=False)
            self.embed.set_footer(text="This raid is full.")
            self.embed.color = 0xff0000
            self.view.stop()
            await self.main_message.edit(embed=self.embed, view=ReadyRaidView(self.main_user, self.main_message, self.embed, self.thread, self.members))
        else:
            if number_of_members == 1:
                self.thread = await self.main_message.channel.create_thread(name=f"{self.embed.title.replace('**', '')} - {self.embed.description.replace('**', '')}", invitable=False, type=discord.ChannelType.private_thread)
                embed = discord.Embed(
                    title="Raid Lobby", description="This is the raid lobby. Please wait until the raid leader starts the raid.", color=0x00ff00, timestamp=datetime.utcnow())
                thread_message = await self.thread.send(embed=embed)
                await thread_message.edit(view=ReadyRaidView(self.main_user, self.main_message, self.embed, self.thread, self.members, thread_message))
                await self.thread.add_user(self.main_user)
            self.view.stop()
            await self.main_message.edit(embed=self.embed, view=JoinReadyRaidView(self.main_user, self.main_message, self.embed, self.thread, self.members, self.thread_message))

        await self.thread.add_user(interaction.user)

class RaidView(discord.ui.View):
    def __init__(self, main_user: discord.Member, main_message: discord.Message, embed: discord.Embed, thread: discord.Thread, members: list, thread_message: discord.Message):
        super().__init__(timeout=300)
        self.embed = embed
        self.main_message = main_message
        self.thread = thread
        self.add_item(JoinRaidButton(main_user, main_message,
                      embed, thread, members, thread_message))

    async def on_timeout(self) -> None:
        self.embed.set_footer(text="This raid has expired.")
        self.embed.remove_field(1)
        self.embed.color = 0xff0000
        await self.main_message.edit(embed=self.embed, view=None)
        await self.thread.delete()

class StartRaidButton(discord.ui.Button):
    def __init__(self, main_user: discord.Member, main_message: discord.Message, embed: discord.Embed, thread: discord.Thread, members: list, thread_message: discord.Message):
        super().__init__(label="Start Raid", style=discord.ButtonStyle.primary)
        self.main_user = main_user
        self.main_message = main_message
        self.embed = embed
        self.members = members
        self.thread = thread
        self.thread_message = thread_message

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.main_user:
            await interaction.response.send_message("You are not the raid leader.", ephemeral=True)
            return
        self.embed.set_footer(text="This raid has started.")
        if len(self.embed.fields) == 3:
            field = self.embed.fields[2]
            value = field.value.split("\n\n")
            field.value = value[0] + "\n\n" + \
                "**Please join the raid lobby in a thread on this channel.**"
            self.embed.remove_field(2)
            self.embed.add_field(
                name=field.name, value=field.value, inline=False)
        else:
            self.embed.color = 0xff0000
            self.embed.add_field(name="**Please join the raid lobby in a thread on this channel.**",
                                 value="\u200b", inline=False)
        self.view.stop()
        await self.main_message.edit(embed=self.embed, view=None)
        thread_embed = discord.Embed(
            title="Raid Lobby", description="This is the raid lobby. The host has started the raid!", color=0xff0000, timestamp=datetime.utcnow())
        await self.thread_message.edit(embed=thread_embed, view=None)
        await interaction.response.send_message("You have started this raid.", ephemeral=True)

        await self.thread.send(f"**{self.main_user.mention} has started the raid.**\n\n{self.embed.fields[1].value}")
        await self.thread.send(', '.join([i.display_name for i in self.members]))
        await asyncio.sleep(60*30)
        await self.thread.delete()


class ReadyRaidView(discord.ui.View):
    def __init__(self, main_user: discord.Member, main_message: discord.Message, embed: discord.Embed, thread: discord.Thread, members: list, thread_message: discord.Message):
        super().__init__(timeout=300)
        self.main_message = main_message
        self.embed = embed
        self.thread = thread
        self.add_item(StartRaidButton(
            main_user, main_message, embed, thread, members, thread_message))

    async def on_timeout(self) -> None:
        self.embed.set_footer(text="This raid has expired.")
        self.embed.remove_field(1)
        self.embed.remove_field(2)
        self.embed.color = 0xff0000
        await self.main_message.edit(embed=self.embed, view=None)
        await self.thread.delete()


class JoinReadyRaidView(discord.ui.View):
    def __init__(self, main_user: discord.Member, main_message: discord.Message, embed: discord.Embed, thread: discord.Thread, members: list, thread_message: discord.Message):
        super().__init__(timeout=300)
        self.embed = embed
        self.main_message = main_message
        self.thread = thread
        self.add_item(JoinRaidButton(main_user, main_message,
                      embed, thread, members, thread_message))
        self.add_item(StartRaidButton(main_user, main_message,
                      embed, thread, members, thread_message))

    async def on_timeout(self) -> None:
        self.embed.set_footer(text="This raid has expired.")
        self.embed.remove_field(1)
        self.embed.color = 0xff0000
        await self.main_message.edit(embed=self.embed, view=None)
        await self.thread.delete()
