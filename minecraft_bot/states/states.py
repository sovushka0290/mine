from aiogram.fsm.state import State, StatesGroup


class RegisterNick(StatesGroup):
    waiting_nick = State()


class CreateTask(StatesGroup):
    title = State()
    description = State()
    resource = State()
    quantity = State()
    deadline = State()


class SendReport(StatesGroup):
    photo = State()
    resource = State()
    quantity = State()


class WarnPlayer(StatesGroup):
    choose_player = State()
    reason = State()


class EditWarehouse(StatesGroup):
    resource = State()
    quantity = State()
