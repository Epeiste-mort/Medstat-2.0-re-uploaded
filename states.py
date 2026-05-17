from aiogram.fsm.state import State, StatesGroup

class User_states(StatesGroup):
    registration = State()
    reg_organisation = State()
    reg_post = State()
    registration_accepted = State()
    form_choosing = State()
    question_process = State()
    neuro_process = State()
    file_date = State()

class Admin_states(StatesGroup):
    registration_process = State()
    post_publication = State()
    file_loading = State()
    delete_member = State()
    answers_form = State()
    user_sending = State()
    delete_file = State()
    report_ending = State()
    form_managing = State()
    users_managing = State()
    user_adding = State()
    form_linking = State()
    spec_linking = State()
    
class Specialist_states(StatesGroup):
    choosing_question = State()
    answer_question = State()
    public_choose_message = State()
    complex_public = State()
    choosing_filter = State()

