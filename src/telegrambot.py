import telegram
import telegram.ext
import logging
import functools
import emoji


class TextBaseFilter(telegram.ext.BaseFilter):
    def __init__(self, text):
        self._text = text

    def filter(self, message):
        return message.text == self._text


class EmojiTextBaseFilter(telegram.ext.BaseFilter):
    def __init__(self, text):
        self._text = text

    def filter(self, message):
        return emoji.demojize(message.text) == self._text


class Telegrambot(object):

    def __init__(self, token, users):
        self._token = token
        self._parse_users(users)
        self._telegram_bot = telegram.Bot(token=self._token)
        self._telegram_updater = telegram.ext.Updater(token=self._token)
        self._telegram_dispatcher = self._telegram_updater.dispatcher
        self._error_callback_added = False
        logging.debug('Telegrambot.init()')

    def _parse_users(self, users):
        self._admins = set()
        self._user_map = dict()
        self._loggers = set()
        for user in users:
            self._user_map[user["id"]] = user["name"]
            if user.get("authorized"):
                self._admins.add(user["id"])
            if user.get("send_logs"):
                self._loggers.add(user["id"])

    def __del__(self):
        self.stop_polling()
        # logging.debug('Telegrambot.__del__()')

    def start_polling(self, add_error_callback=True):
        if add_error_callback and not self._error_callback_added:
            self._telegram_dispatcher.add_handler(
                telegram.ext.MessageHandler(telegram.ext.Filters.command, self._restricted_log(self._unknown_cmd_callback)))
            self._error_callback_added = True
        self._telegram_updater.start_polling()
        logging.debug('Telegrambot.start_polling()')

    def stop_polling(self):
        # logging.debug('Telegrambot.stop_polling()')
        self._telegram_updater.stop()

    def idle(self):
        self._telegram_updater.idle()

    def send_message(self, to, text, markup=None):
        try:
            self._telegram_bot.send_message(chat_id=to, text=text, reply_markup=markup)
            logging.info('Telegrambot.send_message(): message sent to %s.' % str(to))
            return True
        except telegram.TelegramError as err:
            logging.error('Telegrambot.send_message(): error %s' % err.message)
            return False

    def _log_message(self, text, user_who_triggers=None):
        if self._loggers and isinstance(text, str):
            for logger in self._loggers:
                if user_who_triggers != logger: # do not send log message to the logger who triggered the action
                    self.send_message(logger, 'Log message:\n%s' % text)

    def add_message_callback(self, message, function, restrict=False, contains_emoji=False):
        """
        Adds a callback to the message 'message'!
        The function must have 2 parameters (bot, update).
        If pass_args is True a third parameter is needed.
        If restrict is true the command will be available only to admin users.
        :param command_string:
        :param function:
        :param pass_args:
        :return:
        """
        self._telegram_dispatcher.add_handler(
            telegram.ext.MessageHandler(EmojiTextBaseFilter(message) if contains_emoji else TextBaseFilter(message),
                                        self._restricted_log(function) if restrict else self._logging_fun(function)))
        logging.info('Telegrambot.add_message_callback(): added callback to message %s.' % message)

    def add_command_callback(self, command_string, function, pass_args=False, restrict=False):
        """
        Adds a callback to the command '/command_string' (mustn't contain the /)!
        The function must have 2 parameters (bot, update).
        If pass_args is True a third parameter is needed.
        If restrict is true the command will be available only to admin users.
        :param command_string: 
        :param function: 
        :param pass_args: 
        :return: 
        """
        self._telegram_dispatcher.add_handler(
            telegram.ext.CommandHandler(command_string,
                                        self._restricted_log(function) if restrict else self._logging_fun(function),
                                        pass_args=pass_args))
        logging.info('Telegrambot.add_command_callback(): added callback to command %s.' % command_string)

    @staticmethod
    def get_markup_keyboard_for(messages):
        return telegram.replykeyboardmarkup.ReplyKeyboardMarkup(messages)

    @staticmethod
    def get_user_id_from_update(update):
        # extract user_id from arbitrary update
        try:
            user_id = update.message.from_user.id
        except (NameError, AttributeError):
            try:
                user_id = update.inline_query.from_user.id
            except (NameError, AttributeError):
                try:
                    user_id = update.chosen_inline_result.from_user.id
                except (NameError, AttributeError):
                    try:
                        user_id = update.callback_query.from_user.id
                    except (NameError, AttributeError):
                        logging.error("No user_id available in update.")
                        return None
        return user_id

    @staticmethod
    def get_user_name_from_update(update):
        # extract user_id from arbitrary update
        try:
            user = update.message.from_user
        except (NameError, AttributeError):
            try:
                user = update.inline_query.from_user
            except (NameError, AttributeError):
                try:
                    user = update.chosen_inline_result.from_user
                except (NameError, AttributeError):
                    try:
                        user = update.callback_query.from_user
                    except (NameError, AttributeError):
                        logging.error("No user_id available in update.")
                        return None
        return user.name

    def _restricted_log(self, func):
        @functools.wraps(func)
        def wrapped(bot, update, *args, **kwargs):
            user_id = Telegrambot.get_user_id_from_update(update)
            user_name = Telegrambot.get_user_name_from_update(update)
            if user_id not in self._admins:
                logging.warning('Telegrambot._restricted_log: unauthorized access denied for %s in %s.' %
                                (user_name, func.__name__))
                self._log_message('Unauthorized user %d tried to call function %s.' % (user_id, func.__name__), user_id)
                # bot.send_message(chat_id=user_id, text='Unauthorized')
                return

            logging.info('Telegrambot._restricted_log: user %s calling %s' % (user_name, func.__name__))
            self._log_message('user %s calling %s' % (user_name, func.__name__), user_id)
            return func(bot, update)

        return wrapped

    def _logging_fun(self, func):
        @functools.wraps(func)
        def wrapped(bot, update, *args, **kwargs):
            user_id = Telegrambot.get_user_id_from_update(update)
            user_name = Telegrambot.get_user_name_from_update(update)
            logging.info('Telegrambot._logging_fun: user %s calling %s' % (user_name, func.__name__))
            self._log_message('user %s calling %s' % (user_name, func.__name__), user_id)
            return func(bot, update)

        return wrapped

    def _unknown_cmd_callback(self, bot, update):
        logging.debug('Telegrambot:unknown_cmd_callback()')
        self.send_message(update.message.chat_id, "Sorry, wrong command!")
