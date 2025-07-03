The bot is ran via webhooks, so to get it started, you have to set one up first.
I used the free plan at **ngrok.com**. The program uses environment variables, 
so make sure to make your own dotenw file to 
house the webhook link (variable "**WEBHOOK_URL**") and bot token 
(variable "**BOT_TOKEN**") if you want to deploy the base version bot.

Commands

**/start** - command list

**/set_filters** - course filter system

**/website** - link

_/register - has the same functionality as set filters for now_

test are included and have to be run with pytest and pytest-asyncio