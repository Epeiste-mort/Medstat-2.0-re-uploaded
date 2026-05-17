from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import FSInputFile
import json
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
import re
import datetime
import os
from copy import copy 
from html import escape

from keyboards import Admin_Keyboards, User_Keyboards, Specialist_keyboards
from db_actions import Database
from states import Admin_states, Specialist_states, User_states
from additional_functions import *
from cache_container import cache

db = Database()
router = Router()
message_int = MessageInteraction()

@router.callback_query(User_states.reg_organisation)
async def process_miac_selection(callback: types.CallbackQuery, state: FSMContext) -> None:
    '''
    Модуль с выбором МИАЦ
    '''
    if callback.data.startswith('district'):
        # После выбора федерального округа из callback_data извлекается его ID.
        # Формат данных ожидается как `district_<id>`.
        district_id = callback.data.split('_')[-1]
        # По ID округа строится следующая inline-клавиатура уже со списком регионов/областей.
        regions_keyboard = await User_Keyboards.create_regions_buttons(district_id=int(district_id))
        # Текущее сообщение не дублируется, а редактируется:
        # пользователь остается в одной последовательной цепочке выбора.
        await callback.message.edit_text('Выберите регион/область', reply_markup=regions_keyboard)
    elif callback.data.startswith('region'):
        # На втором шаге пользователь выбирает конкретный регион.
        # Из callback_data извлекается идентификатор региона в формате `region_<id>`.
        region_id = callback.data.split('_')[-1]
        # По выбранному региону из БД подтягивается связанный МИАЦ/субъект,
        # который потом сохраняется как часть регистрационной анкеты.
        miac_name = await db.get_miac_information(info_type='miac', miac_id=int(region_id))
        # Состояние регистрации сохраняется тем же,
        # потому что сценарий еще не завершен и дальше продолжается сбор данных пользователя.
        await state.set_state(User_states.reg_organisation)
        # В FSM-контекст записывается выбранный субъект (`subject`),
        # чтобы затем использовать его при сохранении формы регистрации в БД.
        await state.update_data(subject=miac_name)
        # После выбора региона пользователь переводится с inline-этапа
        # на обычный текстовый ввод названия места работы.
        await callback.message.edit_text('Введите название вашего места работы')

@router.callback_query(User_states.neuro_process)
async def catch_questions(callback: types.CallbackQuery, state: FSMContext):
    callback_data = callback.data
    data = await state.get_data()
    
    try:
        bot_answer = data["bot_answer"]
    except KeyError:
        return await callback.answer(text="Просим отправить ваш вопрос по указанной вами форме")
    
    try:
        user_msg = data["user_message"]
        temp_msg = data["temp_msg"]
        
        if callback_data == "redirect_question":
            await question_redirect(query=user_msg, state=state)
            await callback.answer(text="Вопрос успешно обработан")
            await message_delition(*bot_answer, temp_msg, time_sleep=0)
            await state.update_data(bot_answer=None)
            await state.set_state(User_states.form_choosing)
        elif callback_data == "chose_reply":
            chosen_answer = re.findall(pattern=r"<b>Ответ №\d:<\/b>(.+)", string=callback.message.html_text)[0] 
            await state.update_data(chosen_answer=chosen_answer)
            await question_redirect(query=user_msg, state=state, q_state="Accept", succes_answered=True)
            await callback.answer(text="Вопрос успешно обработан")
            await message_delition(*bot_answer, temp_msg, time_sleep=0)
            await state.update_data(bot_answer=None)
            await state.set_state(User_states.form_choosing)
        elif callback_data.startswith("sec"):
            if bot_answer:
                await callback.answer(text="Выберете опцию из предложенных - 'Передать вопрос' или 'Выбрать ответ'") 
            else:
                await callback.answer(text="Просим отправить ваш вопрос по указанной вами форме")
                    
    except (TypeError, KeyError, TelegramBadRequest):
        if bot_answer:
            await callback.answer(text="Выберете опцию из предложенных - 'Передать вопрос' или 'Выбрать ответ'") 
        else:
            await callback.answer(text="Просим отправить ваш вопрос по указанной вами форме")
               
@router.callback_query(Specialist_states.complex_public)
async def non_message_data(callback: types.CallbackQuery, state: FSMContext) -> None:
    from non_script_files.config import forms_data, RASDEL_FORM
    from cache_container import cache
    from main import bot

    if 'other' in callback.data:
        data = await state.get_data()
        menu_id = callback.message.message_id
        file_dict, file_id = data[f'query_format_info:{menu_id}'], data[f'file_id:{menu_id}']
        menu_cache = await cache.get(f"publication_menu:{data[f'publication_menu:{menu_id}'].message_id}") ; menu_cache = json.loads(menu_cache)
        spec_forms = await db.get_specform(user_id=callback.from_user.id)

        if 'form' in callback.data:
            form_id = int(re.findall(r"\d\d?", callback.data)[0])            

            for key, value in forms_data.items():
                if key in menu_cache: 
                    continue

                if value == form_id:
                    form_type = key
                    break
            
            menu_cache.append(form_type)
            passed_forms = list(filter(lambda x: x["form_name"] not in menu_cache, spec_forms))
            found_patterns = ("open", ) if "open" in menu_cache else ()
            await cache.set(f"publication_menu:{data[f'publication_menu:{menu_id}'].message_id}", json.dumps(menu_cache))

            match file_dict['query_format']:
                case 'Document': await bot.send_document(chat_id=RASDEL_FORM, 
                                                         document=file_id, message_thread_id=forms_data[form_type], 
                                                         caption=file_dict['caption_text'])
                case 'Photo': pass
                case 'Video': pass
                case 'Text': await bot.send_message(chat_id=RASDEL_FORM,
                                                    message_thread_id=forms_data[form_type],
                                                    text=data["not_attached_caption"])

            await callback.message.edit_reply_markup(inline_message_id=str(data[f'publication_menu:{menu_id}'].message_id), reply_markup=Specialist_keyboards.publication_buttons(file_type='other', passed_forms_info=passed_forms, found_patterns=found_patterns))
            message = await callback.message.reply(f'Информация отправлена в канал формы: {form_type}')
            await message_delition(message, time_sleep=10)
            await db.add_suggestion_to_post(post_content=file_id, post_suggestor=callback.from_user.id, pub_type_tuple=tuple(file_dict.values()), pub_state='Accept')
        elif 'open_chat' in callback.data:
            menu_cache.append("open") ; await cache.set(f"publication_menu:{data[f'publication_menu:{menu_id}'].message_id}", json.dumps(menu_cache))
            passed_forms = list(filter(lambda x: x["form_name"] not in menu_cache, spec_forms))
            await callback.message.edit_reply_markup(inline_message_id=str(data[f'publication_menu:{menu_id}'].message_id), reply_markup=Specialist_keyboards.publication_buttons(file_type='other', passed_forms_info=passed_forms, found_patterns=('open', )))
            message = await callback.message.answer('Запрос на публикацию в открытом канале отправлен')
            await message_delition(message, time_sleep=10)
            await db.add_suggestion_to_post(post_content=file_id, post_suggestor=callback.from_user.id, pub_type_tuple=tuple(file_dict.values()))
    if callback.data == 'finish_state':
        await callback.answer(text='Вы успешно завершили процесс')
        await callback.message.delete()
        message = await callback.message.answer('Теперь вы можете вернуться в главное меню или опубликовать другой файл')
        await message_delition(message, time_sleep=10)

