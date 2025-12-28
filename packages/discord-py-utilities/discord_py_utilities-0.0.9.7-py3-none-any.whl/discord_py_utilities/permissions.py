from typing import Any

import discord
from discord import CategoryChannel, DMChannel, ForumChannel, GroupChannel, Member, StageChannel, TextChannel, Thread, \
	User, \
	VoiceChannel
PERMISSIONS = [
	"add_reactions", "administrator", "attach_files", "ban_members", "change_nickname", "connect",
	"create_events", "create_expressions", "create_instant_invite", "create_polls", "create_private_threads",
	"create_public_threads", "deafen_members", "embed_links", "external_emojis", "external_stickers",
	"kick_members", "manage_channels", "manage_emojis", "manage_emojis_and_stickers", "manage_events",
	"manage_expressions", "manage_guild", "manage_messages", "manage_nicknames", "manage_permissions",
	"manage_roles", "manage_threads", "manage_webhooks", "mention_everyone", "moderate_members", "move_members",
	"mute_members", "priority_speaker", "read_message_history", "read_messages", "request_to_speak",
	"send_messages", "send_messages_in_threads", "send_polls", "send_tts_messages", "send_voice_messages",
	"speak", "stream", "use_application_commands", "use_embedded_activities", "use_external_apps",
	"use_external_emojis", "use_external_sounds", "use_external_stickers", "use_soundboard",
	"use_voice_activation", "value", "view_audit_log", "view_channel", "view_creator_monetization_analytics",
	"view_guild_insights"
]


def check_missing_channel_permissions(
		channel: User | Member | VoiceChannel | StageChannel | TextChannel | ForumChannel | CategoryChannel | Thread | DMChannel | GroupChannel | None,
		permissions: str | list) -> list :
	"""
	Check which permissions are missing for the bot in the specified channel.
	:param channel:
	:param permissions:
	:return:
	"""
	if isinstance(channel, discord.User) :
		return ["User not added"]

	if isinstance(permissions, str) :
		permissions = [permissions]
	bot_perms = channel.permissions_for(channel.guild.me)
	if permissions is None :
		return [perm for perm in PERMISSIONS if not getattr(bot_perms, perm)]
	return [perm for perm in permissions if not getattr(bot_perms, perm)]


def check_missing_guild_permissions(guild: discord.Guild, permissions: str | list[str]) -> None | list[str] :
	"""
	Check if the bot is missing the required permissions in the guild and returns a list with the missing permissions.
	:param guild:
	:param permissions:
	"""
	if isinstance(permissions, str) :
		permissions = [permissions]
	bot_perms = guild.me.guild_permissions
	return [perm for perm in permissions if not getattr(bot_perms, perm)]


def get_bot_permissions(guild: discord.Guild) -> discord.Permissions | dict :
	"""
	Get all the permissions of the bot in the guild.
	:param guild:
	"""
	bot_perms = guild.me.guild_permissions
	permissions = {
		name : getattr(bot_perms, name)
		for name in PERMISSIONS
	}

	return [key for key, value in permissions.items() if value is True]


def check_bot_channel_permissions(channel: discord.TextChannel,
                                  permissions: str | list[str] = None) -> list[str] :
	"""
	Check if the bot has the required permissions in the channel, if no permissions are specified, it will return all the permissions the bot has in the channel.
	:param channel:
	:param permissions:
	:return:

	"""
	if isinstance(permissions, str) :
		permissions = [permissions]
	bot_perms = channel.permissions_for(channel.guild.me)
	if permissions is None :
		return [perm for perm in PERMISSIONS if getattr(bot_perms, perm)]
	return [perm for perm in permissions if getattr(bot_perms, perm)]


def find_first_accessible_text_channel(guild: discord.Guild) -> discord.TextChannel | None :
	"""
	Finds the first text channel in a guild where the bot has basic access permissions.
	Returns None if no such channel is found.
	"""
	for channel in guild.text_channels :
		if not isinstance(channel, discord.TextChannel) :
			continue

		missing = check_missing_channel_permissions(channel, ["view_channel", "send_messages"])
		if not missing :
			return channel
	return None
