import random
from tools.keyboards import (
    Keyboard,
    Callback,
    ButtonColor
)
from db import db
import config
from .base import BaseAction


# ------------------------------------------------------------------------
class NotMessageOwnerAction(BaseAction):
    """Action that denies force
    unless it belongs to the author
    of the message with keyboard.
    """
    NAME = "not_msg_owner"

    async def _handle(self, event: dict, kwargs) -> bool:
        snackbar_message = "⚠️ Отказано в доступе."

        self.snackbar(event, snackbar_message)

        return False



# ------------------------------------------------------------------------
class CancelAction(BaseAction):
    """Cancels the command, closes the menu,
    and deletes the message.
    """
    NAME = "cancel_command"

    async def _handle(self, event: dict, kwargs) -> bool:
        self.api.messages.delete(
            peer_id=event.get("peer_id"),
            cmids=event.get("cmid"),
            delete_for_all=1
        )

        snackbar_message = "❗Отмена команды."

        self.snackbar(event, snackbar_message)

        return True



# ------------------------------------------------------------------------
class MarkAction(BaseAction):
    """Creates a "chat" mark and stores
    data about it in the database.
    """
    NAME = "set_mark"

    async def _handle(self, event: dict, kwargs) -> bool:
        fields = ("conv_mark",)
        mark = db.execute.select(
            schema="toaster",
            table="conversations",
            fields=fields,
            conv_id=event.get("peer_id")
        )
        already_marked = bool(mark)

        payload = event.get("payload")
        mark = payload.get("mark")

        if not already_marked:

            db.execute.insert(
                schema="toaster",
                table="conversations",
                conv_id=event.get("peer_id"),
                conv_name=event.get("peer_name"),
                conv_mark=mark
            )

            snackbar_message = f"📝 Беседа помечена как \"{mark}\"."

        else:
            snackbar_message = f"❗Беседа уже имеет метку \"{mark}\"."

        self.snackbar(event, snackbar_message)

        return True



class UpdateConvDataAction(BaseAction):
    """Updates the data of a conversation
    that already has a label. First of all,
    it is necessary for the correct display
    of logs when changing the name of the
    conversation.
    """
    NAME = "update_conv_data"

    async def _handle(self, event: dict, kwargs) -> bool:
        fields = ("conv_mark",)
        mark = db.execute.select(
            schema="toaster",
            table="conversations",
            fields=fields,
            conv_id=event.get("peer_id")
        )
        already_marked = bool(mark)

        if already_marked:
            new_data = {
                "conv_name": event.get("peer_name"),
            }
            db.execute.update(
                schema="toaster",
                table="conversations",
                new_data=new_data,
                conv_id=event.get("peer_id")
            )

            snackbar_message = "📝 Данные беседы обновлены."

        else:
            snackbar_message = "❗Беседа еще не имеет метку."

        self.snackbar(event, snackbar_message)

        return True



class DropMarkAction(BaseAction):
    """Removes the mark from the conversation,
    deleting records about it in the database.
    """
    NAME = "drop_mark"

    async def _handle(self, event: dict, kwargs) -> bool:
        fields = ("conv_mark",)
        mark = db.execute.select(
            schema="toaster",
            table="conversations",
            fields=fields,
            conv_id=event.get("peer_id")
        )
        already_marked = bool(mark)

        if already_marked:
            db.execute.delete(
                schema="toaster",
                table="conversations",
                conv_id=event.get("peer_id")
            )

            snackbar_message = f"📝 Метка \"{mark[0][0]}\" снята с беседы."

        else:
            snackbar_message = "❗Беседа еще не имеет метку."

        self.snackbar(event, snackbar_message)

        return True



