import dotenv, os

import twilight_vk
from twilight_vk.framework.rules import TextRule

dotenv.load_dotenv()

bot = twilight_vk.TwilightVK(
    BOT_NAME=os.getenv("BOT_NAME"),
    ACCESS_TOKEN=os.getenv("BOT_ACCESS_TOKEN"),
    GROUP_ID=os.getenv("BOT_GROUP_ID")
)

@bot.on_event.message_new(TextRule(value=["привет", "hello"], ignore_case=True))
async def hello(event: dict):
    return "Hello world"

bot.start()