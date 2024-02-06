# reportme
Telegram-bot for sending notification by HTTP-requests.

# Requirements
* Python 3.8

# What is this bot for?
This bot organize notifications via Telegram when only HTTP requests are available.

The user can create a personal message channel in this bot and get a secret key for it.

Later, when an HTTP request is made with the specified message and key, the user will receive this message from the bot

You can try the current example of a telegram bot based on this code here: [@reportme_bot](tg://resolve?domain=reportme_bot)

# How to use it

Let's say you have already set up a version of this bot on your server or are using a [public](tg://resolve?domain=reportme_bot) version.
1. Start chat with telegram bot
2. Create a new message channel with the command **/add channel_name**
3. You will receive an example of a link to send the message (with a secret key in it)
4. Open this link in the browser or make an HTTP request from anywhere and get a notification
5. You can stop notifications from any channel with the command **/stop KEY** (where KEY is the secret key of the channel to stop)

## Bot commands
**/help** — Show brief manual\
**/add** NAME — Add new stream with given name\
**/del** KEY — Delete stream\
**/list** — List all your streams (their names and keys)\
**/info** KEY — Get stream info (name, status, key and sample link)\
**/run** KEY — Activate stream\
**/stop** KEY — Stop stream

# How to setup bot
The first thing you should prepare environment and install all requirenments (requirements.txt). Then set all environment variables:
* REPORTME_BASE_URL — URL for access to service (e.g. `https://your-site.com`)
* REPORTME_DB_HOST — Host of your database
* REPORTME_DB_USER — Database user
* REPORTME_DB_PASSWORD — Database user password
* REPORTME_DB_DATABASE — Database
* REPORTME_BOT_TOKEN — Token for telegram bot received from [@BotFather](tg://resolve?domain=BotFather)
* REPORTME_WEBHOOK_PATH — (optional) Set if you want to process requests on the sublevel URL (e.g. "/qwe/" lead to URLs like `https://your-site.com/qwe/...`). The path must start and end with the '/'