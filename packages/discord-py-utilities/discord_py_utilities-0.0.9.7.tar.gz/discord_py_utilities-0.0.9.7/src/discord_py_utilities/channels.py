import logging

import discord


def create_channel(guild: discord.Guild, channel_name: str,
                   channel_type: discord.ChannelType = discord.ChannelType.text,
                   category: discord.CategoryChannel = None) :
	"""
	Create a channel in a given guild.
	:return:
	:param guild: The guild (server) where the channel will be created.
	:param channel_name: The name of the channel to be created.
	:param channel_type: The type of the channel (text or voice).
	:param category: The category under which the channel will be created (optional).
	:return: The created channel object.
	"""
	match channel_type :
		case discord.ChannelType.voice :
			# Creates voice channels
			return guild.create_voice_channel(name=channel_name, category=category)
		case discord.ChannelType.forum :
			# Creates forum channels
			return guild.create_forum(name=channel_name, category=category)
		case discord.ChannelType.stage_voice :
			# Creates stage channels
			return guild.create_stage_channel(name=channel_name, category=category)
		case _ :
			# Creates text channels and handles undefined channel types
			return guild.create_text_channel(name=channel_name, category=category)

def delete_channel(channel: discord.abc.GuildChannel, reason = "Deleted by bot") :
	"""
	Delete a channel.
	:param reason:
	:param channel: The channel to be deleted.
	:return: None
	"""
	try:
		return channel.delete(reason=reason)
	except discord.Forbidden:
		logging.error(f"Failed to delete channel {channel.name}({channel.id}): FORBIDDEN")
		return None