@router.callback_query(Specialist_states.public_choose_message)
async def redirecting_data(callback: types.CallbackQuery, state: FSMContext) -> None:
    '''Обработка текстовых сообщений - вопрос-ответов'''
    from main import bot
    from cache_container import Data_storage
    from keyboards import BUTTONS_TO_NUMBER
    from non_script_files.config import forms_data, RASDEL_FORM

    await state.set_state(Specialist_states.choosing_question)
    data = await state.get_data()
    
    def callback_addition():
        nonlocal BUTTONS_TO_NUMBER, Data_storage
        found_data = []
        for row in Data_storage.callback_texts:
            for pattern in BUTTONS_TO_NUMBER.keys():
                if pattern in row:
                    found_data.append(pattern)
        return set(found_data)
    
    question_text = data['question']
    message_int.parse_message(question_text)
    question_message_id = await db.get_question_message_id(question_id=data['question_id'])
    question = message_int.question
    
    if not data['user_id']:
        lp_user_id = db.get_user_id(question=question_text, message_id=data["question_message"])
        tuple_of_info = await db.get_lp_user_info(lp_user_id=lp_user_id)
    else:
        tuple_of_info = await db.get_lp_user_info(lp_user_id=data['user_id'])
        
    user_id = tuple_of_info[1][1]
    
    form_type: str = message_int.form_name
    form_type_orig = copy(form_type.strip())
    form_type = form_type[:25] + "..." if len(form_type) > 25 else form_type

    try:
        await bot.edit_message_text(text=f'<b>Вы выбираете тип публикации для этого вопроса</b>\n{question_text}', chat_id=callback.from_user.id, message_id=data['question_message'])
    except TelegramBadRequest:
        pass
    await state.set_state(Specialist_states.public_choose_message)

    Data_storage.callback_texts.append(callback.data)
    await db.answer_process_report(question_id=int(data['question_id']),
                                     answer=data['spec_answer'],
                                     specialist_id=callback.from_user.id)
    
    if callback.data == "private_message":
        found_data = tuple(callback_addition())
        await callback.message.edit_reply_markup(inline_message_id=str(data['menu'].message_id), reply_markup=Specialist_keyboards.publication_buttons(spec_forms=form_type, found_patterns=found_data))
        await bot.send_message(chat_id=user_id, text=f'<b>Вопрос:</b> {question}\n<b>Ответ</b>: {data["spec_answer"]}', reply_to_message_id=question_message_id)
        message = await callback.message.reply(f'Ответ отправлен пользователю в личные сообщения')
        await message_delition(message, time_sleep=10)
    elif "form_type" in callback.data:
        found_data = tuple(callback_addition())
                
        try:
            await bot.send_message(chat_id=RASDEL_FORM, text=f'<b>Вопрос</b>:{question}\n\n<b>Ответ</b>: {data["spec_answer"]}', message_thread_id=forms_data[form_type_orig])
            await callback.message.edit_reply_markup(inline_message_id=str(data['menu'].message_id), reply_markup=Specialist_keyboards.publication_buttons(spec_forms=form_type, found_patterns=found_data))
            query_dict, file_id = extracting_query_info(query=callback)
            await db.add_suggestion_to_post(post_content=f'{question}\n<b>Ответ</b>: {data["spec_answer"]}', post_suggestor=callback.from_user.id, pub_type_tuple=tuple(query_dict.values()), pub_state='Accept')
            message = await callback.message.reply(f'Ответ отправлен в канал формы: {form_type_orig}')
            await message_delition(message, time_sleep=10)
        except KeyError as err:
            await callback.answer(text=f"Произошла ошибка при отправке сообщения в раздел формы {form_type_orig}...")
        
    elif callback.data == 'open_chat_public':
        found_data = tuple(callback_addition())
        query_dict, file_id = extracting_query_info(query=callback)
        await state.update_data(query_format='Answer')
        await db.add_suggestion_to_post(post_content=f'<b>Вопрос</b>:{question}\n\n<b>Ответ</b>: {data["spec_answer"]}', post_suggestor=callback.from_user.id, pub_type_tuple=tuple(query_dict.values()))
        message = await callback.message.answer('Запрос на публикацию в открытом канале отправлен')
        await callback.message.edit_reply_markup(inline_message_id=str(data['menu'].message_id), reply_markup=Specialist_keyboards.publication_buttons(spec_forms=form_type, found_patterns=found_data))
        await message_delition(message, time_sleep=10)
    elif callback.data == 'finish_state':
        await bot.edit_message_text(text=f'<b>Вы успешно ответили на этот вопрос</b>\n{question_text}', chat_id=callback.from_user.id, message_id=data['question_message'])
        await callback.answer(text='Вы успешно завершили процесс')
        await callback.message.delete()
        message = await callback.message.answer('Теперь вы можете выбирать другие вопросы для ответа')
        await state.set_state(Specialist_states.choosing_question)
        await message_delition(message, time_sleep=10)
        
