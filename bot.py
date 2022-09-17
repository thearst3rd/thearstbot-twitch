# Basic twitch bot

import os
import sqlite3
from twitchio.ext import commands
from dotenv import load_dotenv

PREFIX = "!"
DB_PATH = "storage.db"


class Bot(commands.Bot):
	def __init__(self):
		super().__init__(token = os.environ["TMI_TOKEN"], prefix=PREFIX, initial_channels=[os.environ["CHANNEL"]])
		self.db_con = sqlite3.connect(DB_PATH)
		self.db_cur = self.db_con.cursor()

		if self.db_cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='custom_commands'").fetchone() == None:
			self.db_cur.execute("CREATE TABLE custom_commands(command, output_text)")
			print("Created database table")
		else:
			commands = self.db_cur.execute("SELECT * FROM custom_commands").fetchall()
			print(f"{len(commands)} custom commands available")

	async def event_ready(self):
		print(f"Logged in as | {self.nick}")
		print(f"User id is | {self.user_id}")

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
	async def addcommand(self, ctx: commands.Context):
		# Lets moderators add custom text responses
		if not ctx.author.is_mod:
			await ctx.send("lmao nice try ur not a mod")
			return
		# Not sure if ctx.args is supposed to work but it seems like it doesn't...
		# I want the last arg to not get split anyway, so I do it myself
		args = ctx.message.content.split(" ", 2)
		if len(args) < 3:
			await ctx.send("lmao plz supply 3 args")
			return
		command_name = args[1]
		command_text = args[2]

		if self.db_cur.execute("SELECT * FROM custom_commands WHERE command=?", [command_name]).fetchone() is not None \
					or self.get_command(command_name) is not None:
			await ctx.send("lmao that command already exists")
			return

		self.db_cur.execute("INSERT INTO custom_commands VALUES (?, ?)", [command_name, command_text])
		self.db_con.commit()
		await ctx.send(f"Adding command: \"{PREFIX}{command_name}\" -> \"{command_text}\"")

	@commands.command()
	async def removecommand(self, ctx: commands.Context):
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
