import logging
import re

import discord
from discord.ext import commands

from .permissions import check_missing_channel_permissions


def extract_invite_code(invite_url: str) -> str | None :
	"""Extracts the invite code from a Discord invite URL."""
	match = re.search(r"(?:https?://)?(?:www\.)?discord(?:\.gg|app\.com/invite)/([a-zA-Z0-9-]+)", invite_url)
	return match.group(1) if match else invite_url


async def check_guild_invites(bot: commands.AutoShardedBot, guild: discord.Guild, current_invite=None) -> str :
	invite: None | discord.Invite = None

	if current_invite :
		try :
			invite_code = extract_invite_code(current_invite)
			invite = await bot.fetch_invite(invite_code)
			return invite.url
		except discord.HTTPException or discord.NotFound :
			logging.info(f"{guild.name}'s invite expired, creating a new one.")
		except ValueError:
			logging.info(f"{guild.name}'s has weird characters in invite code, {current_invite}")
	try :
		for channel in guild.channels :
			if len(check_missing_channel_permissions(channel, ["view_channel", "create_instant_invite"])) > 0 :
				continue
			try :
				invite: str = await create_invite(channel, reason=f"Missing Invite/Invalid invite, making a new one.")
			except discord.NotFound :
				continue
			return invite
	except discord.Forbidden :
		logging.info(f"No permission to create invites in {guild.name}")
	try :
		invite: discord.Invite = (await guild.invites())[0]
		return invite.url
	except discord.Forbidden :
		logging.info(f"No permission to fetch invites in {guild.name}")
		return "forbidden"
	except IndexError :
		logging.info(f"{guild.name} has no invites.")
		return "no invites available"
	except Exception as e :
		logging.error(f"Error creating invite: {e}")
		return "error creating invite"


async def create_invite(channel: discord.TextChannel, reason=None, max_age=604800) -> str :
	try :
		invite = await channel.create_invite(max_age=604800, reason=reason)
		return invite.url
	except discord.Forbidden :
		return 'No permission'
	except Exception as e :
		logging.warning(f"Error creating invite: {e}")
		return f'No permission/Error'