@router.callback_query(Specialist_states.choosing_question)
async def process_answers(callback: types.CallbackQuery, state: FSMContext) -> None:
    from additional_functions import choose_form, create_questions
    '''
    Выбор вопроса специалистом
    '''
    data = await state.get_data()
    search_filter = data['custom_filter']
    if 'dialogue_history' in callback.data:
        from cache_container import Data_storage
        message_int.parse_message(callback.message.html_text)
        page_number = 1
        history_text = "" ; NEXT_STRING = "\n"

        if "limit" in callback.data or "offset" in callback.data:
            passed_values = callback.data.split("&") ; passed_values = passed_values[1].split(":") ; passed_values = int(passed_values[1])
            page_number = 1 if passed_values == 4 else passed_values // 4 
            information_tuple = await db.get_user_history(question_id=Data_storage.question_id, values_range=[4, 4 * page_number])
        else:
            message_id = int(message_int.message_id)
            question_info = message_int.question
            Data_storage.question_id = await db.get_question_id(message_id=message_id)
            information_tuple = await db.get_user_history(question_id=Data_storage.question_id)

        history = information_tuple[0] ; history = list(history.items())
        try:
            user_full_identification = list(information_tuple[1])
        
            for i in range(len(history)):
                history_text += f"""{''.join([f'{elem[0]} - {elem[1]}{NEXT_STRING}' for elem in list(history[i][1].items())])}\n\n"""
            history_text += f"Номер страницы: {page_number + 1}"
            await callback.message.edit_text(text=history_text, reply_markup=Specialist_keyboards.question_buttons(condition=(Data_storage.question_id, information_tuple[2], 4 * page_number)))
        except TypeError: await callback.answer(text="Данные о пользователе поменялись или пользователь был удален из баз данных, в связи с чем нет возможности вывести историю диалога с ним...")
    elif 'answer_the_question' in callback.data:
        custom_filter = SearchFilter(specialist_id=callback.from_user.id)
        questions = await create_questions(questions_filter=custom_filter)
        await callback.message.edit_text('Выберите вопрос')
        message_ids = []
        for question in questions:
            lp_user_info = await db.get_lp_user_info(lp_user_id=question['lp_user_id'])
            user_name = lp_user_info[0][1]
            try:
                message = await callback.message.answer(f'<b>Пользователь:</b> {user_name}\n<b>Субъект:</b> {question["subject_name"]}\n<b>Форма:</b> {question["form_name"]}\n<b>Вопрос:</b> {question["question"]}\n<s>{question["message_id"]}</s>\n\n<b>Ответ:</b> {question["spec_answer"]}', 
                                                reply_markup=Specialist_keyboards.question_buttons())
            except KeyError:
                text = message_int.create_message(user_id=user_name,
                                              subject=question['subject_name'],
                                              form_name=question['form_name'],
                                              question=question['question'],
                                              message_id=question['message_id'],
                                              question_date=question['question_date'])
                message = await callback.message.answer(text=text, 
                                                    reply_markup=Specialist_keyboards.question_buttons())
            message_ids.append(message.message_id)
        await callback.message.answer('Если вопросы закончились (нет больше кнопок у них), то нажмите здесь кнопку для генерации новых',
                                    reply_markup=Specialist_keyboards.questions_gen())
        try:
            await state.update_data(message_ids=message_ids)
        except UnboundLocalError:
            pass
    elif callback.data == 'choose_question':
        message_int.parse_message(callback.message.html_text)
        markup = InlineKeyboardBuilder()
        message_id = int(message_int.message_id)
        question_info = message_int.question
        question_id = await db.get_question_id(message_id=message_id)
        result_check = await db.check_question(question_id=question_id, message_id=message_id)
        lp_user_id = await db.get_user_id(question=question_info, message_id=message_id)
        
        # if result_check == 'Вопрос взят':
        #     await callback.message.edit_text(f'<b>Вопрос взят</b>\n{callback.message.html_text}')
        #     await callback.message.answer('Выберите другой вопрос, так как на этот уже отвечает другой специалист')
        # else:
        #     try:
        #         await db.answer_process_report(question_id=int(question_id),
        #                              answer='Вопрос взят',
        #                              specialist_id=callback.from_user.id)
        await callback.message.edit_reply_markup(reply_markup=markup.as_markup())
        edit = await callback.message.edit_text(f'<b>Выбранный вопрос</b>\n{callback.message.html_text}')
        await callback.message.answer('Введите свой ответ')
        await state.set_state(Specialist_states.answer_question)
        await state.update_data(question_id=question_id, question_message=edit.message_id,
                                question=callback.message.html_text,
                            user_id=lp_user_id)
            # except TypeError:
            #     print(f"Произошла ошибка обработки сообщения: message_id={message_id}, question_info={question_info}")    
    elif callback.data == 'close_question':
        message_int.parse_message(callback.message.html_text)
        message_id = int(message_int.message_id)
        question_info = message_int.question
        question_id = await db.get_question_id(message_id=message_id)
        print("ID сообщения -", question_id)
        try:
            await db.answer_process_report(question_id=int(question_id),
                                 answer='Закрытие вопроса',
                                 specialist_id=callback.from_user.id)
            await callback.message.edit_text(f'<b>Вопрос закрыт</b>\n{callback.message.html_text}')
        except TypeError: await callback.answer(text="ID вопроса неопределен, просим связаться с разработчиками и передать номер вопроса, обозначенный после 'Дата вопроса'")
    elif 'back_to_question' in callback.data:
        questions = await create_questions(questions_filter=search_filter)
        question_id = callback.data ; question_id = question_id.split(":") ; question_id = int(question_id[1])
        question_info = await db.get_question_id(inputed_question_id=question_id)

        data = {'question': question_info['question_content'],
                'lp_user_id': question_info['lp_user_id'],
                'form_name': question_info['form_name'],
                'message_id': question_info['question_message'],
                'subject_name': question_info['subject_name'],
                'question_date': question_info['question_date']}
        
        lp_user_info = await db.get_lp_user_info(lp_user_id=data['lp_user_id']) ; user_name = lp_user_info[0][3]
        text = message_int.create_message(user_id=user_name,
                                              subject=data['subject_name'],
                                              form_name=data['form_name'],
                                              question=data['question'],
                                              message_id=data['message_id'],
                                              question_date=data['question_date'])
        message = await callback.message.edit_text(text=text, 
                                        reply_markup=Specialist_keyboards.question_buttons())
    elif "admin" in callback.data:
        from additional_functions import create_questions
        callback_data = callback.data.split(":")[1]
        
        if "back" not in callback_data:
            await state.set_state(Admin_states.answers_form)
            data = await state.get_data()
            operation_type = data["operation_type"]
            await state.set_state(Specialist_states.choosing_question)
            flag = False
            if operation_type == "unanswered":
                questions = await create_questions(callback.from_user.id, form=callback_data)
            else:
                questions = await create_questions(callback.from_user.id, question_status="Accept", form=callback_data)
                flag = True
            await callback.message.edit_text('Выберите вопрос')
            message_ids = []
            for question in questions:
                lp_user_info = await db.get_lp_user_info(lp_user_id=question['lp_user_id'])
                user_name = lp_user_info[0][1]
                try:
                    message = await callback.message.answer(f'<b>Пользователь:</b> {user_name}\n<b>Субъект:</b> {question["subject_name"]}\n<b>Форма:</b> {question["form_name"]}\n<b>Вопрос:</b> {question["question"]}\n<s>{question["message_id"]}</s>\n\n<b>Ответ:</b> {question["spec_answer"]}', 
                                                reply_markup=Specialist_keyboards.question_buttons())
                except KeyError:
                    message = await callback.message.answer(f'<b>Пользователь:</b> {user_name}\n<b>Субъект:</b> {question["subject_name"]}\n<b>Форма:</b> {question["form_name"]}\n<b>Вопрос:</b> {question["question"]}:\n<s>{question["message_id"]}</s>', 
                                                    reply_markup=Specialist_keyboards.question_buttons())
                message_ids.append(message.message_id)
            await callback.message.answer('Если вопросы закончились (нет больше кнопок у них), то нажмите здесь кнопку для генерации новых',
                                        reply_markup=Specialist_keyboards.questions_gen(flag=flag, in_the_section=callback_data))
            try:
                await state.update_data(message_ids=message_ids)
            except UnboundLocalError:
                pass
        else:
            operation_type = callback_data.split("_")[1]
            
            if operation_type == "unanswered":
                forms = await choose_form(user_id=callback.from_user.id, callback=callback, user_type="Admin")
                questions = await create_questions(callback.from_user.id)
            elif operation_type == "answered":
                forms = await choose_form(user_id=callback.from_user.id, callback=callback, user_type="Admin", question_status="Accept")
                questions = await create_questions(callback.from_user.id, question_status="Accept")
            
            if forms is True:
                await state.set_state(Admin_states.answers_form)
                await state.update_data(operation_type=operation_type)
                return
        
@router.callback_query(Admin_states.delete_member)
async def delete_chat_members(callback: types.CallbackQuery, state: FSMContext) -> None:
    '''
    Удаление пользователя из чата
    '''
    data = await state.get_data()
    ids = data['ids_to_delete']
    from non_script_files.config import COORD_CHAT 
    from additional_functions import delete_member
    if callback.data == 'coord_chat':
        await delete_member(message=ids, chat_id=COORD_CHAT)
    await state.clear()
    await callback.message.answer('Пользователь удален из чата', 
                                  reply_markup=Admin_Keyboards.main_menu())

