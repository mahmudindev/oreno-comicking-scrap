import os
import dotenv
import logging

from .bot import Bot
from .bot_jikan import BotJikan

logging.basicConfig(level=logging.DEBUG)

def main():
    dotenv.load_dotenv()

    logger = logging.getLogger(__name__)
    note_file = open('bot.txt', 'a', encoding='utf-8')

    bot = Bot(
        os.getenv('COMICKING_SCRAP_BASE_COMICKING') or '',
        oauth_issuer=os.getenv('COMICKING_SCRAP_OAUTH_ISSUER') or '',
        oauth_client_id=os.getenv('COMICKING_SCRAP_OAUTH_CLIENT_ID') or '',
        oauth_client_secret=os.getenv('COMICKING_SCRAP_OAUTH_CLIENT_SECRET') or '',
        oauth_audience=os.getenv('COMICKING_SCRAP_OAUTH_AUDIENCE') or '',
        logger=logger,
        note_file=note_file
    )
    bot.load(True)

    bot_jikan = BotJikan(
        bot,
        logger=logger
    )
    bot_jikan.process(int(os.getenv('COMICKING_SCRAP_PROCESS_MAX_NEW_COMIC') or 1))

    note_file.close()
