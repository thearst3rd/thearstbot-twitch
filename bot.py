# Basic twitch bot

import os
import sqlite3
from twitchio.ext import commands
from twitchio.ext import pubsub
from dotenv import load_dotenv

PREFIX = "!"
DB_PATH = "storage.db"


class Bot(commands.Bot):
	def __init__(self):
		super().__init__(token = os.environ["TMI_TOKEN"], prefix=PREFIX, initial_channels=[os.environ["CHANNEL"]])
		self.db_con = sqlite3.connect(DB_PATH)
		self.db_cur = self.db_con.cursor()

		self.db_cur.execute("CREATE TABLE IF NOT EXISTS custom_commands(command TEXT, output_text TEXT, author TEXT)")
		self.db_cur.execute("CREATE TABLE IF NOT EXISTS channel_reward_messages(title TEXT, output_text TEXT)")
		print("Created database table")
		commands = self.db_cur.execute("SELECT count(*) FROM custom_commands").fetchone()
		print(f"{commands[0]} custom commands available")

	# Adds a custom command from a string
	async def add_custom_command(self, ctx, command_str, author):
		args = command_str.split(" ", 1)
		if len(args) < 2:
			await ctx.send("lmao plz supply 2 args")
			return
		command_name = args[0]
		command_text = args[1]

		if not command_name.isalnum():
			await ctx.send("lmao that command name is too funky")
			return

		if self.db_cur.execute("SELECT * FROM custom_commands WHERE command=?", [command_name]).fetchone() is not None \
					or self.get_command(command_name) is not None:
			await ctx.send("lmao that command already exists")
			return

		self.db_cur.execute("INSERT INTO custom_commands VALUES (?, ?, ?)", [command_name, command_text, author])
		self.db_con.commit()
		await ctx.send(f"Adding command: \"{PREFIX}{command_name}\" -> \"{command_text}\"")

	async def event_ready(self):
		print(f"Logged in as | {self.nick}")
		print(f"User id is | {self.user_id}")

		# This entire pubsub thing feels so janky... There simply must be a better way to do it
		if "PUBSUB_TOKEN" in os.environ and "PUBSUB_USER_ID" in os.environ:
			self.pubsub = pubsub.PubSubPool(self)
			topics = [
				pubsub.channel_points(os.environ["PUBSUB_TOKEN"])[int(os.environ["PUBSUB_USER_ID"])]
			]
			await self.pubsub.subscribe_topics(topics)

			# Can I put this function somewhere else LMAO
			@self.event()
			async def event_pubsub_channel_points(event: pubsub.PubSubChannelPointsMessage):
				reward_title = event.reward.title
				result = self.db_cur.execute("SELECT output_text FROM channel_reward_messages WHERE title=?", [reward_title]).fetchone()
				if result is not None:
					message = result[0]
					message = message.replace("%USER%", event.user.name)
					if event.input:
						message = message.replace("%INPUT%", event.input)
					await self.get_channel(os.environ["CHANNEL"]).send(message)

	async def event_message(self, message):
		if message.echo:
			return

		# I really want to do this with the add_command function and have no need for this event_message override, but
		# I cannot for the life of me figure out how to make "anonymous" coroutines (like, async lambda or something),
		# so I'm just manually handling the command here before passing to the command handler
		if message.content.startswith(PREFIX):
			first_token = message.content[len(PREFIX):].strip().split()[0]
			res = self.db_cur.execute("SELECT output_text FROM custom_commands WHERE command=?", [first_token]).fetchone()
			if res is not None:
				await message.channel.send(res[0])
				return

		await self.handle_commands(message)

	@commands.command()
	async def hello(self, ctx: commands.Context):
		# Basic hello world command, executed with "!hello". Reply hello to whoever made the command
		response = f"Hello {ctx.author.name}! "
		if ctx.author.is_broadcaster:
			response += "👑"
		else:
			if ctx.author.is_mod:
				response += "⚔"
			# Uncomment these once twitchio gets a new release
			#elif ctx.author.is_vip:
			#	response += "💎"
			if ctx.author.is_subscriber:
				response += "🤑"
		await ctx.send(response.strip())

	@commands.command()
	async def addcmd(self, ctx: commands.Context):
		# Lets moderators add custom text responses
		if not ctx.author.is_mod:
			await ctx.send("lmao nice try ur not a mod")
			return
		# Not sure if ctx.args is supposed to work but it seems like it doesn't...
		# I want the last arg to not get split anyway, so I do it myself
		args = ctx.message.content.split(" ", 1)
		if len(args) < 2:
			await ctx.send("lmao plz supply 2 args")
			return
		await self.add_custom_command(ctx, args[1], ctx.author.name)

	@commands.command()
	async def removecmd(self, ctx: commands.Context):
		if not ctx.author.is_mod:
			await ctx.send("lmao nice try ur not a mod")
			return

		args = ctx.message.content.split(" ", 1)
		if len(args) < 2:
			await ctx.send("lmao wut command")
			return

		command_name = args[1]
		if self.get_command(command_name) is not None:
			await ctx.send("lmao u cant delet this")
			return

		if self.db_cur.execute("SELECT * FROM custom_commands WHERE command=?", [command_name]).fetchone() is None:
			await ctx.send("lmao wut is that command")
			return

		self.db_cur.execute("DELETE FROM custom_commands WHERE command=?", [command_name])
		self.db_con.commit()
		await ctx.send(f"Deleted command \"{PREFIX}{command_name}\"")

	@commands.command()
	async def help(self, ctx: commands.Context):
		message = "Available commands:"
		for command in self.commands:
			if command not in ["addcmd", "removecmd"] or ctx.author.is_mod:
				message += f" {PREFIX}{command}"
		for command in self.db_cur.execute("SELECT command FROM custom_commands").fetchall():
			message += f" {PREFIX}{command[0]}"
		await ctx.send(message)


def main():
	load_dotenv()
	bot = Bot()
	bot.run()
	# bot.run() is blocking and will stop execution of any below code here until stopped or closed.


if __name__ == "__main__":
	main()
