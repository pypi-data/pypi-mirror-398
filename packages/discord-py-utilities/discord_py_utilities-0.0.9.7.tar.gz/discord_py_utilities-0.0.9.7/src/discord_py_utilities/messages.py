import asyncio
import logging

import discord
from discord import CategoryChannel, DMChannel, ForumChannel, GroupChannel, Member, StageChannel, TextChannel, Thread, \
	User, \
	VoiceChannel
from discord.ext.commands.help import MISSING

from .exceptions import NoChannelException, NoPermissionException
from .permissions import check_missing_channel_permissions

MAX_LENGTH = 1800


async def handle_no_permission(channel: User | Member | VoiceChannel | StageChannel | TextChannel | ForumChannel | CategoryChannel | Thread | DMChannel | GroupChannel | None,
                               error_mode: str = 'error') :
	"""
	Handles no permission errors within the code based on error_modes: error, warn, ignore.
	Error: Raises NoPermissionException
	Warn: Logs a warning message and sends a message to the owner of the guild.
	Ignore: Does nothing.
	:param channel:
	:param error_mode:
	"""
	match error_mode.lower() :
		case 'error' :
			missing_perms = check_missing_channel_permissions(channel,
			                                                  ['view_channel', 'send_messages', 'embed_links',
			                                                   'attach_files'])
			raise NoPermissionException(required_perms=missing_perms, channel=channel)
		case 'warn' :
			missing_perms = check_missing_channel_permissions(channel,
			                                                  ['view_channel', 'send_messages', 'embed_links',
			                                                   'attach_files'])
			logging.warning(f"Missing permission to send message to {channel.name}")
			await channel.guild.owner.send(
				f"Missing permission to send message to {channel.name}. Check permissions: {', '.join(missing_perms)}", )
		case 'ignore' :
			logging.debug(f"Missing permission to send message to {channel.name}. Ignoring.")
		case _ :
			logging.debug(f"Missing valid error_mode, defaulting to error.")
			missing_perms = check_missing_channel_permissions(channel,
			                                                  ['view_channel', 'send_messages', 'embed_links', 'attach_files'])
			raise NoPermissionException(required_perms=missing_perms, channel=channel)


async def send_message(channel: User | Member | VoiceChannel | StageChannel | TextChannel | ForumChannel | CategoryChannel | Thread | DMChannel | GroupChannel | None, message: str = None, embed=None,
                       view=None, files=None, error_mode: str = 'error') -> discord.Message :
	"""Send a message to a channel, if there is no permission it will send an error message to the owner. Automatically handles messages longer than 2000 characters by splitting them into multiple messages.
	:param channel:
	:param message:
	:param embed:
	:param view:
	:param files:
	:param error_mode:
	:return:
	"""
	last_message = None
	if channel is None :
		raise NoChannelException
	try :
		length = 0
		if not message or len(message) < 1 :
			message = " "
		while length < len(message) :
			last_message = await channel.send(message[length :length + MAX_LENGTH], embed=embed, view=view, files=files)
			length += MAX_LENGTH
		else :
			return last_message
	except discord.errors.Forbidden :
		await handle_no_permission(channel, error_mode)


async def send_response(interaction: discord.Interaction, response, ephemeral=False, view=MISSING, embed=MISSING, error_mode = 'error') :
	"""Sends a response to an interaction. If the interaction is already responded, it will send a followup message.
	:param error_mode:
	:param interaction:
	:param response:
	:param ephemeral:
	:param view:
	:param embed:
	:return:
	"""
	try :
		if not response or len(response) < 1 :
			response = " "
		return await interaction.response.send_message(response, ephemeral=ephemeral, view=view, embed=embed)
	except discord.errors.Forbidden :
		await handle_no_permission(interaction.channel, error_mode=error_mode)
	except discord.errors.NotFound or discord.InteractionResponded :
		try :
			await interaction.followup.send(
				response,
				ephemeral=ephemeral,
				view=view,
				embed=embed,

			)
		except discord.errors.NotFound :
			await send_message(interaction.channel, response, view=view, embed=embed)


	except Exception :
		return await send_message(interaction.channel ,response, view=view, embed=embed)


async def await_message(interaction, message) -> discord.Message | bool :
	"""Wait for a message from the user that triggered the interaction. If the message is 'cancel', return False.
	:param interaction:
	:param message:
	:return:
	"""
	msg: discord.Message = await send_message(interaction.channel,
	                                          message)

	def check_message(m, interaction) :
		return m.author == interaction.user and m.channel == interaction.channel

	m = await interaction.client.wait_for('message', check=lambda m : check_message(m, interaction), timeout=600)
	await msg.delete()
	if m.content.lower() == "cancel" :
		return False
	return m


async def fetch_message_or_none(channel: discord.TextChannel | discord.DMChannel | discord.Thread,
                                id: int, wait = 0) -> discord.Message | None :
	"""
	Fetch a message from a channel. If the message is not found, return None. Wait for a specified amount of time before fetching the message; useful for fetching starting message of threads as they often have delays.
	:param wait:
	:return:
	:param channel:
	:param id:
	:return:
	"""
	try :
		await asyncio.sleep(wait)
		return await channel.fetch_message(id)
	except discord.errors.NotFound :
		return None


async def delete_message(message: discord.Message | discord.Thread) :
	"""
	Delete a message. If the message is not found, return None. If the message is not found, send a message to the channel.
	:param message:
	:return:
	"""
	try :
		await message.delete()
	except discord.errors.Forbidden :
		if isinstance(message, discord.Message) :
			await send_message(message.channel, f"Could not delete message {message.jump_url}")
			return
		await send_message(message, f"Could not delete message {message.jump_url}")
	except Exception as e :
		logging.error(
			f"Failed to delete {message} because {e}")