# ------------------------------------------------------------------------
class SetPermissionAction(BaseAction):
    """Sets the user to the "administrator" role,
    records this in the database.
    """
    NAME = "set_permission"

    async def _handle(self, event: dict, kwargs) -> bool:
        fields = ("user_permission",)
        target_id=event["payload"].get("target")
        lvl = db.execute.select(
            schema="toaster",
            table="permissions",
            fields=fields,
            user_id=target_id
        )
        already_promoted = bool(lvl)
        user_lvl = int(event.get("payload").get("permission"))

        if already_promoted:
            if user_lvl == 0:
                role = config.PERMISSIONS_DECODING[user_lvl]
                snackbar_message = f"⚒️ Пользователю назначена роль \"{role}\"."

                db.execute.delete(
                    schema="toaster",
                    table="permissions",
                    user_id=target_id
                )

                self.snackbar(event, snackbar_message)

                return True

            user_lvl = int(lvl[0][0])

            role = config.PERMISSIONS_DECODING[user_lvl]
            snackbar_message = f"❗Пользователь уже имеет роль \"{role}\"."

            self.snackbar(event, snackbar_message)

            return False

        else:
            role = config.PERMISSIONS_DECODING[user_lvl]
            if user_lvl == 0:
                snackbar_message = f"❗Пользователь уже имеет роль \"{role}\"."
                self.snackbar(event, snackbar_message)

                return False

            snackbar_message = f"⚒️ Пользователю назначена роль \"{role}\"."

        user_name = self.get_name(target_id)

        db.execute.insert(
            schema="toaster",
            table="permissions",
            on_duplicate="update",
            conv_id=event.get("peer_id"),
            user_id=target_id,
            user_name=user_name,
            user_permission=user_lvl
        )

        self.snackbar(event, snackbar_message)

        return True


    def get_name(self, user_id: int) -> str:
        """Returns the full name of the user,
        using its unique ID.

        Args:
            user_id (int): User ID.

        Returns:
            str: User full name.
        """
        name = self.api.users.get(
            user_ids=user_id
        )

        if not bool(name):
            name = "Unknown"

        else:
            name = name[0].get("first_name") + \
                " " + name[0].get("last_name")

        return name



class DropPermissionAction(BaseAction):
    """Sets the user to the "user" role,
    records this in the database.
    """
    NAME = "drop_permission"

    async def _handle(self, event: dict, kwargs) -> bool:
        fields = ("user_permission",)
        target_id = event["payload"].get("target")
        lvl = db.execute.select(
            schema="toaster",
            table="permissions",
            fields=fields,
            user_id=target_id
        )
        already_promoted = bool(lvl)

        role = config.PERMISSIONS_DECODING[0]
        snackbar_message = f"⚒️ Пользователю назначена роль \"{role}\"."

        if not already_promoted:
            lvl = 0
            role = config.PERMISSIONS_DECODING[lvl]
            snackbar_message = f"❗Пользователь уже имеет роль \"{role}\"."

            self.snackbar(event, snackbar_message)

            return False

        db.execute.delete(
            schema="toaster",
            table="permissions",
            user_id=target_id
        )

        self.snackbar(event, snackbar_message)

        return True



# ------------------------------------------------------------------------
class GameRollAction(BaseAction):
    """Starts roll game.
    """
    NAME = "game_roll"
    EMOJI=['0️⃣', '1️⃣',' 2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣' ,'8️⃣', '9️⃣']

    async def _handle(self, event: dict, kwargs) -> bool:
        result = random.randint(0,100)
        result = self._convert_to_emoji(result)

        tag = f"[id{event.get('user_id')}|{event.get('user_name')}]"

        new_msg_text = f"{tag} выбивает число: {result}"

        keyboard = (
            Keyboard(inline=True, one_time=False, owner_id=None)
        )

        self.api.messages.edit(
            peer_id=event.get("peer_id"),
            conversation_message_id=event.get("cmid"),
            message=new_msg_text,
            keyboard=keyboard.json
        )

        snackbar_message = "🎲 Рулетка прокручена!"

        self.snackbar(event, snackbar_message)

        return True


    def _convert_to_emoji(self, number):
        result = ''

        for didgit in str(number):
            result += self.EMOJI[int(didgit)]

        return result


class GameCoinflipAction(BaseAction):
    """Starts coinflip game.
    """
    NAME = "game_coinflip"
    EMOJI = ["Орёл 🪙", "Решка 🪙"]

    async def _handle(self, event: dict, kwargs) -> bool:
        result = random.randint(0, 1)
        result = self._convert_to_emoji(result)

        tag = f"[id{event.get('user_id')}|{event.get('user_name')}]"

        new_msg_text = f"{tag} подбрасывает монетку: {result}"

        keyboard = (
            Keyboard(inline=True, one_time=False, owner_id=None)
        )

        self.api.messages.edit(
            peer_id=event.get("peer_id"),
            conversation_message_id=event.get("cmid"),
            message=new_msg_text,
            keyboard=keyboard.json
        )

        snackbar_message = "🎲 Монета брошена!"

        self.snackbar(event, snackbar_message)

        return True


    def _convert_to_emoji(self, number):
        return self.EMOJI[number]


