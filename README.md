# thearstbot - thearst3rd's Twitch Bot

I thought it'd be fun to make a twitch bot, so here it is! It doesn't do much, I mostly just followed [tutorials online](https://dev.to/ninjabunny9000/let-s-make-a-twitch-bot-with-python-2nd8). It may or may not be active on [my twitch channel](https://twitch.tv/thearst3rd).

## Run instructions

Install [python3](https://www.python.org/downloads/), then install the requirements:

```
pip3 install -r requirements.txt
```

Create a `.env` file with the following details:

```
TMI_TOKEN=oauth:<your oauth token>
CLIENT_ID=<your client ID requested from twitch dev>
CHANNEL=<username of channel you want the bot to join>
```

Then, run the bot:

```
python3 bot.py
```

Ask me for help if none of this makes sense lol
