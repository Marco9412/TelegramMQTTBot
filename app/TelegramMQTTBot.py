import logging
import emoji
import telegrambot
import mqttConn
import re


class TelegramMQTTBot(object):
    @staticmethod
    def quit_error(msg):
        logging.critical(msg)
        exit(1)

    def __init__(self, settings):
        logging.info('TelegramMQTTBot.__init__()')
        # TelegramMQTTBot.check_settings(settings)
        self._emoji_re = re.compile('.*:.*:.*')  # maybe fix TODO
        self._mqtt = mqttConn.MqttConnection(settings["mqtt"], self._build_topic_list(settings))
        self._telegram = telegrambot.Telegrambot(settings["token"], settings["users"])
        self._strings = settings["strings"]
        self._menus = settings["menus"]
        self._actions = settings["actions"]
        self._status = settings["status"]
        self._check_strings()
        self._substitute_strings_in_menus()
        self._substitute_strings_in_actions()
        self._substitute_strings_in_statuses()
        self._parse_menus()
        self._parse_actions()
        self._parse_status()
        self._add_help_command()

    def _str_has_emoji(self, string):
        return self._emoji_re.match(string)

    def _fix_str(self, string):
        return emoji.emojize(string, use_aliases=True) if self._str_has_emoji(string) else string

    @staticmethod
    def _build_topic_list(settings):
        topics = set()
        for status in settings["status"]:
            topics.add(status["topic"])
        return topics

    def _check_strings(self):
        for key in self._strings.keys():
            self._strings[key] = self._fix_str(self._strings[key])

    def _substitute_strings_in_menus(self):
        # Substitute known strings in menus definitions
        for i in range(0, len(self._menus)):
            for j in range(0, len(self._menus[i]["triggers"])):
                trigger = self._menus[i]["triggers"][j]
                if trigger in self._strings:
                    self._menus[i]["triggers"].remove(trigger)
                    self._menus[i]["triggers"].append(self._strings[trigger])

            if self._menus[i]["text"] in self._strings:
                self._menus[i]["text"] = self._strings[self._menus[i]["text"]]
            self._menus[i]["text"] = self._fix_str(self._menus[i]["text"])

            if self._menus[i]["help"] in self._strings:
                self._menus[i]["help"] = self._strings[self._menus[i]["help"]]
            self._menus[i]["help"] = self._fix_str(self._menus[i]["help"])

            mark = self._menus[i].get("markup")
            if mark:
                for j in range(0, len(mark)):  # rows
                    for k in range(0, len(mark[j])):  # cols
                        if mark[j][k] in self._strings:
                            mark[j][k] = self._strings[mark[j][k]]
                        mark[j][k] = self._fix_str(mark[j][k])
                self._menus[i]["markup"] = mark

    def _parse_menus(self):
        for menu in self._menus:
            for trigger in menu["triggers"]:
                if trigger[0] == '/':
                    self._telegram.add_command_callback(
                        trigger[1:],
                        self._prepare_lambda_change_menu(menu, trigger),
                        restrict=True if menu.get("restrict") else False
                    )
                else:
                    self._telegram.add_message_callback(
                        trigger,
                        self._prepare_lambda_change_menu(menu, trigger),
                        restrict=True if menu.get("restrict") else False)
                    # TODO add contains emoji parameter?

    def _substitute_strings_in_actions(self):
        for i in range(0, len(self._actions)):
            for j in range(0, len(self._actions[i]["triggers"])):
                trigger = self._actions[i]["triggers"][j]
                if trigger in self._strings:
                    self._actions[i]["triggers"].remove(trigger)
                    self._actions[i]["triggers"].append(self._strings[trigger])

            if self._actions[i]["textOk"] in self._strings:
                self._actions[i]["textOk"] = self._strings[self._actions[i]["textOk"]]
            self._actions[i]["textOk"] = self._fix_str(self._actions[i]["textOk"])

            if self._actions[i]["textErr"] in self._strings:
                self._actions[i]["textErr"] = self._strings[self._actions[i]["textErr"]]
            self._actions[i]["textErr"] = self._fix_str(self._actions[i]["textErr"])

            if self._actions[i]["help"] in self._strings:
                self._actions[i]["help"] = self._strings[self._actions[i]["help"]]
            self._actions[i]["help"] = self._fix_str(self._actions[i]["help"])

            mark = self._actions[i].get("markupOk")
            if mark:
                for j in range(0, len(mark)):  # rows
                    for k in range(0, len(mark[j])):  # cols
                        if mark[j][k] in self._strings:
                            mark[j][k] = self._strings[mark[j][k]]
                        mark[j][k] = self._fix_str(mark[j][k])
                self._actions[i]["markupOk"] = mark

            mark = self._actions[i].get("markupErr")
            if mark:
                for j in range(0, len(mark)):  # rows
                    for k in range(0, len(mark[j])):  # cols
                        if mark[j][k] in self._strings:
                            mark[j][k] = self._strings[mark[j][k]]
                        mark[j][k] = self._fix_str(mark[j][k])
                self._actions[i]["markupErr"] = mark

            for j in range(0, len(self._actions[i]["publish"])):
                if self._actions[i]["publish"][j]["message"] in self._strings:
                    self._actions[i]["publish"][j]["message"] = self._strings[self._actions[i]["publish"][j]["message"]]
                self._actions[i]["publish"][j]["message"] = self._fix_str(self._actions[i]["publish"][j]["message"])

    def _parse_actions(self):
        for action in self._actions:
            for trigger in action["triggers"]:
                if trigger[0] == '/':
                    self._telegram.add_command_callback(
                        trigger[1:],
                        self._prepare_lambda_publish(action, trigger),
                        restrict=True if action.get("restrict") else False
                    )
                else:
                    self._telegram.add_message_callback(
                        trigger,
                        self._prepare_lambda_publish(action, trigger),
                        restrict=True if action.get("restrict") else False)

    def _substitute_strings_in_statuses(self):
        for i in range(0, len(self._status)):
            for j in range(0, len(self._status[i]["triggers"])):
                trigger = self._status[i]["triggers"][j]
                if trigger in self._strings:
                    self._status[i]["triggers"].remove(trigger)
                    self._status[i]["triggers"].append(self._strings[trigger])

            if self._status[i]["textErr"] in self._strings:
                self._status[i]["textErr"] = self._strings[self._status[i]["textErr"]]
            self._status[i]["textErr"] = self._fix_str(self._status[i]["textErr"])

            if self._status[i]["help"] in self._strings:
                self._status[i]["help"] = self._strings[self._status[i]["help"]]
            self._status[i]["help"] = self._fix_str(self._status[i]["help"])

            for key in self._status[i]["text"].keys():
                if self._status[i]["text"][key] in self._strings:
                    self._status[i]["text"][key] = self._strings[self._status[i]["text"][key]]
                self._status[i]["text"][key] = self._fix_str(self._status[i]["text"][key])

    def _parse_status(self):
        for stat in self._status:
            for trigger in stat["triggers"]:
                if trigger[0] == '/':
                    self._telegram.add_command_callback(
                        trigger[1:],
                        self._prepare_lambda_status(stat, trigger),
                        restrict=True if stat.get("restrict") else False
                    )
                else:
                    self._telegram.add_message_callback(
                        trigger,
                        self._prepare_lambda_status(stat, trigger),
                        restrict=True if stat.get("restrict") else False)

    def _prepare_lambda_publish(self, action, trigger):
        la = (lambda ac: lambda bot, update: self._publish_function(ac, bot, update))(action)
        la.__name__ = trigger
        return la

    def _publish_function(self, action, bot, update):
        res = True
        for item in action["publish"]:
            res = res and self._mqtt.raw_publish(item["topic"], item["message"])
        self._telegram.send_message(
            self._telegram.get_user_id_from_update(update),
            self._fix_str(action["textOk"] if res else action["textErr"]),
            self._telegram.get_markup_keyboard_for(
                action["markupOk"] if res else action["markupErr"]
            )
        )

    def _prepare_lambda_change_menu(self, menu, trigger):
        la = (lambda m: lambda bot, update: self._change_menu_function(m, bot, update))(menu)
        la.__name__ = trigger
        return la

    def _change_menu_function(self, menu, bot, update):
        self._telegram.send_message(
            self._telegram.get_user_id_from_update(update),
            self._fix_str(menu["text"]),
            self._telegram.get_markup_keyboard_for(menu["markup"])
        )

    def _prepare_lambda_status(self, stat, trigger):
        la = (lambda st: lambda bot, update: self._status_function(st, bot, update))(stat)
        la.__name__ = trigger
        return la

    def _status_function(self, stat, bot, update):
        value = self._mqtt.get_message(stat["topic"])
        if value:
            for key in stat["text"].keys():
                if re.match(key, value):
                    self._telegram.send_message(
                        self._telegram.get_user_id_from_update(update),
                        self._fix_str(stat["text"][key])  # missing markup
                    )
                    return
        # error case
        self._telegram.send_message(
            self._telegram.get_user_id_from_update(update),
            self._fix_str(stat["textErr"])
        )

    def _add_help_command(self):
        self._help_str = 'Help:\n\nMenus:\n'
        for menu in self._menus:
            for trigger in menu["triggers"]:
                self._help_str = self._help_str + " - " + trigger + ": " + menu["help"] + '\n'
        self._help_str = self._help_str + '\nActions:\n'
        for action in self._actions:
            for trigger in action["triggers"]:
                self._help_str = self._help_str + " - " + trigger + ": " + action["help"] + '\n'
        self._help_str = self._help_str + '\nStatus:\n'
        for stat in self._status:
            for trigger in stat["triggers"]:
                self._help_str = self._help_str + " - " + trigger + ": " + stat["help"] + '\n'

        la = lambda bot, update: self._telegram.send_message(
            self._telegram.get_user_id_from_update(update),
            self._help_str
        )
        la.__name__ = 'help'

        self._telegram.add_command_callback(
            "help",
            la,
            restrict=True
        )

    def start(self):
        self._mqtt.connect()
        self._telegram.start_polling()

    def idle(self):
        self._telegram.idle()

    def stop(self):
        self._telegram.stop_polling()
        self._mqtt.disconnect()