# ------------------------------------------------------------------------
class SystemSettingsAction(BaseAction):
    """Sets the value to the 
    selected message filter settings field.
    """
    NAME = "systems_settings"

    async def _handle(self, event: dict, kwargs) -> bool:
        payload = event["payload"]

        systems = db.execute.select(
            schema="toaster_settings",
            table="settings",
            fields=("setting_name", "setting_status"),
            conv_id=event.get("peer_id"),
            setting_destination="system"
        )

        sys_status = {
            row[0]: int(row[1]) for row in systems
        }

        color_by_status = {
            0: ButtonColor.NEGATIVE,
            1: ButtonColor.POSITIVE
        }

        page = int(payload.get("page", 1))

        if payload.get("sub_action") == "change_setting":
            sys_name = payload.get("system_name")
            new_status = abs(sys_status[sys_name] - 1) # (0 to 1) or (1 to 0)
            sys_status[sys_name] = new_status
            snackbar_message = f"⚠️ Система {'Включена' if new_status else 'Выключена'}."
            db.execute.update(
                schema="toaster_settings",
                table="settings",
                new_data={"setting_status": new_status},
                conv_id=event.get("peer_id"),
                setting_name=sys_name,
                setting_destination="system"
            )

        else:
            snackbar_message = f"⚙️ Меню систем модерации ({page}/1).."

        if page == 1:
            keyboard = (
                Keyboard(inline=True, one_time=False, owner_id=event.get("user_id"))
                .add_row()
                .add_button(
                    Callback(
                        label=f"Возраста аккаунта: {'Вкл.' if sys_status['account_age'] else 'Выкл.'}",
                        payload={
                            "call_action": "systems_settings",
                            "sub_action": "change_setting",
                            "system_name": "account_age",
                            "page": "1"
                        }
                    ),
                    color_by_status[sys_status["account_age"]]
                )
                .add_row()
                .add_button(
                    Callback(
                        label=f"Плохие слова: {'Вкл.' if sys_status['curse_words'] else 'Выкл.'}",
                        payload={
                            "call_action": "systems_settings",
                            "sub_action": "change_setting",
                            "system_name": "curse_words",
                            "page": "1"
                        }
                    ),
                    color_by_status[sys_status["curse_words"]]
                )
                .add_row()
                .add_button(
                    Callback(
                        label=f"Усиленый режим: {'Вкл.' if sys_status['hard_mode'] else 'Выкл.'}",
                        payload={
                            "call_action": "systems_settings",
                            "sub_action": "change_setting",
                            "system_name": "hard_mode",
                            "page": "1"
                        }
                    ),
                    color_by_status[sys_status["hard_mode"]]
                )
                .add_row()
                .add_button(
                    Callback(
                        label=f"Открытое ЛС: {'Вкл.' if sys_status['open_pm'] else 'Выкл.'}",
                        payload={
                            "call_action": "systems_settings",
                            "sub_action": "change_setting",
                            "system_name": "open_pm",
                            "page": "1"
                        }
                    ),
                    color_by_status[sys_status["open_pm"]]
                )
                .add_row()
                .add_button(
                    Callback(
                        label=f"Медленный режим: {'Вкл.' if sys_status['slow_mode'] else 'Выкл.'}",
                        payload={
                            "call_action": "systems_settings",
                            "sub_action": "change_setting",
                            "system_name": "slow_mode",
                            "page": "1"
                        }
                    ),
                    color_by_status[sys_status["slow_mode"]]
                )
                .add_row()
                .add_button(
                    Callback(
                        label="Закрыть меню",
                        payload={
                            "call_action": "cancel_command"
                        }
                    ),
                    ButtonColor.SECONDARY
                )
            )

        new_msg_text = "⚙️ Включение\\Выключение систем модерации:"
        self.api.messages.edit(
            peer_id=event.get("peer_id"),
            conversation_message_id=event.get("cmid"),
            message=new_msg_text,
            keyboard=keyboard.json
        )

        self.snackbar(event, snackbar_message)

        return True



