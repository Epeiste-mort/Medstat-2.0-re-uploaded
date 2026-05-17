from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup

from non_script_files.config import forms_data, OPEN_CHANNEL_URL, COORD_CHAT_URL, RASDEL_FORM_URL
from db_actions import Database


db = Database()

back_to_menu = [[KeyboardButton(text="Возврат в главное меню")]]
general_kb = ReplyKeyboardMarkup(keyboard=back_to_menu, resize_keyboard=True)
BUTTONS_TO_NUMBER = {'private':0, 'form':1, 'open':2}

# ----------------------------------------------U-S-E-R-T-P-A-N-E-L----------------------------------------------
class User_Keyboards():
    
    async def main_menu(filled_form = False, user_id: int = None) -> InlineKeyboardMarkup:

        '''
            Функция, возвращающая все клавиатуры, связанные с главным меню и возвратом к нему.
            Может быть аргументом reply_markup
        '''
        user_starting_keyboard = InlineKeyboardBuilder()
        npa_button = InlineKeyboardButton(text='НПА', callback_data='npa')
        medstat_button = InlineKeyboardButton(text='Медстат', callback_data='medstat')
        statistic_button = InlineKeyboardButton(text='Статистика', callback_data='statistic')
        method_recommendations_button = InlineKeyboardButton(text='Методические рекомендации', callback_data='method_recommendations')
        registration_button = InlineKeyboardButton(text='Регистрация для МИАЦ', callback_data='registration')
        make_question_button = InlineKeyboardButton(text='Задать вопрос', callback_data='make_question')
        open_chat_button = InlineKeyboardButton(text='Открытый канал', callback_data='link_open_chat', url=OPEN_CHANNEL_URL)
        razdel_chat_button = InlineKeyboardButton(text='Канал раздела форм', callback_data='link_razdel_chat')
        link = await db.get_link(user_id=user_id)
        if link:
            sogl_chat_button = InlineKeyboardButton(text='Уведомления MedstatWEB', callback_data='link_sogl_chat', url=link[0]['link'])
        
        if filled_form == False:
            user_starting_keyboard.add(npa_button, 
                        medstat_button, 
                        statistic_button,
                        method_recommendations_button,
                        open_chat_button, 
                        registration_button)
        else:
            try:
                user_starting_keyboard.add(npa_button, 
                            medstat_button, 
                            statistic_button,
                            method_recommendations_button,
                            open_chat_button,
                            make_question_button,
                            razdel_chat_button,
                            sogl_chat_button)
            except UnboundLocalError:
                user_starting_keyboard.add(npa_button, 
                            medstat_button, 
                            statistic_button,
                            method_recommendations_button,
                            open_chat_button,
                            make_question_button,
                            razdel_chat_button)
        
        return user_starting_keyboard.adjust(1, repeat=True).as_markup()
    
    def back_to_main_menu() -> InlineKeyboardBuilder:
        main_menu_back = InlineKeyboardBuilder()
        back_button = InlineKeyboardButton(text='Вернуться в главное меню', callback_data='main_menu')
        main_menu_back.add(back_button)
        return main_menu_back.adjust(1, repeat=True)

    def section_chose(tag_tuple: tuple = None, user_type: str = "User") -> InlineKeyboardBuilder:
        section_key = InlineKeyboardBuilder()

        button_one = InlineKeyboardButton(text='• Ф. № 30 Латышова А.А.', callback_data='sec_one')
        button_two = InlineKeyboardButton(text='• Ф. № 30 Тюрина Е.М. (Березовская)', callback_data='sec_two')
        button_three = InlineKeyboardButton(text='• Ф. № 30 Шелепова Е.А.', callback_data='sec_three')
        button_four = InlineKeyboardButton(text='• Ф. № 14-ДС; Ф. 30 (в части работы СМП) Шляфер С.И.', callback_data='sec_four')
        button_five = InlineKeyboardButton(text='• Ф. № 47', callback_data='sec_five')
        button_six = InlineKeyboardButton(text='• ф. № 8, 33, 2-ТБ, 7-ТБ, 8-ТБ, 10-ТБ (туберкулез)', callback_data='sec_six')
        button_seven = InlineKeyboardButton(text='• Ф. № 12, 12-село', callback_data='sec_seven')
        button_eight = InlineKeyboardButton(text='• Ф. № 19, 41, 54, 16-ВН, 1-РБ, 1-Дети (здрав)', callback_data='sec_eight')
        button_nine = InlineKeyboardButton(text='• Специализированные формы (Ф. № 36 -ПЛ; Ф. № 11, 37; Ф. № 15; Ф. № 64', callback_data='sec_nine')
        button_ten = InlineKeyboardButton(text='Чат координаторов', callback_data='sec_ten')
        button_eleven = InlineKeyboardButton(text='• Нормативные документы', callback_data='sec_eleven')
        button_medstat = InlineKeyboardButton(text='• Система МЕДСТАТ', callback_data='sec_medstat')
        button_general = InlineKeyboardButton(text='• Общий раздел', callback_data='sec_general')
        button_twelve = InlineKeyboardButton(text='• Ф. № 55, 56', callback_data='sec_twelve')
        button_13 = InlineKeyboardButton(text='• Ф. № 61', callback_data='sec_13')
        button_14 = InlineKeyboardButton(text='• Ф. № 9, 34', callback_data='sec_14')
        button_15 = InlineKeyboardButton(text='• Ф. № 57', callback_data='sec_15')
        button_16 = InlineKeyboardButton(text='• ФОСН 70, 53', callback_data='sec_16')
        button_17 = InlineKeyboardButton(text='• Ф. № 13', callback_data='sec_17')
        button_18 = InlineKeyboardButton(text='• Ф. № 65', callback_data='sec_18')
        button_19 = InlineKeyboardButton(text='• Ф. № 14', callback_data='sec_19')
        button_20 = InlineKeyboardButton(text='• Ф. № 7', callback_data='sec_20')
        button_21 = InlineKeyboardButton(text='• Ф. № 30 (в части работы Лабораторной службы)', callback_data='sec_21')
        button_22 = InlineKeyboardButton(text='• Ф. № 10, 36', callback_data='sec_22')
        button_23 = InlineKeyboardButton(text='• Ф. № 42', callback_data='sec_23')
        button_24 = InlineKeyboardButton(text='• Ф. № 32, 232 (вкладыш)', callback_data='sec_24')

        button_tuple = (button_eleven, button_medstat, button_general, button_20, button_six, button_14, button_22, button_nine, button_seven,
                        button_17, button_19, button_four, button_eight, button_24, button_one, button_two, button_three, button_21, button_23, button_five,
                        button_16, button_twelve, button_15, button_13, button_18, button_ten)
        
        if user_type == "Admin":
            [section_key.add(button_elem) for tag_tuple_elem in tag_tuple for button_elem in button_tuple if button_elem.callback_data == tag_tuple_elem]
        else:
            section_key.add(button_eleven, button_medstat, button_general, button_20, button_six, button_14, button_22, button_nine, button_seven,
                        button_17, button_19, button_four, button_eight, button_24, button_one, button_two, button_three, button_21, button_23, button_five,
                        button_16, button_twelve, button_15, button_13, button_18, button_ten)
        
        return section_key.adjust(1, repeat=True)

    async def create_district_buttons() -> InlineKeyboardMarkup:
        '''
        Создание клавиатуры для выбора Федерального округа
        '''
        district_keyboard = InlineKeyboardBuilder()
        from main import db
        result = await db.get_miac_information(info_type='federal_district')
        for record in result:
            federal_name = record['federal_name']
            district_tag = record['district_tag']
            button = InlineKeyboardButton(text=federal_name, callback_data=district_tag)
            district_keyboard.add(button)

        district_keyboard.adjust(1, repeat=True)
        return district_keyboard.as_markup()
    
    async def create_regions_buttons(district_id: int) -> InlineKeyboardMarkup:
        region_keyboard = InlineKeyboardBuilder()
        from main import db
        result = await db.get_miac_information(info_type='region', district_id=district_id)
        for record in result:
            region_name = record['region_name']
            region_tag = record['region_tag']
            button = InlineKeyboardButton(text=region_name, callback_data=region_tag)
            region_keyboard.add(button)

        region_keyboard.adjust(1, repeat=True)
        return region_keyboard.as_markup()
    
    def fuzzy_buttons_generate(questions) -> InlineKeyboardBuilder:
        text_pattern = []
        fuzzy_keyboard = InlineKeyboardBuilder()
        buttons_data = [InlineKeyboardButton(text=f"Ответ на вопрос №{num + 1}", callback_data=f"fuzzy_buttons&simular_rate:{value[1][0]}&index:{value[0]}") for num, value in enumerate(questions)]
        [text_pattern.append(f"Вопрос №{num + 1}: {value[1][1]}\n") for num, value in enumerate(questions)]
        text_pattern = "".join(text_pattern)
        fuzzy_keyboard.add(*[elem for elem in buttons_data])
        fuzzy_keyboard.adjust(1, repeat=True)
        return fuzzy_keyboard, text_pattern

    def back_to_fuzzy_questions() -> InlineKeyboardBuilder:
        back_to_pool = InlineKeyboardBuilder()
        back_to_pool.add(InlineKeyboardButton(text="Назад к списку вопросов", callback_data="back_to_fuzzy"))
        back_to_pool.adjust(1, repeat=True)
        return back_to_pool

    def out_of_fuzzy_questions() -> InlineKeyboardMarkup:
        
        out_of_pool = InlineKeyboardBuilder()
        not_found = InlineKeyboardButton(text="Не нашёл подходящего вопроса", callback_data="not_found_question")
        out_of_pool.add(not_found)
        out_of_pool.adjust(1)
        return out_of_pool.as_markup()
    
    def show_files() -> InlineKeyboardMarkup:
        show_keyboard = InlineKeyboardBuilder()
        week_button = InlineKeyboardButton(text='За последнюю неделю', callback_data='1 week')
        full_button = InlineKeyboardButton(text='За все время', callback_data='full')
        show_keyboard.add(week_button, full_button)
        show_keyboard.adjust(1)
        return show_keyboard.as_markup()

    def model_reply_proc(msg_type: str) -> InlineKeyboardMarkup:
        model_keyboard = InlineKeyboardBuilder()
        chose_correct = InlineKeyboardButton(text="Выбрать ответ", callback_data="chose_reply")
        redirect_question = InlineKeyboardButton(text="Передать вопрос специалисту", callback_data="redirect_question")
        
        if msg_type == "bot":
                    model_keyboard.add(chose_correct)
        elif msg_type == "user":
                    model_keyboard.add(redirect_question)

        model_keyboard.adjust(1)
        return model_keyboard.as_markup()
        
    forms_keyboard: InlineKeyboardBuilder = section_chose()
