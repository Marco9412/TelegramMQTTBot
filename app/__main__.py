import logging.handlers
import fileinput
import json.decoder

import TelegramMQTTBot

LOG_FILENAME = 'telegramMQTTBot.log'

if __name__ == '__main__':
    # parse input
    data = str()
    for line in fileinput.input():
        data = data + line

    settings = str()

    try:
        settings = json.loads(data)
    except json.decoder.JSONDecodeError as e:
        print('Invalid json file! Please check your settings!')
        print(e)
        exit(1)

    if not settings.get("logtostdout") == "true":
        handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=512000, backupCount=5)
        handler.setFormatter(logging.Formatter('%(levelname)s\t%(asctime)s\t%(message)s'))
        logging.getLogger().addHandler(handler)

    # set logs
    if settings.get("logging") == 'debug':
        logging.getLogger().setLevel(logging.DEBUG)
    elif settings.get("logging") == 'warn':
        logging.getLogger().setLevel(logging.WARN)
    elif settings.get("logging") == 'info':
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.DEBUG)  # default

    # start app
    tbot = TelegramMQTTBot.TelegramMQTTBot(settings)
    tbot.start()
    logging.info('Main: Ready!')
    tbot.idle()
    logging.info('Main: Quitting...')
    tbot.stop()