@router.callback_query(User_states.form_choosing)
async def process_starting_general(callback: types.CallbackQuery, state: FSMContext) -> None:
    from non_script_files.config import COORD_CHAT
    '''
    Обработка запросов от inline-кнопок форм
    '''
    from main import bot
    from non_script_files.config import COORD_CHAT
    
    if callback.data == 'sec_ten':
        link = await bot.create_chat_invite_link(chat_id=COORD_CHAT,
                                          name='Чат координаторов',
                                          member_limit=1)
        await callback.message.answer(text=f'Ссылка на чат координаторов {link.invite_link}')
        await callback.message.edit_text(text='Меню', reply_markup=await User_Keyboards.main_menu(True, user_id=callback.from_user.id))
        await state.clear()
    elif callback.data == 'main_menu':
        await callback.message.edit_text('Меню', reply_markup=await User_Keyboards.main_menu(True, user_id=callback.from_user.id))
        await state.clear()
    elif callback.data.startswith("sec"):
        await state.update_data(tag=callback.data)
        form_info = await db.extract_form_info_by_tag(tag_info=callback.data)
        await state.update_data(form_info=form_info)
        data = await state.get_data()
        form_name_for_alert = form_info["form_name"][:40] + "..." if len(form_info["form_name"]) > 40 else form_info["form_name"]
        await callback.answer(text=f'Вы выбрали форму для отправки - {form_name_for_alert}. Теперь, введите Ваш вопрос', show_alert=True)
        
        try:
            if data["notific_message"]:
                await message_delition(data["notific_message"], time_sleep=0)
            else:
                pass
        except KeyError:
            pass
        
        try:
            await callback.message.edit_text(inline_message_id=str(data["notific_message"].message_id), text=f"Вы выбрали форму для отправки - {form_info['form_name']}. Для возврата в меню, воспользуйтесь кнопкой 'Возврат в главное меню'", reply_markup=User_Keyboards.section_chose().as_markup())
        except TelegramBadRequest:
            pass

        await state.set_state(User_states.neuro_process)
        
@router.callback_query(Admin_states.registration_process)
async def process_admin(callback: types.CallbackQuery, state: FSMContext) -> None:
    page_value = 1
    '''
    Обработка запросов от inline-кнопок admin-a
    '''
    callback_data = callback.data
    from main import bot
    from non_script_files.config import COORD_CHAT
    if 'dec_app' in callback_data:
        callback_data = callback_data.split(":")
        try:
            await bot.send_message(chat_id = int(callback_data[1]), text="Ваша заявка была отклонена")
        except TelegramForbiddenError:
            pass
        await db.update_registration_status(string_id=callback_data[2],
                                            admin_id=callback.from_user.id,
                                            reg_status="Decline")
        data = await state.get_data()
        page = int(data['page'])
        await callback.answer(text="Вы отклонили заявку")
        await callback.message.edit_text(text="Выберете заявку из предложенных. Если нету кнопок, прикрепленных к данному сообщению, то заявки не сформировались - вернитесь к данному меню позже", 
                                         reply_markup=Admin_Keyboards.application_gen(page_value=page, unreg_tuple=await db.get_unregistered(passed_values=10*(page - 1), available_values=10)).as_markup())             
    elif 'acc_app' in callback_data:
        from non_script_files.config import COORD_CHAT
        callback_data = callback_data.split(":")
        link = await bot.create_chat_invite_link(chat_id=COORD_CHAT,
                                          name='Чат координаторов',
                                          member_limit=1)
        try:
            await bot.send_message(chat_id=int(callback_data[1]),
                                    text=f'Ваша заявка была подтверждена\nПройдите по данной ссылке и заполните дополнительную информацию {link.invite_link}')
        except TelegramForbiddenError:
            pass
        await db.update_registration_status(string_id=callback_data[2],
                                            admin_id=callback.from_user.id,
                                            reg_status="Accept")
        data = await state.get_data()
        page = int(data['page'])
        await callback.answer(text="Вы приняли заявку")
        await callback.message.edit_text(text="Выберете заявку из предложенных. Если нету кнопок, прикрепленных к данному сообщению, то заявки не сформировались - вернитесь к данному меню позже", 
                                         reply_markup=Admin_Keyboards.application_gen(page_value=page, unreg_tuple=await db.get_unregistered(passed_values=10*(page - 1), available_values=10)).as_markup())             
    elif "generated" in callback_data:
        cb_data = callback.data ; cb_data = cb_data.split("&") ; cb_data = cb_data[1].split(":") ; callback_id = int(cb_data[1])
        info_tuple = await db.get_massive_of_values(form_id=callback_id)
        form_info_list, user_info_list = info_tuple[0], info_tuple[1]
        information_panel = f"""Название субъекта: {form_info_list[2]},\nДолжность: {form_info_list[3]},\nМесто работы(организация): {form_info_list[4]},\nДата регистрации: {form_info_list[5]}"""
        await callback.message.edit_text(text=information_panel, reply_markup=Admin_Keyboards.reg_process_keyboard(form_info_list[1], user_info_list[0]).as_markup())
    elif callback_data == 'check_reg':
        await callback.message.edit_text(text="Выберете заявку из предложенных. Если нету кнопок, прикрепленных к данному сообщению, то заявки не сформировались - вернитесь к данному меню позже", 
                                         reply_markup=Admin_Keyboards.application_gen(page_value=page_value, unreg_tuple=await db.get_unregistered()).as_markup())
        await state.update_data(page='1')
    elif "next_page" in callback_data or "prev_page" in callback_data:
        page_value = callback_data.split(":") ; page_value = int(page_value[1])
        await callback.message.edit_text(text="Выберете заявку из предложенных. Если нету кнопок, прикрепленных к данному сообщению, то заявки не сформировались - вернитесь к данному меню позже", 
                                         reply_markup=Admin_Keyboards.application_gen(page_value=page_value, unreg_tuple=await db.get_unregistered(passed_values=10*(page_value - 1), available_values=10)).as_markup())
        await state.update_data(page=page_value)

@router.callback_query(User_states.file_date)
async def process_getting_files(callback: types.CallbackQuery, state: FSMContext):
    from main import bot
    from keyboards import general_kb
    data = await state.get_data()
    button_type = data['button_type']
    chat_id = callback.from_user.id
    file_info = await db.loading_files(button_type=button_type, time=callback.data)
    for row in file_info:
        if row["file_format"]["caption_text"] == "Null":
            await bot.send_document(chat_id=chat_id, document=row["file_id"])
        else:
            await bot.send_document(chat_id=chat_id, caption=row["file_format"]["caption_text"], document=row["file_id"])

    await state.clear()
    await callback.message.answer(text='Вернитесь в главное меню по кнопке внизу вашего экрана', 
                                  reply_markup=general_kb)
    
@router.callback_query(Admin_states.delete_file)
async def process_delete_file(callback: types.CallbackQuery, state: FSMContext):
    from main import bot
    from non_script_files.config import OPEN_CHANNEL
    if 'delete_choosen_file' in callback.data:
        id = int(callback.data.split(':')[1])
        data = await state.get_data()
        files = data['file_name']
        file_name = files[id]
        await db.delete_files(file_id=id)
        await callback.answer(text='Файл удален',
                              show_alert=True)
        await bot.send_message(chat_id=OPEN_CHANNEL,
                               text=f'Файл {file_name} удален из чат-бота')
        await callback.message.delete()
    elif callback.data == 'close_operation':
        await callback.message.edit_text(text='Меню',
                                         reply_markup=Admin_Keyboards.main_menu())
        await state.clear()
    else:
        files = await db.get_files_to_delete(button_type=callback.data)
        chat_id = callback.from_user.id
        file_names = {}
        for row in files:

            if row["file_format"]["caption_text"] == "Null":
                await bot.send_document(chat_id=chat_id, 
                                        document=row["file_id"], 
                                        reply_markup=Admin_Keyboards.delete_file(id=row["id"], file_name=row["file_format"]["file_name"]))
            else:
                await bot.send_document(chat_id=chat_id, 
                                        caption=row["file_format"]["caption_text"], 
                                        document=row["file_id"],
                                        reply_markup=Admin_Keyboards.delete_file(id=row["id"], file_name=row["file_format"]["file_name"]))
            file_names[row["id"]] = row["file_format"]["file_name"]
        await state.update_data(file_name=file_names)
        await callback.message.answer(text='Чтобы вернуться в главное меню нажмите кнопку',
                                      reply_markup=Admin_Keyboards.close_operation())

