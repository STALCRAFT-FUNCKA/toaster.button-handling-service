from logger import logger
from .abc import ABCHandler
from .actions import action_list


class ButtonHandler(ABCHandler):
    """Event handler class that recognizes commands
    in the message and executing attached to each command
    actions.
    """

    async def _handle(self, event: dict, kwargs) -> bool:
        if not bool(event.get("payload")):
            log_text = f"Missing payload <{event.get('event_id')}>"
            await logger.info(log_text)

            return False

        payload = event.get("payload")
        call_action = payload.get("call_action")

        kbd_owner = await self.__get_kbdowner(event)

        if event.get("user_id") == kbd_owner:
            selected = action_list.get(call_action)

        else:
            selected = action_list.get("not_msg_owner")

        if selected is None:
            log_text = f'Could not call action "{call_action}"'
            await logger.info(log_text)

            return False

        selected = selected(super().api)
        result = await selected(event)

        log_text = f"Event <{event.get('event_id')}> "

        if result:
            log_text += f'triggered "{selected.NAME}" action.'

        else:
            log_text += "did not triggered any action."

        await logger.info(log_text)
        return result

    async def __get_kbdowner(self, event: dict) -> int:
        payload = event.get("payload")
        return payload.get("keyboard_owner")


button_handler = ButtonHandler()
