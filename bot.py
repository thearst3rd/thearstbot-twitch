# Basic twitch bot

import os
from twitchio.ext import commands
from dotenv import load_dotenv


class Bot(commands.Bot):
	def __init__(self):
		super().__init__(token = os.environ["TMI_TOKEN"], prefix="!", initial_channels=[os.environ["CHANNEL"]])

	async def event_ready(self):
		print(f"Logged in as | {self.nick}")
		print(f"User id is | {self.user_id}")

	@commands.command()
	async def hello(self, ctx: commands.Context):
		# Basic hello world command, executed with "!hello". Reply hello to whoever made the command
		await ctx.send(f"Hello {ctx.author.name}!")


def main():
	load_dotenv()
	bot = Bot()
	bot.run()
	# bot.run() is blocking and will stop execution of any below code here until stopped or closed.


if __name__ == "__main__":
	main()