@router.callback_query(Admin_states.post_publication)
async def process_open_chat_publication(callback: types.CallbackQuery, state: FSMContext) -> None:
    '''
    Обработка публикации в открытом канале
    '''
    from main import bot
    from non_script_files.config import OPEN_CHANNEL
    if 'accept_post' in callback.data:
        pub_type = callback.data.split("&") ; pub_type = pub_type[1].split(":") ; pub_type = pub_type[1]
        pub_id = callback.data.split("&") ; pub_id = pub_id[2].split(":") ; pub_id = pub_id[1]
        
        match pub_type.capitalize():
            case 'Text': 
                await bot.send_message(chat_id=OPEN_CHANNEL, text=callback.message.html_text)
                await callback.message.edit_text(text=f'<b>Вы одобрили публикацию этого поста</b>\n{callback.message.html_text}')
            case 'Document': 
                await bot.send_document(chat_id=OPEN_CHANNEL, document=callback.message.document.file_id, caption=callback.message.html_text)
                await callback.message.edit_caption(caption=f'<b>Вы одобрили публикацию этого поста</b>\n{callback.message.html_text}')

        await db.update_publication_status(pub_id=int(pub_id),
                                           publication_status='Accept')
    elif 'decline_post' in callback.data:
        pub_type = callback.data.split("&") ; pub_type = pub_type[1].split(":") ; pub_type = pub_type[1]
        pub_id = callback.data.split("&") ; pub_id = pub_id[2].split(":") ; pub_id = pub_id[1]
        
        match pub_type.capitalize():
            case 'Text': 
                await callback.message.edit_text(text=f'<b>Вы отклонили этот пост</b>\n{callback.message.html_text}')
            case 'Document': 
                await callback.message.edit_caption(caption=f'<b>Вы отклонили этот пост</b>\n{callback.message.html_text}')

        await db.update_publication_status(pub_id=int(pub_id), 
                                           publication_status='Decline')
    elif callback.data == 'publications':
        publications = await db.get_posts_to_public()
            
        for publication in publications:
            try:
                if publication['publication_type']['publication_format'] == 'Text':
                    await callback.message.answer(text=publication['publication_type']['caption_text'], reply_markup=Admin_Keyboards.post_publication(post_id=publication['id']))
                elif publication['publication_type']['publication_format'] == 'Answer':
                    await callback.message.answer(text=publication['publication_content'], reply_markup=Admin_Keyboards.post_publication(post_id=publication['id']))
                elif publication['publication_type']['publication_format'] == 'Document': 
                    await bot.send_document(chat_id=callback.from_user.id, caption=publication['publication_type']['caption_text'], document=publication['publication_content'], reply_markup=Admin_Keyboards.post_publication(pub_type='document', post_id=publication['id']))
            except TypeError:
                continue
        await callback.message.answer(text='Если публикации закончились (нет больше кнопок у них), то нажмите здесь кнопку для генерации новых', reply_markup=Admin_Keyboards.pub_refresh())
        await state.set_state(Admin_states.post_publication)
        
@router.callback_query(Admin_states.file_loading)
async def upload_file(callback: types.CallbackQuery, state: FSMContext) -> None:
    from cache_container import Data_storage
    from main import bot
    if callback.data == "npa":
        await state.update_data(folder_type="npa")
        data = await state.get_data()
        await callback.message.edit_text(inline_message_id=str(data['inline_menu'].message_id), text="Прикрепите файл(ы) и при необходимости добавьте описание. Для завершения процесса отправки нажмите на кнопку 'Завершить загрузку'. В противном случае загруженные вами файлы НЕ загрузятся в систему. Для отмены действия вернитесь в главное меню, нажав на соответствующую кнопку.", reply_markup=Admin_Keyboards.file_loading(True))
    elif callback.data == "medstat":
        await state.update_data(folder_type="medstat")
        data = await state.get_data()
        await callback.message.edit_text(inline_message_id=str(data['inline_menu'].message_id), text="Прикрепите файл(ы) и при необходимости добавьте описание. Для завершения процесса отправки нажмите на кнопку 'Завершить загрузку'. В противном случае загруженные вами файлы НЕ загрузятся в систему. Для отмены действия вернитесь в главное меню, нажав на соответствующую кнопку.", reply_markup=Admin_Keyboards.file_loading(True))
    elif callback.data == "statistic":
        await state.update_data(folder_type="statistic")
        data = await state.get_data()
        await callback.message.edit_text(inline_message_id=str(data['inline_menu'].message_id), text="Прикрепите файл(ы) и при необходимости добавьте описание. Для завершения процесса отправки нажмите на кнопку 'Завершить загрузку'. В противном случае загруженные вами файлы НЕ загрузятся в систему. Для отмены действия вернитесь в главное меню, нажав на соответствующую кнопку.", reply_markup=Admin_Keyboards.file_loading(True))
    elif callback.data == "method_recommendations":
        await state.update_data(folder_type="method_recommendations")
        data = await state.get_data()
        await callback.message.edit_text(inline_message_id=str(data['inline_menu'].message_id), text="Прикрепите файл(ы) и при необходимости добавьте описание. Для завершения процесса отправки нажмите на кнопку 'Завершить загрузку'. В противном случае загруженные вами файлы НЕ загрузятся в систему. Для отмены действия вернитесь в главное меню, нажав на соответствующую кнопку.", reply_markup=Admin_Keyboards.file_loading(True))
    elif callback.data == "check_loaded":
        data = await state.get_data()
        try:
            files = data["file_sending_process"]
        except KeyError:
            await callback.answer(text="Вы ещё не загрузили файлы")
            return None
        loaded_text = "Ниже представлены файлы и подписи к ним, которые вы загрузили в текущей сессии.\n\n"
        
        for dict_instance in files.values(): 
            string = f'{dict_instance["file_name"]}: {dict_instance["caption_text"]}\n'
            loaded_text += "------------------------------------------------------------------------------------------\n" + string + "------------------------------------------------------------------------------------------\n\n"
        
        txt_report = save_to_txt(loaded_files=f"{datetime.datetime.now()}\n\n{loaded_text}", save_mode="w+")
        txt_report = FSInputFile('loaded_files.txt')
        
        try:
            await callback.message.edit_text(text=loaded_text, reply_markup=Admin_Keyboards.file_loading(True))
        except TelegramBadRequest: 
            try:
                await callback.message.edit_text(text=loaded_text[:4096], reply_markup=Admin_Keyboards.file_loading(True))
            except TelegramBadRequest:
                pass
            await bot.send_document(chat_id=Data_storage.user_id, document=txt_report, caption="В случае, если телеграм обрезает сообщение, высылается файл со всей информацией текущей сессии")
        
    elif callback.data == "cancel_loading":
        data = await state.get_data()
        
        match data["folder_type"]:
            case 'npa':
                folder_type = "НПА"
            case 'medstat':
                folder_type = "Медстат"
            case 'statistic':
                folder_type = "Статистика"
            case 'method_recommendations':
                folder_type = "Методические рекомендации"
        
        files = data["file_sending_process"]
        await document_loading(button_name=data['folder_type'], doc_info=files)
        from non_script_files.config import OPEN_CHANNEL
        files_info = ""
        for file_info in files.values():
            file_name = file_info.get('file_name')
            caption_text = file_info.get('caption_text')

            if file_name and caption_text:
                files_info += f"- {file_name}\n\t\t{caption_text}\n"
        await bot.send_message(chat_id=OPEN_CHANNEL, text=f'В раздел файлов <b>{folder_type}</b> загружен/ы файл/ы:\n {files_info}')
        menu = await callback.message.edit_text(inline_message_id=str(data['inline_menu'].message_id), text="Процесс загрузки в форму успешно завершен. Выберете в какой раздел загружать файлы", reply_markup=Admin_Keyboards.file_loading())
        await state.update_data(inline_menu=menu)