# ----------------------------------------------U-S-E-R-T-P-A-N-E-L----------------------------------------------

# ----------------------------------------------O-W-N-E-R-P-A-N-E-L----------------------------------------------

class Owner_Keyboards():

    def main_menu() -> InlineKeyboardBuilder:
        owner_starting_keyboard = InlineKeyboardBuilder()

        admin_panel = InlineKeyboardButton(text='Админ-панель', callback_data='admin_panel')
        specialist_panel = InlineKeyboardButton(text='Специалист-панель', callback_data='specialist_panel')
        owner_starting_keyboard.add(admin_panel, specialist_panel)
        return owner_starting_keyboard
    
    owner_starting_keyboard = main_menu().adjust(1, repeat=True)
# ----------------------------------------------O-W-N-E-R-P-A-N-E-L----------------------------------------------

# ----------------------------------------------A-D-M-I-N-P-A-N-E-L----------------------------------------------
class Admin_Keyboards():
    
    def main_menu() -> InlineKeyboardMarkup:
        '''
            Функция, возвращающая все клавиатуры, связанные с главным меню и возвратом к нему.
            Может быть аргументом reply_markup
        '''
        admin_starting_keyboard = InlineKeyboardBuilder()

        check_registrations = InlineKeyboardButton(text='Проверить регистрацию', callback_data='check_reg')
        registration_db = InlineKeyboardButton(text='Данные о зарегистрированных', callback_data='registration_db')
        publications = InlineKeyboardButton(text='Проверить публикации', callback_data='publications')
        open_chan = InlineKeyboardButton(text='Открытый канал', callback_data='op_channel_join', url=OPEN_CHANNEL_URL)
        coord_chat = InlineKeyboardButton(text='Чат координаторов', callback_data='coord_chat_join', url=COORD_CHAT_URL)
        sections = InlineKeyboardButton(text='Разделы форм', callback_data='sections_join', url=RASDEL_FORM_URL)
        file_button = InlineKeyboardButton(text='Загрузить файлы', callback_data='load_file')
        delete_file_button = InlineKeyboardButton(text='Удалить файл/ы', callback_data='delete_file')
        forms_managing = InlineKeyboardButton(text="Управление разделами", callback_data="forms_managing")
        users_managing = InlineKeyboardButton(text="Управление специалистами", callback_data="users_managing")
        delete_member = InlineKeyboardButton(text='Удалить пользователя из чата', callback_data='delete_member')
        send_private_message = InlineKeyboardButton(text='Отправить пользователю сообщение', callback_data='send_to_user')
        reporting_period_ending = InlineKeyboardButton(text='Завершить отчетный период', callback_data='end_of_report')

        admin_starting_keyboard.add(check_registrations,
                                    registration_db,
                                    publications,
                                    open_chan,
                                    coord_chat,
                                    sections,
                                    file_button,
                                    delete_file_button,
                                    forms_managing,
                                    users_managing,
                                    delete_member,
                                    send_private_message,
                                    reporting_period_ending)
        admin_starting_keyboard.adjust(1, repeat=True)
        return admin_starting_keyboard.as_markup()
       
    def forms_manager_keyboard() -> InlineKeyboardBuilder:
        admin_forms_keyboard = InlineKeyboardBuilder()
        
        return_to_menu = InlineKeyboardButton(text="Вернуться в главное меню", callback_data="admin_panel")
        add_form = InlineKeyboardButton(text="Создать раздел", callback_data="forms_add")
        delete_form = InlineKeyboardButton(text="Удалить раздел", callback_data="forms_del")
        
        admin_forms_keyboard.add(add_form, delete_form, return_to_menu)
        admin_forms_keyboard.adjust(1)

        return admin_forms_keyboard.as_markup()
       
    def users_manager_keyboard() -> InlineKeyboardBuilder:
        admin_users_keyboard = InlineKeyboardBuilder()

        return_to_menu = InlineKeyboardButton(text="Вернуться в главное меню", callback_data="admin_panel")
        add_user = InlineKeyboardButton(text="Добавить специалиста", callback_data="users_add")
        change_form = InlineKeyboardButton(text="Изменить формы специалиста", callback_data="users_change")
        delete_user = InlineKeyboardButton(text="Удалить специалиста", callback_data="users_del")

        admin_users_keyboard.add(add_user, change_form, delete_user, return_to_menu)
        admin_users_keyboard.adjust(1)

        return admin_users_keyboard.as_markup()
       
    def reg_process_keyboard(user_id, user_string_id) -> InlineKeyboardBuilder:
        '''
            Функция, возвращающая все клавиатуры, связанные с процессом регистрации (с соотношением админ-->юзер)
            Может быть аргументом reply_markup
        '''
        admin_registrator_keyboard = InlineKeyboardBuilder()
        
        back_to_checking = InlineKeyboardButton(text='Вернуться', callback_data='check_reg')
        decline = InlineKeyboardButton(text='Отклонить заявку', callback_data=f'dec_app:{user_id}:{user_string_id}')
        accept = InlineKeyboardButton(text='Принять заявку', callback_data=f'acc_app:{user_id}:{user_string_id}')

        admin_registrator_keyboard.add(accept, decline,
                                       back_to_checking)
        admin_registrator_keyboard.adjust(2, 1)

        return admin_registrator_keyboard
    
    def application_gen(unreg_tuple, page_value: int) -> InlineKeyboardBuilder:

        '''
            Отдельная функция, генерирующая кнопки, в з-ти от заявок пользователей
            Может быть аргументом reply_markup
        '''

        if page_value == 1 and len(unreg_tuple[1]) == 10:
            unique_keys, registration_forms = unreg_tuple[0], unreg_tuple[1]
            generated_keyboard = InlineKeyboardBuilder()
            buttons_data_1 = [InlineKeyboardButton(text=f"Пользователь из {registration_forms[i]['region_name']}", callback_data=f"generated_button&uk:{registration_forms[i]['id']}&datetime:{registration_forms[i]['registration_date']}") for i in range(len(registration_forms))]
            next_page = InlineKeyboardButton(text="Следующая страница", callback_data=f"next_page:{page_value + 1}")
            generated_keyboard.add(*[elem for elem in buttons_data_1], next_page)
            generated_keyboard.adjust(1, repeat=True)

            return generated_keyboard
        elif page_value == 1 and len(unreg_tuple[1]) < 10:
            unique_keys, registration_forms = unreg_tuple[0], unreg_tuple[1]
            generated_keyboard = InlineKeyboardBuilder()
            buttons_data_2 = [InlineKeyboardButton(text=f"Пользователь из {registration_forms[i]['region_name']}", callback_data=f"generated_button&uk:{registration_forms[i]['id']}&datetime:{registration_forms[i]['registration_date']}") for i in range(len(registration_forms))]
            generated_keyboard.add(*[elem for elem in buttons_data_2])
            generated_keyboard.adjust(1, repeat=True)

            return generated_keyboard
        elif page_value > 1 and len(unreg_tuple[1]) < 10:
            unique_keys, registration_forms = unreg_tuple[0], unreg_tuple[1]
            generated_keyboard = InlineKeyboardBuilder()
            buttons_data_3 = [InlineKeyboardButton(text=f"Пользователь из {registration_forms[i]['region_name']}", callback_data=f"generated_button&uk:{registration_forms[i]['id']}&datetime:{registration_forms[i]['registration_date']}") for i in range(len(registration_forms))]
            prev_page = InlineKeyboardButton(text="Предыдущая страница", callback_data=f"prev_page:{page_value - 1}")
            generated_keyboard.add(*[elem for elem in buttons_data_3], prev_page)
            generated_keyboard.adjust(1, repeat=True)
    
            return generated_keyboard
        else:
            unique_keys, registration_forms = unreg_tuple[0], unreg_tuple[1]
            generated_keyboard = InlineKeyboardBuilder()
            buttons_data_4 = [InlineKeyboardButton(text=f"Пользователь из {registration_forms[i]['region_name']}", callback_data=f"generated_button&uk:{registration_forms[i]['id']}&datetime:{registration_forms[i]['registration_date']}") for i in range(len(registration_forms))]
            next_page = InlineKeyboardButton(text="Следующая страница", callback_data=f"next_page:{page_value + 1}")
            prev_page = InlineKeyboardButton(text="Предыдущая страница", callback_data=f"prev_page:{page_value - 1}")
            generated_keyboard.add(*[elem for elem in buttons_data_4], next_page, prev_page)
            generated_keyboard.adjust(1, repeat=True)
    
            return generated_keyboard

    def post_publication(post_id: int, pub_type: str = 'text') -> InlineKeyboardMarkup:
        '''
        Клавиатура для выбора публикации в открытом канале
        '''
        publication_keyboard = InlineKeyboardBuilder()

        accept_post = InlineKeyboardButton(text='Опубликовать', callback_data=f'accept_post&pub_type:{pub_type}&pub_id:{post_id}')
        decline_post = InlineKeyboardButton(text='Не опубликовывать', callback_data=f'decline_post&pub_type:{pub_type}&pub_id:{post_id}')

        publication_keyboard.add(accept_post, decline_post)
        publication_keyboard.adjust(2)

        return publication_keyboard.as_markup()

    def pub_refresh() -> InlineKeyboardMarkup:
        pub_ref_kb = InlineKeyboardBuilder()
        pub_ref_kb.add(InlineKeyboardButton(text='Проверить публикации', callback_data='publications'))
        pub_ref_kb.adjust(1)
        return pub_ref_kb.as_markup()

    def file_loading(cancel = False, history_check = False) -> InlineKeyboardMarkup:
        file_kb = InlineKeyboardBuilder()
        if cancel == False:
            npa_button = InlineKeyboardButton(text='НПА', callback_data='npa')
            medstat_button = InlineKeyboardButton(text='Медстат', callback_data='medstat')
            statistic_button = InlineKeyboardButton(text='Статистика', callback_data='statistic')
            method_recommendations_button = InlineKeyboardButton(text='Методические рекомендации', callback_data='method_recommendations')
            file_kb.add(npa_button, medstat_button, statistic_button, method_recommendations_button)
            file_kb.adjust(1)
            return file_kb.as_markup()
        else:

            cancel = InlineKeyboardButton(text="Завершить загрузку", callback_data="cancel_loading")
            check = InlineKeyboardButton(text="Посмотреть загруженные файлы", callback_data="check_loaded")
            file_kb.add(cancel, check)
            file_kb.adjust(1)
            return file_kb.as_markup()
        
    def delete_in_chat() -> InlineKeyboardMarkup:
        delete_keyboard = InlineKeyboardBuilder()

        coord = InlineKeyboardButton(text='Чат координаторов', callback_data='coord_chat')
        forms = InlineKeyboardButton(text='Раздел форм', callback_data='forms_chat')

        delete_keyboard.add(coord, forms)
        delete_keyboard.adjust(1)
        return delete_keyboard.as_markup()
    
    def delete_file(id: int, file_name: str) -> InlineKeyboardMarkup:
        delete_file_keyboard = InlineKeyboardBuilder()

        delete_button = InlineKeyboardButton(text='Удалить файл', callback_data=f'delete_choosen_file:{id}')

        delete_file_keyboard.add(delete_button)
        return delete_file_keyboard.as_markup()
    
    def close_operation() -> InlineKeyboardMarkup:
        close_operation_keyboard = InlineKeyboardBuilder()

        close_button = InlineKeyboardButton(text='Завершить операцию', callback_data='close_operation')

        close_operation_keyboard.add(close_button)
        return close_operation_keyboard.as_markup()

    def filters_menu_admin() -> InlineKeyboardMarkup:
        '''
        Кнопки для меню с фильтрами
        '''
        filters_menu_keyboard = InlineKeyboardBuilder()

        regions_filter_button = InlineKeyboardButton(text='Выбрать регион', callback_data='regions_filter')
        question_type_button = InlineKeyboardButton(text='Выбрать тип вопроса', callback_data='question_type')
        form_selection_button = InlineKeyboardButton(text='Выбрать форму', callback_data='form_selection')
        show_questions_button = InlineKeyboardButton(text='Вывести вопросы', callback_data='show_questions')

        filters_menu_keyboard.add(regions_filter_button,
                                  question_type_button,
                                  form_selection_button,
                                  show_questions_button)
        filters_menu_keyboard.adjust(1)
        return filters_menu_keyboard.as_markup()
    
    def questions_type_menu(unanswered_choosen: str, answered_choosen: str) -> InlineKeyboardMarkup:
        '''
        Кнопки меню фильтра по выбору типа вопросов
        '''
        questions_type_menu = InlineKeyboardBuilder()

        unanswered_button = InlineKeyboardButton(text=f'Неотвеченные вопросы: режим {unanswered_choosen}', callback_data='unanswered_questions')
        answered_button = InlineKeyboardButton(text=f'Отвеченные вопросы: режим {answered_choosen}', callback_data='answered_questions')
        select_filter_button = InlineKeyboardButton(text='Применить', callback_data='select_filter')

        questions_type_menu.add(unanswered_button,
                                answered_button,
                                select_filter_button)
        questions_type_menu.adjust(1)
        return questions_type_menu.as_markup()
    
    def forms_selection(*btns) -> InlineKeyboardMarkup:
        section_key = InlineKeyboardBuilder()

        button_one = InlineKeyboardButton(text='• Ф. № 30 Латышова А.А.', callback_data='sec_one')
        button_two = InlineKeyboardButton(text='• Ф. № 30 Тюрина Е.М. (Березовская)', callback_data='sec_two')
        button_three = InlineKeyboardButton(text='• Ф. № 30 Шелепова Е.А.', callback_data='sec_three')
        button_four = InlineKeyboardButton(text='• Ф. № 14-ДС; Ф. 30 (в части работы СМП) Шляфер С.И.', callback_data='sec_four')
        button_five = InlineKeyboardButton(text='• Ф. № 47', callback_data='sec_five')
        button_six = InlineKeyboardButton(text='• ф. № 8, 33, 2-ТБ, 7-ТБ, 8-ТБ, 10-ТБ (туберкулез)', callback_data='sec_six')
        button_seven = InlineKeyboardButton(text='• Ф. № 12, 12-село', callback_data='sec_seven')
        button_eight = InlineKeyboardButton(text='• Ф. № 19, 41, 54, 16-ВН, 1-РБ, 1-Дети (здрав)', callback_data='sec_eight')
        button_nine = InlineKeyboardButton(text='• Специализированные формы (Ф. № 36 -ПЛ; Ф. № 11, 37; Ф. № 15; Ф. № 64', callback_data='sec_nine')
        button_ten = InlineKeyboardButton(text='Чат координаторов', callback_data='sec_ten')
        button_eleven = InlineKeyboardButton(text='• Нормативные документы', callback_data='sec_eleven')
        button_medstat = InlineKeyboardButton(text='• Система МЕДСТАТ', callback_data='sec_medstat')
        button_general = InlineKeyboardButton(text='• Общий раздел', callback_data='sec_general')
        button_twelve = InlineKeyboardButton(text='• Ф. № 55, 56', callback_data='sec_twelve')
        button_13 = InlineKeyboardButton(text='• Ф. № 61', callback_data='sec_13')
        button_14 = InlineKeyboardButton(text='• Ф. № 9, 34', callback_data='sec_14')
        button_15 = InlineKeyboardButton(text='• Ф. № 57', callback_data='sec_15')
        button_16 = InlineKeyboardButton(text='• ФОСН 70, 53', callback_data='sec_16')
        button_17 = InlineKeyboardButton(text='• Ф. № 13', callback_data='sec_17')
        button_18 = InlineKeyboardButton(text='• Ф. № 65', callback_data='sec_18')
        button_19 = InlineKeyboardButton(text='• Ф. № 14', callback_data='sec_19')
        button_20 = InlineKeyboardButton(text='• Ф. № 7', callback_data='sec_20')
        button_21 = InlineKeyboardButton(text='• Ф. № 30 (в части работы Лабораторной службы)', callback_data='sec_21')
        button_22 = InlineKeyboardButton(text='• Ф. № 10, 36', callback_data='sec_22')
        button_23 = InlineKeyboardButton(text='• Ф. № 42', callback_data='sec_23')
        button_24 = InlineKeyboardButton(text='• Ф. № 32, 232 (вкладыш)', callback_data='sec_24')

        section_key.add(button_eleven, button_medstat, button_general, button_20, button_six, button_14, button_22, button_nine, button_seven, button_17, button_19, button_four, 
                        button_eight, button_24, button_one, button_two, button_three, button_21, button_23, button_five, button_16, button_twelve, button_15, button_13, button_18, button_ten)
        
        return section_key

    def report_ending(data_loaded: bool = False, data_cleared: bool = False) -> InlineKeyboardMarkup:
        report_kb = InlineKeyboardBuilder()
        load_data = InlineKeyboardButton(text="Выгрузить данные", callback_data="load_data")
        clear_data = InlineKeyboardButton(text="Очистить базы", callback_data="clear_data")
        return_to_menu = InlineKeyboardButton(text="Вернуться в главное меню", callback_data="admin_panel")
        
        if data_loaded == False:
            report_kb.add(load_data, return_to_menu)
        else:
            report_kb.add(clear_data, return_to_menu)
        
        if data_cleared == True:
            report_kb = InlineKeyboardBuilder()
            return report_kb.add(InlineKeyboardButton(text="Вернуться в главное меню", callback_data="admin_panel")).as_markup()
            
        return report_kb.as_markup()
            
    async def linking_specs(form_id):
        spec_keyboard = InlineKeyboardBuilder()
        
        spec_data = await db.get_all_spec()
        btns = [InlineKeyboardButton(text=sp_name, callback_data=f'sp_{sp_id}_{form_id}') for sp_id, sp_name in spec_data]
        
        spec_keyboard.add(*btns)
        spec_keyboard.add(InlineKeyboardButton(text="Завершить", callback_data='end'))
        spec_keyboard.adjust(1)
        
        return spec_keyboard.as_markup()
            
    forms_keyboard: InlineKeyboardBuilder = forms_selection()
    