class FilterSettingsAction(BaseAction):
    """Sets the value to the selected
    moderation systems settings field.
    """
    NAME = "filters_settings"

    async def _handle(self, event: dict, kwargs) -> bool:
        payload = event["payload"]

        systems = db.execute.select(
            schema="toaster_settings",
            table="settings",
            fields=("setting_name", "setting_status"),
            conv_id=event.get("peer_id"),
            setting_destination="filter"
        )

        filt_status = {
            row[0]: int(row[1]) for row in systems
        }

        color_by_status = {
            0: ButtonColor.NEGATIVE,
            1: ButtonColor.POSITIVE
        }

        page = int(payload.get("page", 1))

        if payload.get("sub_action") == "change_setting":
            filt_name = payload.get("filter_name")
            new_status = abs(filt_status[filt_name] - 1) # (0 to 1) or (1 to 0)
            filt_status[filt_name] = new_status
            snackbar_message = f"⚠️ Фильтр {'Включен' if not new_status else 'Выключен'}."
            db.execute.update(
                schema="toaster_settings",
                table="settings",
                new_data={"setting_status": new_status},
                conv_id=event.get("peer_id"),
                setting_name=filt_name,
                setting_destination="filter"
            )

        else:
            snackbar_message = f"⚙️ Меню фильтров сообщений ({page}/4)."

        if page == 1:
            keyboard = (
                Keyboard(inline=True, one_time=False, owner_id=event.get("user_id"))
                .add_row()
                .add_button(
                    Callback(
                        label=f"Приложения: {'Вкл.' if filt_status['app_action'] else 'Выкл.'}",
                        payload={
                            "call_action": "filters_settings",
                            "sub_action": "change_setting",
                            "filter_name": "app_action",
                            "page": "1"
                        }
                    ),
                    color_by_status[filt_status["app_action"]]
                )
                .add_row()
                .add_button(
                    Callback(
                        label=f"Музыка: {'Вкл.' if filt_status['audio'] else 'Выкл.'}",
                        payload={
                            "call_action": "filters_settings",
                            "sub_action": "change_setting",
                            "filter_name": "audio",
                            "page": "1"
                        }
                    ),
                    color_by_status[filt_status["audio"]]
                )
                .add_row()
                .add_button(
                    Callback(
                        label=f"Аудио: {'Вкл.' if filt_status['audio_message'] else 'Выкл.'}",
                        payload={
                            "call_action": "filters_settings",
                            "sub_action": "change_setting",
                            "filter_name": "audio_message",
                            "page": "1"
                        }
                    ),
                    color_by_status[filt_status["audio_message"]]
                )
                .add_row()
                .add_button(
                    Callback(
                        label=f"Файлы: {'Вкл.' if filt_status['doc'] else 'Выкл.'}",
                        payload={
                            "call_action": "filters_settings",
                            "sub_action": "change_setting",
                            "filter_name": "doc",
                            "page": "1"
                        }
                    ),
                    color_by_status[filt_status["doc"]]
                )
                .add_row()
                .add_button(
                    Callback(
                        label="-->",
                        payload={
                            "call_action": "filters_settings",
                            "page": "2"
                        }
                    ),
                    ButtonColor.SECONDARY
                )
                .add_row()
                .add_button(
                    Callback(
                        label="Закрыть меню",
                        payload={
                            "call_action": "cancel_command"
                        }
                    ),
                    ButtonColor.SECONDARY
                )
            )

        elif page == 2:
            keyboard = (
                Keyboard(inline=True, one_time=False, owner_id=event.get("user_id"))
                .add_row()
                .add_button(
                    Callback(
                        label=f"Пересыл: {'Вкл.' if filt_status['forward'] else 'Выкл.'}",
                        payload={
                            "call_action": "filters_settings",
                            "sub_action": "change_setting",
                            "filter_name": "forward",
                            "page": "2"
                        }
                    ),
                    color_by_status[filt_status["forward"]]
                )
                .add_row()
                .add_button(
                    Callback(
                        label=f"Ответ: {'Вкл.' if filt_status['reply'] else 'Выкл.'}",
                        payload={
                            "call_action": "filters_settings",
                            "sub_action": "change_setting",
                            "filter_name": "reply",
                            "page": "2"
                        }
                    ),
                    color_by_status[filt_status["reply"]]
                )
                .add_row()
                .add_button(
                    Callback(
                        label=f"Граффити: {'Вкл.' if filt_status['graffiti'] else 'Выкл.'}",
                        payload={
                            "call_action": "filters_settings",
                            "sub_action": "change_setting",
                            "filter_name": "graffiti",
                            "page": "2"
                        }
                    ),
                    color_by_status[filt_status["graffiti"]]
                )
                .add_row()
                .add_button(
                    Callback(
                        label=f"Стикеры: {'Вкл.' if filt_status['sticker'] else 'Выкл.'}",
                        payload={
                            "call_action": "filters_settings",
                            "sub_action": "change_setting",
                            "filter_name": "sticker",
                            "page": "2"
                        }
                    ),
                    color_by_status[filt_status["sticker"]]
                )
                .add_row()
                .add_button(
                    Callback(
                        label="<--",
                        payload={
                            "call_action": "filters_settings",
                            "page": "1"
                        }
                    ),
                    ButtonColor.SECONDARY
                )
                .add_button(
                    Callback(
                        label="-->",
                        payload={
                            "call_action": "filters_settings",
                            "page": "3"
                        }
                    ),
                    ButtonColor.SECONDARY
                )
                .add_row()
                .add_button(
                    Callback(
                        label="Закрыть меню",
                        payload={
                            "call_action": "cancel_command"
                        }
                    ),
                    ButtonColor.SECONDARY
                )
            )

        elif page == 3:
            keyboard = (
                Keyboard(inline=True, one_time=False, owner_id=event.get("user_id"))
                .add_row()
                .add_button(
                    Callback(
                        label=f"Линки: {'Вкл.' if filt_status['link'] else 'Выкл.'}",
                        payload={
                            "call_action": "filters_settings",
                            "sub_action": "change_setting",
                            "filter_name": "link",
                            "page": "3"
                        }
                    ),
                    color_by_status[filt_status["link"]]
                )
                .add_row()
                .add_button(
                    Callback(
                        label=f"Изображения: {'Вкл.' if filt_status['photo'] else 'Выкл.'}",
                        payload={
                            "call_action": "filters_settings",
                            "sub_action": "change_setting",
                            "filter_name": "photo",
                            "page": "3"
                        }
                    ),
                    color_by_status[filt_status["photo"]]
                )
                .add_row()
                .add_button(
                    Callback(
                        label=f"Опросы: {'Вкл.' if filt_status['poll'] else 'Выкл.'}",
                        payload={
                            "call_action": "filters_settings",
                            "sub_action": "change_setting",
                            "filter_name": "poll",
                            "page": "3"
                        }
                    ),
                    color_by_status[filt_status["poll"]]
                )
                .add_row()
                .add_button(
                    Callback(
                        label=f"Видео: {'Вкл.' if filt_status['video'] else 'Выкл.'}",
                        payload={
                            "call_action": "filters_settings",
                            "sub_action": "change_setting",
                            "filter_name": "video",
                            "page": "3"
                        }
                    ),
                    color_by_status[filt_status["video"]]
                )
                .add_row()
                .add_button(
                    Callback(
                        label="<--",
                        payload={
                            "call_action": "filters_settings",
                            "page": "2"
                        }
                    ),
                    ButtonColor.SECONDARY
                )
                .add_button(
                    Callback(
                        label="-->",
                        payload={
                            "call_action": "filters_settings",
                            "page": "4"
                        }
                    ),
                    ButtonColor.SECONDARY
                )
                .add_row()
                .add_button(
                    Callback(
                        label="Закрыть меню",
                        payload={
                            "call_action": "cancel_command"
                        }
                    ),
                    ButtonColor.SECONDARY
                )
            )

        elif page == 4:
            keyboard = (
                Keyboard(inline=True, one_time=False, owner_id=event.get("user_id"))
                .add_row()
                .add_button(
                    Callback(
                        label=f"Записи: {'Вкл.' if filt_status['Wall'] else 'Выкл.'}",
                        payload={
                            "call_action": "filters_settings",
                            "sub_action": "change_setting",
                            "filter_name": "Wall",
                            "page": "4"
                        }
                    ),
                    color_by_status[filt_status["Wall"]]
                )
                .add_row()
                .add_button(
                    Callback(
                        label=f"Геопозиция: {'Вкл.' if filt_status['geo'] else 'Выкл.'}",
                        payload={
                            "call_action": "filters_settings",
                            "sub_action": "change_setting",
                            "filter_name": "geo",
                            "page": "4"
                        }
                    ),
                    color_by_status[filt_status["geo"]]
                )
                .add_row()
                .add_button(
                    Callback(
                        label="<--",
                        payload={
                            "call_action": "filters_settings",
                            "page": "3"
                        }
                    ),
                    ButtonColor.SECONDARY
                )
                .add_row()
                .add_button(
                    Callback(
                        label="Закрыть меню",
                        payload={
                            "call_action": "cancel_command"
                        }
                    ),
                    ButtonColor.SECONDARY
                )
            )

        new_msg_text = "⚙️ Включение\\Выключение фильтров сообщений:"
        self.api.messages.edit(
            peer_id=event.get("peer_id"),
            conversation_message_id=event.get("cmid"),
            message=new_msg_text,
            keyboard=keyboard.json
        )

        self.snackbar(event, snackbar_message)

        return True