@router.callback_query(Admin_states.report_ending)
async def rep_ending_proc(callback: types.CallbackQuery, state: FSMContext):
    from main import bot
    if callback.data == 'admin_panel':
        await state.clear()
        menu = await callback.message.edit_text(text="Добро пожаловать в Админ-панель", reply_markup=Admin_Keyboards.main_menu())
        await state.update_data(main_menu=menu)
    elif callback.data == "load_data":
        await callback.message.edit_text(text="Перед обновлением баз удостоверьтесь в том, что данные по зарегистрированным пользователям в текущем отчетном году сохранены. Для этого в главном меню нажмите кнопку 'Данные о зарегистрированных'.\nОбнуление затрагивает следующие базы данных:\n1. База по зарегистрированным пользователям, которым подтвердили регистрацию\n2. База по пользователям не прошедшим регистрацию или же заявка которых была отклонена\n 3. Вопросно-ответные базы данных", reply_markup=Admin_Keyboards.report_ending(True))
        records = await db.get_specialits_questions(return_all_records=True)
        await excel_full_unloading(records)
        excel = FSInputFile('unloading.xlsx')
        await bot.send_document(chat_id=callback.from_user.id,
                                document=excel)
    elif callback.data == "clear_data":
        result = await db.truncate_data(callback=callback)
        await callback.message.edit_text(text="Базы данных успешно обнулены", reply_markup=Admin_Keyboards.report_ending(data_cleared=True)) if result == True else ...

@router.callback_query(Specialist_states.choosing_filter)
async def process_choosing_filters(callback: types.CallbackQuery, state: FSMContext):
    '''
    Выбор фильтра для вывода вопросов
    '''
    data = await state.get_data()
    search_filter = data['custom_filter']
    if callback.data.startswith('district'):
        district_id = callback.data.split('_')[-1]
        regions_keyboard = await User_Keyboards.create_regions_buttons(district_id=int(district_id))
        await callback.message.edit_text('Выберите регион/область', reply_markup=regions_keyboard)
    elif callback.data == 'regions_filter':
        markup = await User_Keyboards.create_district_buttons()
        await callback.message.edit_text('Выберите Федеральный округ', reply_markup=markup)
    elif callback.data == 'question_type':
        await callback.message.edit_text('Нажмите на кнопку с типом вопросов и фильтр переключится, после чего нажмите кнопку "Применить".',
                                         reply_markup=Admin_Keyboards.questions_type_menu(unanswered_choosen='вкл.',
                                                                                          answered_choosen='выкл.'))
    elif callback.data.endswith('answered_questions'):
        replacement = {'вкл.': 'выкл.',
                       'выкл.': 'вкл.'}
        data_from_callback = callback.data
        for button in callback.message.reply_markup.inline_keyboard[:2]:
            if button[0].callback_data == data_from_callback:
                choosen_flag = replacement.get(button[0].text[-5:].strip())
            else:
                not_choosen_flag = button[0].text[-5:].strip()
        if data_from_callback == 'unanswered_questions':
            menu = Admin_Keyboards.questions_type_menu(unanswered_choosen=choosen_flag,
                                                       answered_choosen=not_choosen_flag)
        else:
            menu = Admin_Keyboards.questions_type_menu(unanswered_choosen=not_choosen_flag,
                                                       answered_choosen=choosen_flag)
        try:
            await callback.message.edit_reply_markup(reply_markup=menu)
        except TelegramBadRequest: await callback.answer(text='Чтобы сбросить фильтр, вернитесь в меню')
    elif callback.data == 'select_filter':
        transformation = {'вкл.': True,
                          'выкл.': False}
        unanswered_flag = transformation.get(callback.message.reply_markup.inline_keyboard[0][0].text[-5:].strip())
        answered_flag = transformation.get(callback.message.reply_markup.inline_keyboard[1][0].text[-5:].strip())
        if unanswered_flag:
            search_filter.question_states.append('Pending')
        if answered_flag:
            search_filter.question_states.append('Accept')
        try:
            data['role']
            await callback.message.edit_text('Выберите фильтры для вывода вопросов. И используйте кнопку "Вывести вопросы", если фильтры выбраны или не нужны.\nПо умолчанию будут выведены неотвеченные вопросы',
                                            reply_markup=Admin_Keyboards.filters_menu_admin())
        except KeyError:
            await callback.message.edit_text('Выберите фильтры для вывода вопросов. И используйте кнопку "Вывести вопросы", если фильтры выбраны или не нужны.\nПо умолчанию будут выведены неотвеченные вопросы',
                                            reply_markup=Specialist_keyboards.filters_menu_specialist())
    elif callback.data == 'show_questions':
        questions = await create_questions(questions_filter=search_filter)
        await state.set_state(Specialist_states.choosing_question)
        await callback.message.edit_text('Выберите вопрос')
        message_ids = []
        for question in questions:
            lp_user_info = await db.get_lp_user_info(lp_user_id=question['lp_user_id'])
            user_name = lp_user_info[0][1]            
            
            try:
                message = await callback.message.answer(f'<b>Пользователь:</b> {user_name}\n<b>Субъект:</b> {question["subject_name"]}\n<b>Форма:</b> {question["form_name"]}\n<b>Вопрос:</b> {question["question"]}\n<s>{question["message_id"]}</s>\n\n<b>Ответ:</b> {question["spec_answer"]}', 
                                                reply_markup=Specialist_keyboards.question_buttons())
            except KeyError:
                try:
                    text = message_int.create_message(user_id=user_name,
                                              subject=question['subject_name'],
                                              form_name=question['form_name'],
                                              question=question['question'],
                                              message_id=question['message_id'],
                                              question_date=question['question_date'])
                    message = await callback.message.answer(text=text, reply_markup=Specialist_keyboards.question_buttons())
                except TelegramBadRequest:
                    text = message_int.create_message(user_id=user_name,
                                              subject=question['subject_name'],
                                              form_name=question['form_name'],
                                              question=escape(question['question']),
                                              message_id=question['message_id'],
                                              question_date=question['question_date'])
                    message = await callback.message.answer(text=text, reply_markup=Specialist_keyboards.question_buttons())
            except TelegramBadRequest:
                message = await callback.message.answer(f'<b>Пользователь:</b> {user_name}\n<b>Субъект:</b> {question["subject_name"]}\n<b>Форма:</b> {question["form_name"]}\n<b>Вопрос:</b> {escape(question["question"])}\n<s>{question["message_id"]}</s>\n\n<b>Ответ:</b> {question["spec_answer"]}', 
                                                reply_markup=Specialist_keyboards.question_buttons())
                            
            message_ids.append(message.message_id)
        await callback.message.answer('Если вопросы закончились (нет больше кнопок у них), то нажмите здесь кнопку для генерации новых',
                                    reply_markup=Specialist_keyboards.questions_gen())
        try:
            await state.update_data(message_ids=message_ids)
        except UnboundLocalError:
            pass
    elif callback.data == 'form_selection':
        Admin_Keyboards.forms_keyboard.adjust(1)
        
        await callback.message.edit_text('Выберите форму',
                                         reply_markup=Admin_Keyboards.forms_keyboard.as_markup())
    elif callback.data.startswith('region'):
        region_id = callback.data.split('_')[-1]
        miac_name = await db.get_miac_information(info_type='miac', miac_id=int(region_id))
        search_filter.region = miac_name
        try:
            data['role']
            await callback.message.edit_text('Выберите фильтры для вывода вопросов. И используйте кнопку "Вывести вопросы", если фильтры выбраны или не нужны.\nПо умолчанию будут выведены неотвеченные вопросы',
                                            reply_markup=Admin_Keyboards.filters_menu_admin())
        except KeyError:
            await callback.message.edit_text('Выберите фильтры для вывода вопросов. И используйте кнопку "Вывести вопросы", если фильтры выбраны или не нужны.\nПо умолчанию будут выведены неотвеченные вопросы',
                                            reply_markup=Specialist_keyboards.filters_menu_specialist())
    else:
        search_filter.form = callback.data
        try:
            data['role']
            await callback.message.edit_text('Выберите фильтры для вывода вопросов. И используйте кнопку "Вывести вопросы", если фильтры выбраны или не нужны.\nПо умолчанию будут выведены неотвеченные вопросы',
                                            reply_markup=Admin_Keyboards.filters_menu_admin())
        except KeyError:
            await callback.message.edit_text('Выберите фильтры для вывода вопросов. И используйте кнопку "Вывести вопросы", если фильтры выбраны или не нужны.\nПо умолчанию будут выведены неотвеченные вопросы',
                                            reply_markup=Specialist_keyboards.filters_menu_specialist())

