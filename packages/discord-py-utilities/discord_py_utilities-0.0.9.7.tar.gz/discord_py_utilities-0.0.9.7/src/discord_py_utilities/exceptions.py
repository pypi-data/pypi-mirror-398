import discord

from .permissions import check_missing_channel_permissions, check_missing_guild_permissions


class NoPermissionException(Exception) :
	"""Raised when the bot does not have permission to send a message"""

	def __init__(self, required_perms: str | list, channel: discord.TextChannel = None, guild: discord.Guild = None,
	             message="Missing permission to send message: ", ) :
		if isinstance(channel, discord.TextChannel) :
			self.message = message + ", ".join(check_missing_channel_permissions(channel, required_perms))
			super().__init__(self.message)
			return
		if isinstance(guild, discord.Guild) :
			self.message = message + ", ".join(check_missing_guild_permissions(guild, required_perms))
			super().__init__(self.message)
			return
		self.message = message + "Unknown context (no channel or guild provided)."
		super().__init__(self.message)

	def __str__(self) :
		return self.message


class NoChannelException(Exception) :
	"""Raised when the server does not have a channel set to send a message"""

	def __init__(self, message="No channel set or does not exist, check the config or fill in the required arguments.") :
		self.message = message
