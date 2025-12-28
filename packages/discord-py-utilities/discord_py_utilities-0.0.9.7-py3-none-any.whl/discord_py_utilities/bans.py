import logging

import discord

from .exceptions import NoPermissionException
from .messages import send_message


async def ban_member(bans_class, interaction, user, reason, days=1, inform=False) :
	"""

	:param bans_class:
	:param interaction:
	:param user:
	:param reason:
	:param days:
	:param inform:
	:return:
	"""
	try :
		await bans_class.add_ban(user.id, interaction.guild.id, reason, interaction.user.name)
		await interaction.guild.ban(user, reason=reason, delete_message_days=days)
		embed = discord.Embed(title=f"{user.name} ({user.id}) banned!", description=f"{reason}", color=discord.Color.red())
		embed.set_footer(text=f"Moderator: {interaction.user.name}, was the user informed? {'Yes' if inform else 'No'}")
		await send_message(interaction.channel, embed=embed)
		if not inform :
			return
		try :
			await user.send(f"You have been banned from {interaction.guild.name} for `{reason}`")
		except discord.errors.Forbidden :
			pass
		except Exception as e:
			logging.warning(f"could not dm user: {e}")

	except discord.Forbidden :
		error = f"Missing permission to ban user {user.name}({user.id}). Check permissions: ban_members or if the bot is higher in the hierarchy than the user."
		logging.error(error)
		await interaction.channel.send(error)
		raise NoPermissionException(required_perms=['ban_members'], guild=interaction.guild)


async def ban_user(interaction: discord.Interaction, user: discord.User, ban_type, reason_modal, ban_class, inform=True,
                   clean=False) :
	if interaction.guild is None :
		await send_message(interaction.channel, "This command can only be used in a server")
		return
	if user is None :
		await send_message(interaction.channel,
		                   "User not found, bot may not be able to fetch user or an invalid id was provided.")
	if user.id == interaction.user.id :
		await send_message(interaction.channel, "You can't ban yourself")
		return
	if user.id == interaction.client.user.id :
		await send_message(interaction.channel, "I can't ban myself")
		return
	if user.id == interaction.guild.owner_id :
		await send_message(interaction.channel, "You can't ban the owner of the server")
		return
	if ban_type == "[silent]" or ban_type == "[hidden]" :
		inform = False

	reason = f"{ban_type}{reason_modal}"

	await ban_member(ban_class, interaction, user, reason, days=1 if clean else 0, inform=inform)

async def dm_user(interaction, reason_modal, user) :
	try :
		await user.send(f"You have been banned from {interaction.guild.name} for `{reason_modal}`")
	except discord.errors.Forbidden :
		pass