@router.callback_query(Admin_states.answers_form)
async def process_choosing_answers_form(callback: types.CallbackQuery, state: FSMContext):
    '''
    Обработка и выдача вопрос по определенной форме для админов
    '''
    from additional_functions import create_questions
    data = await state.get_data()
    operation_type = data["operation_type"]
    await state.set_state(Specialist_states.choosing_question)
    flag = False
    if operation_type == "unanswered":
        questions = await create_questions(callback.from_user.id, form=callback.data)
    else:
        questions = await create_questions(callback.from_user.id, question_status="Accept", form=callback.data)
        flag = True
    await callback.message.edit_text('Выберите вопрос')
    message_ids = []
    for question in questions:
        lp_user_info = await db.get_lp_user_info(lp_user_id=question['lp_user_id'])
        user_name = lp_user_info[0][1]
        try:
            message = await callback.message.answer(f'<b>Пользователь:</b> {user_name}\n<b>Субъект:</b> {question["subject_name"]}\n<b>Форма:</b> {question["form_name"]}\n<b>Вопрос:</b> {question["question"]}\n<s>{question["message_id"]}</s>\n\n<b>Ответ:</b> {question["spec_answer"]}', 
                                                reply_markup=Specialist_keyboards.question_buttons())
        except KeyError:
            text = message_int.create_message(user_id=user_name,
                                              subject=question['subject_name'],
                                              form_name=question['form_name'],
                                              question=question['question'],
                                              message_id=question['message_id'],
                                              question_date=question['question_date'])
            message = await callback.message.answer(text=text, 
                                                reply_markup=Specialist_keyboards.question_buttons())
        message_ids.append(message.message_id)
    await callback.message.answer('Если вопросы закончились (нет больше кнопок у них), то нажмите здесь кнопку для генерации новых',
                                reply_markup=Specialist_keyboards.questions_gen(flag=flag, in_the_section=callback.data))
    try:
        await state.update_data(message_ids=message_ids)
    except UnboundLocalError:
        pass

@router.callback_query(Admin_states.form_managing)
async def managing_forms(callback: types.CallbackQuery, state: FSMContext) -> None:
    from main import bot
    
    if callback.data == 'forms_add':
        msg = await callback.message.edit_text(text='Отправьте название формы (без пробелов и отступов)')
        await state.update_data(msg=msg, forms_action="add")
    elif callback.data == "forms_del":
        msg = await callback.message.edit_text(text='Отправьте название формы (без пробелов и отступов)')
        await state.update_data(msg=msg, forms_action="delete")
    else:
        await state.clear()
        menu = await callback.message.edit_text(text="Добро пожаловать в Админ-панель", reply_markup=Admin_Keyboards.main_menu())
        await state.update_data(main_menu=menu)

@router.callback_query(Admin_states.users_managing)
async def managing_users(callback: types.CallbackQuery, state: FSMContext) -> None:
    
    if callback.data == 'users_add':
        msg = await callback.message.edit_text(text='Отправьте ID специалиста')
        await state.update_data(msg=msg, users_action="add")
    elif callback.data == "users_del":
        msg = await callback.message.edit_text(text='Отправьте ID специалиста')
        await state.update_data(msg=msg, users_action="delete")
    elif callback.data == "users_change":
        msg = await callback.message.edit_text(text='Отправьте ID специалиста')
        await state.update_data(msg=msg, users_action="change")