# ----------------------------------------------A-D-M-I-N-P-A-N-E-L----------------------------------------------

# ----------------------------------------------G-E-N-E-R-A-L-----------------------------------------------

# ----------------------------------------------G-E-N-E-R-A-L-----------------------------------------------

# -----------------------------------------S-P-E-C-I-A-L-I-S-T-P-A-N-E-L----------------------------------------------
class Specialist_keyboards():

    def main_menu() -> InlineKeyboardMarkup:
        main_menu_kb = InlineKeyboardBuilder()

        unanswered_questions = InlineKeyboardButton(text='Ответить на вопросы', callback_data='answer_the_question')
        upload_file = InlineKeyboardButton(text='Отправить файл\\сообщение', callback_data='complex_upload')
        main_menu_kb.add(unanswered_questions, 
                         upload_file)
        main_menu_kb.adjust(1)
        return main_menu_kb.as_markup()
    
    def sending_process() -> InlineKeyboardBuilder:
        sending_kb = InlineKeyboardBuilder()
        sending_kb.add(InlineKeyboardButton(text='Отменить отправку', callback_data='specialist_panel'))
        sending_kb.adjust(1)
        return sending_kb

    def questions_gen(flag = False, in_the_section: str = None) -> InlineKeyboardBuilder:
        '''
        Создание кнопок вопросов для специалиста
        '''
        specialist_starting_keyboard = InlineKeyboardBuilder()

        unanswered_questions = InlineKeyboardButton(text='Ответить на вопросы', callback_data='answer_the_question') if in_the_section == None else InlineKeyboardButton(text='Ответить на вопросы', callback_data=f'admin:{in_the_section}')
        
        specialist_starting_keyboard.add(unanswered_questions)
        specialist_starting_keyboard.add(InlineKeyboardButton(text="Вернуться к формам", callback_data="admin:back_unanswered")) if in_the_section != None else None

        specialist_starting_keyboard.adjust(1)
        return specialist_starting_keyboard.as_markup()
    
    def question_buttons(condition: str = None) -> InlineKeyboardMarkup:
        '''
        Создание кнопок для взаимодействия с вопросом
        '''
        question_keyboard = InlineKeyboardBuilder()
        if condition == None:
            choose_button = InlineKeyboardButton(text='Выбрать вопрос', callback_data=f'choose_question')
            close_button = InlineKeyboardButton(text='Закрыть вопрос', callback_data=f'close_question')
            check_history = InlineKeyboardButton(text='История диалога', callback_data=f'dialogue_history')
            question_keyboard.add(choose_button, close_button, check_history)
            question_keyboard.adjust(2)
            return question_keyboard.as_markup()
        elif isinstance(condition, tuple) == True:
            if condition[2] == 0 and condition[1] == 4:
                back_to_question = InlineKeyboardButton(text='Вернуться к вопросу', callback_data=f'back_to_question:{condition[0]}')
                next_page = InlineKeyboardButton(text="Следующая страница", callback_data=f"dialogue_history-limit:4&offset:4")
                question_keyboard.add(back_to_question, next_page)
                question_keyboard.adjust(1)
                return question_keyboard.as_markup()
            elif condition[2] != 0 and condition[1] == 4:
                back_to_question = InlineKeyboardButton(text='Вернуться к вопросу', callback_data=f'back_to_question:{condition[0]}')
                next_page = InlineKeyboardButton(text="Следующая страница", callback_data=f"dialogue_history-limit:4&offset:{condition[2] + 4}")
                prev_page = InlineKeyboardButton(text="Предыдущая страница", callback_data=f"dialogue_history-limit:4&offset:{condition[2] - 4}")
                question_keyboard.add(back_to_question, next_page, prev_page)
                question_keyboard.adjust(1)
                return question_keyboard.as_markup()
            elif condition[2] != 0 and condition[1] < 4:
                back_to_question = InlineKeyboardButton(text='Вернуться к вопросу', callback_data=f'back_to_question:{condition[0]}')
                prev_page = InlineKeyboardButton(text="Предыдущая страница", callback_data=f"dialogue_history-limit:4&offset:{condition[2] - 4}")
                question_keyboard.add(back_to_question, prev_page)
                question_keyboard.adjust(1)
                return question_keyboard.as_markup()
            elif condition[2] == 0 and condition[1] < 4:
                back_to_question = InlineKeyboardButton(text='Вернуться к вопросу', callback_data=f'back_to_question:{condition[0]}')
                question_keyboard.add(back_to_question)
                question_keyboard.adjust(1)
                return question_keyboard.as_markup()
            
    def publication_buttons(spec_forms = None, found_patterns: tuple = (), file_type: str = 'message', passed_forms_info = forms_data) -> InlineKeyboardBuilder:
        '''
        Данная функция принимает в себя обязательный аргумент form_type, за который закрепляется имя формы,
        а так же необязательные позиционные аргументы *args что представляют из себя 
        кнопки, которые необходимо выключить.
        Планируется, что в 
        '''

        if isinstance(spec_forms, str) != True:
            spec_forms = [form_name[1] for form_name in spec_forms] if spec_forms != None else ...
            spec_forms = {form_name:value for form_name in spec_forms for key, value in passed_forms_info.items() if key == form_name} if isinstance(passed_forms_info, dict) == True and spec_forms != None else {form_elem["form_name"]:forms_data.get(form_elem["form_name"]) for form_elem in passed_forms_info}

        public_kb = InlineKeyboardBuilder()
        if len(found_patterns) == 0:
            finish_redirectiong = InlineKeyboardButton(text="Завершить публикацию", callback_data="finish_state")
            
            if file_type == 'message':
                private_chat = InlineKeyboardButton(text="В личные сообщения пользователю", callback_data="private_message")
                section_chat = InlineKeyboardButton(text=f"В раздел формы {spec_forms}", callback_data=f"form_type:{spec_forms}") if isinstance(spec_forms, str) == True else [InlineKeyboardButton(text=f'В раздел формы {form_name}', callback_data=f'form_id:{form_id}&{file_type}') for form_name, form_id in spec_forms.items()]
                open_channel = InlineKeyboardButton(text="В открытый канал", callback_data="open_chat_public")
                public_kb.add(private_chat, section_chat, open_channel, finish_redirectiong) if isinstance(spec_forms, str) == True else public_kb.add(private_chat, *section_chat, open_channel, finish_redirectiong)
            else:
                section_chat = InlineKeyboardButton(text=f"В раздел формы {spec_forms}", callback_data=f"form_type:{spec_forms}&{file_type}") if isinstance(spec_forms, str) == True else [InlineKeyboardButton(text=f'В раздел формы {form_name}', callback_data=f'form_id:{form_id}&{file_type}') for form_name, form_id in spec_forms.items()]
                open_channel = InlineKeyboardButton(text="В открытый канал", callback_data=f"open_chat_public&{file_type}")
                public_kb.add(section_chat, open_channel, finish_redirectiong) if isinstance(spec_forms, str) == True else public_kb.add(*section_chat, open_channel, finish_redirectiong)

            public_kb.adjust(1)
            return public_kb.as_markup()
        else:
            if file_type == 'message':
                BUTTONS_DICT = {
                    'private': InlineKeyboardButton(text="В личные сообщения пользователю", callback_data="private_message"),
                    'form': InlineKeyboardButton(text=f"В раздел формы {spec_forms}", callback_data=f"form_type:{spec_forms}"),
                    'open': InlineKeyboardButton(text="В открытый канал", callback_data="open_chat_public")
                }
            else:
                BUTTONS_DICT = {
                    'form': InlineKeyboardButton(text=f"В раздел формы {spec_forms}", callback_data=f"form_type:{spec_forms}&{file_type}") if isinstance(spec_forms, dict) != True else [InlineKeyboardButton(text=f"В раздел формы {form_name}", callback_data=f"form_type:{form_id}&{file_type}") for form_name, form_id in spec_forms.items()],
                    'open': InlineKeyboardButton(text="В открытый канал", callback_data=f"open_chat_public&{file_type}")
                } 

            found_patterns = set(found_patterns)
            keys = set(BUTTONS_DICT.keys()) 

            resulted_buttons = [BUTTONS_DICT[elem] for elem in keys.difference(found_patterns)] if isinstance(BUTTONS_DICT['form'], list) == True else [BUTTONS_DICT[elem] for elem in keys.difference(found_patterns)]

            if isinstance(resulted_buttons, list):
                try:
                    public_kb.add(*resulted_buttons, InlineKeyboardButton(text="Завершить публикацию", callback_data="finish_state"))
                except ValueError:
                    public_kb.add(*resulted_buttons[0], InlineKeyboardButton(text="Завершить публикацию", callback_data="finish_state"))
            else:
                public_kb.add(*resulted_buttons, InlineKeyboardButton(text="Завершить публикацию", callback_data="finish_state"))
            public_kb.adjust(1)
            return public_kb.as_markup()
        
    def forward_buttons() -> InlineKeyboardMarkup:
        forward_keyboard = InlineKeyboardBuilder()
        
        private = InlineKeyboardButton(text='В личные сообщения пользователю', callback_data='private_public')
        form = InlineKeyboardButton(text='В раздел формы', callback_data='form_public')
        open_chat = InlineKeyboardButton(text='В открытый канал', callback_data='open_chat_public')
        end = InlineKeyboardButton(text='Выйти', callback_data='end_public')

        forward_keyboard.add(private, form, open_chat, end)
        forward_keyboard.adjust(1, repeat=True)
        return forward_keyboard.as_markup()
    
    def filters_menu_specialist() -> InlineKeyboardMarkup:
        '''
        Кнопки для меню с фильтрами
        '''
        filters_menu_keyboard = InlineKeyboardBuilder()

        regions_filter_button = InlineKeyboardButton(text='Выбрать регион', callback_data='regions_filter')
        question_type_button = InlineKeyboardButton(text='Выбрать тип вопроса', callback_data='question_type')
        show_questions_button = InlineKeyboardButton(text='Вывести вопросы', callback_data='show_questions')

        filters_menu_keyboard.add(regions_filter_button,
                                  question_type_button,
                                  show_questions_button)
        filters_menu_keyboard.adjust(1)
        return filters_menu_keyboard.as_markup()



# -----------------------------------------S-P-E-C-I-A-L-I-S-T-P-A-N-E-L----------------------------------------------