@router.callback_query(Admin_states.spec_linking)
async def spec_linking(callback: types.CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    
    if callback.data != "end":
        spec_id = callback.data.split("_")[1]
        form_id = callback.data.split("_")[2]
        
        await db.link_spec_to_form(spec_id=int(spec_id), form_id=int(form_id))
        await callback.answer(text="Специалист привязан")
    else:
        callback.answer(text="Раздел был успешно создан")
        
        await state.clear()
        menu = await data["msg"].edit_text(text="Добро пожаловать в Админ-панель", reply_markup=Admin_Keyboards.main_menu())
        await state.update_data(main_menu=menu)

@router.callback_query(Admin_states.form_linking)
async def form_linking(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.update_data(tag=callback.data)
    form_info = await db.extract_form_info_by_tag(tag_info=callback.data)
    await state.update_data(form_info=form_info)
    data = await state.get_data()
    
    try:
        data["forms"]
    except KeyError:
        data["forms"] = []
        
    data["forms"].append(f"{form_info['form_name']}\n")
    
    form_name_for_alert = form_info["form_name"][:40] + "..." if len(form_info["form_name"]) > 40 else form_info["form_name"]
    await callback.answer(text=f'Вы привязали специалиста к формам: {", ".join(data["forms"])}', show_alert=True)
    await db.link_spec_to_form(spec_id=data["spec_id"], form_id=form_info["id"])
    await state.update_data(data=data)
    
@router.callback_query()
async def process_user(callback: types.CallbackQuery, state: FSMContext) -> None:
    '''
    Обработка запросов от inline-кнопок user-a
    '''

    @access_block_decorator
    async def getting_started(callback: types.CallbackQuery, state: FSMContext):
        await state.set_state(User_states.form_choosing)
        User_Keyboards.forms_keyboard.adjust(1)
        menu_info = await callback.message.edit_text(text='Добро пожаловать в меню вопросных форм. Выберете нужную форму. Для возврата в меню, воспользуйтесь кнопкой "Возврат в главное меню"', reply_markup=User_Keyboards.forms_keyboard.as_markup())
        await state.update_data(menu=menu_info)
        
    @access_block_decorator
    async def getting_link(callback: types.CallbackQuery, state: FSMContext):
        await callback.message.answer('Ссылка на канал раздела форм - https://t.me/+cNQvBD_FWpQxZWRi')

    chat_id = callback.from_user.id
    from main import bot

    if callback.data == 'main_menu':
        await callback.message.edit_text('Меню', reply_markup=await User_Keyboards.main_menu(True, user_id=callback.from_user.id))
    elif callback.data == 'npa':
        await state.set_state(User_states.file_date)
        await state.update_data(button_type='npa')
        await callback.message.edit_text(text='Выберите период времени', reply_markup=User_Keyboards.show_files())
    elif callback.data == 'medstat':
        await state.set_state(User_states.file_date)
        await state.update_data(button_type='medstat')
        await callback.message.edit_text(text='Выберите период времени', reply_markup=User_Keyboards.show_files())
    elif callback.data == 'statistic':
        await state.set_state(User_states.file_date)
        await state.update_data(button_type='statistic')
        await callback.message.edit_text(text='Выберите период времени', reply_markup=User_Keyboards.show_files())
    elif callback.data == 'method_recommendations':
        await state.set_state(User_states.file_date)
        await state.update_data(button_type='method_recommendations')
        await callback.message.edit_text(text='Выберите период времени', reply_markup=User_Keyboards.show_files())
    elif callback.data == 'registration':
        markup = await User_Keyboards.create_district_buttons()
        await callback.message.edit_text('Выберите Федеральный округ', reply_markup=markup)
        await state.set_state(User_states.reg_organisation)
    elif callback.data == "make_question":
        await getting_started(callback, state)
    elif callback.data == 'admin_panel':
        await state.clear()
        menu = await callback.message.edit_text(text="Добро пожаловать в Админ-панель", reply_markup=Admin_Keyboards.main_menu())
        await state.update_data(main_menu=menu)
    elif callback.data == 'specialist_panel':
        await callback.message.edit_text(text="Добро пожаловать в Специалист-панель", reply_markup=Specialist_keyboards.main_menu())
    elif callback.data == 'link_open_chat':
        await callback.answer('Вы перешли в открытый канал')
    elif callback.data == 'link_razdel_chat':
        await getting_link(callback, state)
    elif callback.data == 'chats_and_channels':
        await callback.message.edit_text(text="Выберете чат\канал в который хотите перейти", reply_markup=Admin_Keyboards.access_to_channels())
    elif callback.data == 'complex_upload':
        await callback.message.edit_text(text='Прикрепите файл и текстовое описание к нему или же вы можете написать текстовое сообщение-объявление для отправки в раздел форм')
        await state.set_state(Specialist_states.complex_public)
    elif callback.data == 'answer_the_question':
        from non_script_files.config import priority_list
        custom_filter = SearchFilter(specialist_id=callback.from_user.id)
        for info in priority_list['OWNER']:
            if callback.from_user.id == info['user_id']:
                await callback.message.edit_text('Выберите фильтры для вывода вопросов. И используйте кнопку "Вывести вопросы", если фильтры выбраны или не нужны.',
                                                reply_markup=Admin_Keyboards.filters_menu_admin())
                await state.update_data(role='OWNER')
                break
        else:
            await callback.message.edit_text('Выберите фильтры для вывода вопросов. И используйте кнопку "Вывести вопросы", если фильтры выбраны или не нужны.',
                                                reply_markup=Specialist_keyboards.filters_menu_specialist())
        await state.update_data(custom_filter=custom_filter)
        await state.set_state(Specialist_states.choosing_filter)
    elif callback.data == 'check_reg':
        await callback.message.edit_text(text="""Выберете заявку из предложенных. Если нету кнопок, прикрепленных к данному сообщению, то заявки не сформировались - вернитесь к данному меню позже. Для возврата в главное меню воспользуйтесь кнопкой 'Возврат в главное меню'""", reply_markup=Admin_Keyboards.application_gen(page_value=1, unreg_tuple=await db.get_unregistered()).as_markup())
        await state.set_state(Admin_states.registration_process)
        await state.update_data(page='1')
    elif callback.data == 'publications':
        publications = await db.get_posts_to_public()
        data = await state.get_data()
    
        for publication in publications:
            try:
                if publication['publication_type']['publication_format'] == 'Text':
                    await callback.message.answer(text=publication['publication_type']['caption_text'], reply_markup=Admin_Keyboards.post_publication(post_id=publication['id']))
                elif publication['publication_type']['publication_format'] == 'Answer':
                    await callback.message.answer(text=publication['publication_content'], reply_markup=Admin_Keyboards.post_publication(post_id=publication['id']))
                elif publication['publication_type']['publication_format'] == 'Document': 
                    await bot.send_document(chat_id=callback.from_user.id, caption=publication['publication_type']['caption_text'], document=publication['publication_content'], reply_markup=Admin_Keyboards.post_publication(pub_type='document', post_id=publication['id']))
            except TypeError:
                continue

        await callback.message.edit_text(text='Если публикации закончились (нет больше кнопок у них), то нажмите здесь кнопку для генерации новых', reply_markup=Admin_Keyboards.pub_refresh())
        await state.set_state(Admin_states.post_publication)
    elif callback.data == 'op_channel_join':
        await callback.answer(text="Вы перешли в открытый канал")
    elif callback.data == 'coord_chat_join':
        await callback.answer(text='Вы перешли в чат координаторов')
    elif callback.data == 'sections_join':
        await callback.answer(text='Вы перешли в разделы форм')
    elif callback.data == 'registration_db':
        from main import bot
        await creating_excel_users()
        excel = FSInputFile('miac_output.xlsx')
        await bot.send_document(chat_id=callback.from_user.id,
                                document=excel)
    elif callback.data == 'load_file':
        data = await state.get_data()
        await state.set_state(Admin_states.file_loading)
        try:
            menu = await callback.message.edit_text(inline_message_id=str(data["main_menu"].message_id), text="Выберете в какой раздел загружать файлы", reply_markup=Admin_Keyboards.file_loading())
            await state.update_data(inline_menu=menu)
        except KeyError:
            menu = await callback.message.answer(text="Выберете в какой раздел загружать файлы", reply_markup=Admin_Keyboards.file_loading())
            await state.update_data(inline_menu=menu)
    elif callback.data == 'delete_member':
        await callback.message.edit_text(text='Введите один или несколько user_id через запятую')
        await state.set_state(Admin_states.delete_member)
    elif callback.data == 'send_to_user':
        cb_msg = await callback.message.edit_text(text="Введите id пользователя(ей), после чего отправьте текстовое сообщение для рассылки пользователю(ям). Если пользователей больше одного, то вводите id через ',' или помещайте каждый новый id на новой строке (ctrl + enter)")
        await state.set_state(Admin_states.user_sending)
    elif callback.data == 'delete_file':
        await callback.message.edit_text(text='Выберите раздел, из которого нужно удалить',
                                         reply_markup=Admin_Keyboards.file_loading())
        await state.set_state(Admin_states.delete_file)
    elif callback.data == 'end_of_report':
        await callback.message.edit_text(text="""Для завершения годового отчёта необходимо в первую очередь выгрузить данные, используя кнопку 'Выгрузить данные', и уже после выгрузки вам будет доступна кнопка обнуления баз бота.""",
                                         reply_markup=Admin_Keyboards.report_ending())
        await state.set_state(Admin_states.report_ending)
    elif callback.data == "forms_managing":
        await callback.message.edit_text(text='Выберете опцию из списка',
                                         reply_markup=Admin_Keyboards.forms_manager_keyboard()) 
        await state.set_state(Admin_states.form_managing)
    elif callback.data == "users_managing":
        await callback.message.edit_text(text='Выберете опцию из списка',
                                         reply_markup=Admin_Keyboards.users_manager_keyboard()) 
        await state.set_state(Admin_states.users_managing)







    










