from additional_functions import user_registration_decorator, fuzzy_handler, question_redirect, save_to_txt, extracting_query_info, message_delition
from additional_functions import delete_member, object_type_generator
from states import User_states, Specialist_states, Admin_states
from main import db, llm_model, bot
from keyboards import User_Keyboards, Specialist_keyboards, Admin_Keyboards
from non_script_files.config import COORD_CHAT, RASDEL_FORM, ADMIN_CHAT, forms_data, priority_list

from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.utils.chat_action import ChatActionMiddleware, ChatActionSender
from aiogram.enums.chat_action import ChatAction
from aiogram.types.input_file import FSInputFile
import json
import datetime
import copy
import asyncio
from aiogram.types import InlineKeyboardButton

router = Router()
router.message.middleware(ChatActionMiddleware())

@router.message(Command('start'))
@user_registration_decorator
async def process_start(message: types.Message, state: FSMContext) -> None:
    '''
    Выдаем пользователю определенный набор кнопок от его статуса
    '''
    await state.clear()

@router.message(F.text.contains('Возврат') | F.text.contains('Не нашёл'))
async def exiting_fuzzy(message: types.Message, state: FSMContext):
    await message.delete()
    if "Возврат в главное меню" in message.text:
        @user_registration_decorator
        async def process_start(message: types.Message, state: FSMContext) -> None:
            data = await state.get_data()
            '''
            Выдаем пользователю определенный набор кнопок от его статуса
            '''
            try:
                temp_msg = data["temp_msg"]
                bot_answer = data["bot_answer"]
                
                await message_delition(*bot_answer, temp_msg, time_sleep=0)
            except KeyError:
                pass
                
            await state.clear()
        await process_start(message, state)

@router.message(User_states.reg_organisation)
async def process_fio_input(message: types.Message, state: FSMContext) -> None:
    '''
    Получение места работы
    '''
    await state.update_data(organisation=message.text)
    await message.answer('Введите Вашу должность')
    await state.set_state(User_states.reg_post)

@router.message(User_states.reg_post)
async def process_telephone_number_input(message: types.Message, state: FSMContext) -> None:
    '''
    Получение наименования должности
    '''
    await state.update_data(post=message.text)
    await db.add_registration_form(message.from_user.id, await state.get_data())
    await db.after_registration_process(message.from_user.id, message.from_user.full_name)
    await db.update_user_info(user_id=message.from_user.id, telegram_name=message.from_user.full_name)
    await message.answer('''Ваши данные отправлены на проверку, ожидайте подтверждения.
После чего Вы сможете задать вопрос специалисту и получить доступ к каналам разделов форм''', reply_markup=await User_Keyboards.main_menu(True, user_id=message.from_user.id))
    await state.clear()

@router.message(User_states.neuro_process)
async def process_question_input(message: types.Message, state: FSMContext) -> None:
    '''
    Обработка вопроса через LLM
    '''   
    document = None
    topk_chunks = None
    q_chunks = None
    a_chunks = None
    sim_rates = None
    reply = [] ; logs = ""
    question_content = ""
    bot_answer = []
    
    await state.set_state(User_states.form_choosing)
    f_data = await state.get_data()
    form_id = f_data["form_info"]["id"]
    await state.set_state(User_states.neuro_process)
    
    await state.update_data(user_question=message.text, user_message=message)
            
    async def executor():
        nonlocal topk_chunks, sim_rates, q_chunks, a_chunks
        q_chunks, a_chunks = await llm_model.get_raw_chunks(u_query=message.text, form_id=form_id)
        topk_chunks, sim_rates = llm_model.retrieve_chunks(query_embed=llm_model.embed_query(query=message.text), raw_qchunks=q_chunks)

    temp_msg = await message.reply(text="Ожидайте ответ бота на ваше сообщение. Если вы не отыскали подходящего вопроса из предложенных, просим воспользоваться кнопкой 'Передать вопрос специалисту'. В случае, если вы нашли вопрос схожий с вашим и вас устроил представленный ответ, нажмите на кнопку 'Выбрать ответ'")
    await executor()

    try:
        if topk_chunks.any():
            for num, idx in enumerate(topk_chunks):
                reply.append((f"<b>Вопрос №{num + 1}:</b> {q_chunks[idx]}", f"<b>Ответ №{num + 1}:</b> {a_chunks[idx]}"))
                logs = logs + f"Вопрос №{num + 1}: {q_chunks[idx]}\nОтвет №{num + 1}: {a_chunks[idx]}\nСхожесть: {round(sim_rates[idx].item(), 2)}\n\n"

            for question, answer in reply:
                try:
                    bot_answer.append(await message.answer(text=f"Возможно вы имели в виду:\n\n{question}\n{answer}", reply_markup=User_Keyboards.model_reply_proc(msg_type="bot")))
                except TelegramBadRequest:
                    continue
    except AttributeError:
        logs = logs + f"Не найден контекст для вопроса:\n{message.text}\n\n"
          
    await temp_msg.edit_reply_markup(reply_markup=User_Keyboards.model_reply_proc(msg_type="user"))
    await state.update_data(bot_answer=bot_answer, temp_msg=temp_msg)
    
@router.message(Specialist_states.answer_question)
async def process_answer(message: types.Message, state: FSMContext) -> None:
    from main import bot
    from cache_container import Data_storage
    data = await state.get_data()
    question_id = data['question_id'] ; question_text = data['question'] ; question_text_for_user = question_text.split("\n")
    form_type = question_text_for_user[2].split(":") ; form_type = form_type[1].strip()
    await db.answer_process_report(question_id=int(question_id),
                             answer=message.text,
                             specialist_id=message.from_user.id)
    form_type = form_type[:25] + "..." if len(form_type) > 25 else form_type
    publication_menu = await bot.send_message(chat_id=message.from_user.id, text="Выберите тип публикации. Для того, чтобы выйти из меню нажмите 'Завершить публикацию'. В противном случае вы не сможете отвечать на другие вопросы", reply_markup=Specialist_keyboards.publication_buttons(spec_forms=form_type))
    await bot.edit_message_text(text=f'<b>Вы выбираете тип публикации для этого вопроса</b>\n{question_text}', chat_id=message.from_user.id, message_id=data['question_message'])
    await state.update_data(menu=publication_menu, spec_answer=message.text)
    await state.set_state(Specialist_states.public_choose_message)
    Data_storage.callback_texts = []

@router.message(F.text.contains('/send'))
async def process_sending_ids(message: types.message):
    from main import bot
    from additional_functions import account_link
    info = message.text.split(',')
    user_id = info[0][6:]
    subject = info[1]
    fio = info[2]
    forward = await bot.send_message(chat_id=5214835464, text=f'Новые полученные данные от пользователя с user_id: {user_id}\nСубъект: {subject}\n{fio}',
                                     reply_markup=await account_link(url=f'tg://user?id={user_id}'))
    await bot.pin_chat_message(chat_id=5214835464, message_id=forward.message_id)

@router.message(Specialist_states.complex_public)
async def information_extract(message: types.Message, state: FSMContext) -> None:
    from cache_container import cache
    data = await state.get_data()
    query_format_info, file_id = extracting_query_info(query=message)
    spec_forms = await db.get_specform(user_id=message.from_user.id)

    if message.document:        
        while spec_forms == None:
            spec_forms = await db.get_specform(user_id=message.from_user.id)

        try:
            if query_format_info["has_caption"] == False and data["not_attached_caption"] != 'Null':
                    query_format_info["caption_text"] = data["not_attached_caption"]
                    query_format_info["has_caption"] = True
                    state.update_data(not_attached_caption='Null')
        except KeyError:
            pass

        try:
            publication_menu = await message.answer(text=f'Документ {query_format_info["file_name"]} успешно загрузился и готов к отправке', reply_markup=Specialist_keyboards.publication_buttons(spec_forms=spec_forms,file_type='other'))
            await cache.set(f"publication_menu:{publication_menu.message_id}", json.dumps([]))
            await state.update_data(data={
                f"publication_menu:{publication_menu.message_id}":publication_menu,
                f"query_format_info:{publication_menu.message_id}":query_format_info,
                f"file_id:{publication_menu.message_id}":file_id})
        except KeyError:
            pass
    elif message.text:
        await state.update_data(not_attached_caption=message.text)
        try:
            query_format_info['caption_text'] = message.text
            publication_menu = await message.answer(text=f'Текст сообщения {message.text} успешно загрузился и готов к отправке', reply_markup=Specialist_keyboards.publication_buttons(spec_forms=spec_forms,file_type='other'))
            await cache.set(f"publication_menu:{publication_menu.message_id}", json.dumps([]))
            await state.update_data(data={
                f"publication_menu:{publication_menu.message_id}":publication_menu,
                f"query_format_info:{publication_menu.message_id}":query_format_info,
                f"file_id:{publication_menu.message_id}":file_id})
        except KeyError:
            pass
    else: 
        await message.answer(text="Вы попытались прикрепить неподдерживаемый тип файла (фото/видео/аудио)... Просим повторить процесс, но с другим типом файла")
        
@router.message(Admin_states.file_loading)
async def file_reciever(message: types.Message, state: FSMContext):  
    from cache_container import Data_storage 
                   
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
            
    file_format = extracting_query_info(message) 
    
    try:
        file_id = message.document.file_id
    except AttributeError:
        pass
    
    try:
        if data["file_sending_process"]:
            pass
    except KeyError:
        await state.update_data(file_sending_process={})
    
    if message.media_group_id == None and file_format[0]["query_format"] != "Text":
        data = await state.get_data()
        data['file_sending_process'].update([(file_id, file_format[0])])
        Data_storage.not_attached_caption = [None, 0]
    elif message.media_group_id == None and file_format[0]["query_format"] == "Text":
        Data_storage.not_attached_caption = [message.text, message.message_id]
        await message.delete()
        return None
    else:
        data = await state.get_data()
        try:
            if data["current_media_group"][0] == message.media_group_id:
                file_format[0]["caption_text"] = data["current_media_group"][1][0] if Data_storage.not_attached_caption[0] != None else "Null"
                file_format[0]["has_caption"] = True if Data_storage.not_attached_caption[0] != None else False
            else:
                try:
                    if Data_storage.not_attached_caption[1] == data["current_media_group"][1][1]:
                        Data_storage.not_attached_caption = [None, 0] 
                    else:
                        pass
                except AttributeError:
                    pass
                if  Data_storage.not_attached_caption[0] != None:
                    file_format[0]["caption_text"] = Data_storage.not_attached_caption[0]
                    file_format[0]["has_caption"] = True
                await state.update_data(current_media_group=(message.media_group_id, Data_storage.not_attached_caption))
        except KeyError:
            if  Data_storage.not_attached_caption[0] != None:
                file_format[0]["caption_text"] = Data_storage.not_attached_caption[0]
                file_format[0]["has_caption"] = True
            await state.update_data(current_media_group=(message.media_group_id, Data_storage.not_attached_caption))
        
        data['file_sending_process'].update([(file_id, file_format[0])])
        
    await message.delete()
    file_one = await message.answer(text=f"Файл {message.document.file_name} успешно загрузился в форму {folder_type}")
    await message_delition(file_one, time_sleep=20)

@router.message(Admin_states.delete_member)
async def get_ids_to_delete(message: types.Message, state: FSMContext):
    await state.update_data(ids_to_delete=message.text)
    await message.answer(text='Выберите в каком чате удалить пользователя',
                         reply_markup=Admin_Keyboards.delete_in_chat())

@router.message(Admin_states.user_sending)
async def private_sending_proc(message: types.Message, state: FSMContext):
    from main import bot
    data = await state.get_data()

    try:
        if data["ids_passed"] == True:
            for u_id in data["user_ids"]:
                try:
                    await bot.send_message(chat_id=int(u_id), text=f'Сообщение от координатора: {message.text}')
                    msg = await message.answer(text=f"Сообщение отправлено пользователю с id = {u_id}")
                    await message_delition(msg, time_sleep=5)
                    await state.update_data(ids_passed=False)
                    msg_end = await message.answer(text="Отправка завершена. Вернитесь в главное меню или совершите отправку сообщения пользователям, в первую очередь указав их id")
                    await message_delition(msg_end, time_sleep=10)
                except ValueError:
                    msg = await message.answer(text="Некорректный формат данных для id, повторите ваш ввод")
                    await message_delition(msg, time_sleep=5)
                    await state.update_data(ids_passed=False)
        else:
            if "\n" in message.text:
                await state.update_data(user_ids=(*message.text.split("\n"),))
            elif "," in message.text:
                await state.update_data(user_ids=(*message.text.split(","),)) 
            else:
                await state.update_data(user_ids=(message.text,))
        
            await state.update_data(ids_passed=True)
            await message.delete()
            msg_send = await message.answer(text="Введите текст сообщения для отправки пользователю(ям)")
            await message_delition(msg_send, time_sleep=10)
    except KeyError:
        if "\n" in message.text:
            await state.update_data(user_ids=(*message.text.split("\n"),))
        elif "," in message.text:
            await state.update_data(user_ids=(*message.text.split(","),)) 
        else:
            await state.update_data(user_ids=(message.text,))

        await state.update_data(ids_passed=True)
        await message.delete()
        msg_send = await message.answer(text="Введите текст сообщения для отправки пользователю(ям)")
        await message_delition(msg_send, time_sleep=10)

@router.message(Admin_states.form_managing)
async def managing_forms(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    
    action = data["forms_action"]
    
    if action == "add":
        forum_topic = await bot.create_forum_topic(chat_id=RASDEL_FORM, name=message.text)
        forms_data.update([(message.text, forum_topic.message_thread_id)])
        
        Admin_Keyboards.forms_keyboard.add(InlineKeyboardButton(text=message.text, callback_data=f'sec_{forum_topic.message_thread_id}')) 
        User_Keyboards.forms_keyboard.add(InlineKeyboardButton(text=message.text, callback_data=f'sec_{forum_topic.message_thread_id}')) 
        
        await db.add_form(message.text, f'sec_{forum_topic.message_thread_id}')
        
        await data["msg"].edit_text(text="Выберете специалиста для привязки к форме", reply_markup=await Admin_Keyboards.linking_specs(forum_topic.message_thread_id))
        await state.set_state(Admin_states.spec_linking)
        await state.update_data(msg=data["msg"])
        
    elif action == "delete":
        try:
            forum_topic = await bot.delete_forum_topic(chat_id=RASDEL_FORM, message_thread_id=forms_data[message.text])
            
            Admin_Keyboards.forms_keyboard._markup = [
            [button for button in row if button.callback_data != f'sec_{forms_data[message.text]}']
            for row in Admin_Keyboards.forms_keyboard._markup
            ]
            
            await db.delete_form(f'sec_{forms_data[message.text]}')
            forms_data.pop(message.text)
                    
            await state.clear()
            menu = await message.answer(text="Раздел был успешно удален. Добро пожаловать в Админ-панель", reply_markup=Admin_Keyboards.main_menu())
            await state.update_data(main_menu=menu)
        except (TelegramBadRequest, KeyError):
            pass 
    else:
        await state.clear()
        menu = await message.answer(text="Добро пожаловать в Админ-панель", reply_markup=Admin_Keyboards.main_menu())
        await state.update_data(main_menu=menu)

@router.message(Admin_states.users_managing)
async def managing_users(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    action = data["users_action"]
    
    if action == "add":
        user_id = int(message.text)
        await state.set_state(Admin_states.user_adding)
        await state.update_data(user_data={"user_id": user_id, "user_fio": None, "privilege_type": None})
        await message.answer(text=f"Введите ФИО пользователя для продолжения")
    elif action == "delete":
        try:
            user_id = int(message.text)
            priv_type = await db.delete_user(spec_id=user_id)
            data = list(filter(lambda x: x["user_id"] == user_id, priority_list[priv_type]))
            priority_list[priv_type].remove(data[0])
            await message.answer(text=f"Пользователь с ID {user_id} успешно удален из базы данных")
        except ValueError:
            await message.answer(text="Некорректный ID пользователя")
    elif action == "change":
        spec_name = await db.get_spec_info_by_user_id(user_id=int(message.text))
        spec_forms = await db.get_specform(user_id=int(message.text))
        spec_forms = [form["form_name"] for form in spec_forms]
        User_Keyboards.forms_keyboard.adjust(1)
        form_menu = await message.answer(text=f"Специалист: {spec_name['user_fio']}. Просим привязать его к формам для полноценной работы. Формы до изменения: {', '.join(spec_forms)}", reply_markup=User_Keyboards.forms_keyboard.as_markup())
        await state.set_state(Admin_states.form_linking)
        await state.update_data(form_menu=form_menu, spec_id=int(message.text))

@router.message(Admin_states.user_adding)
async def adding_user(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    user_data = data["user_data"]
    
    if user_data["user_fio"] == None:
        user_data["user_fio"] = message.text
        await state.update_data(user_data=user_data)
        await message.answer(text="Введите тип привилегии для пользователя: OWNER (админ бота), SPECIALIST (специалист)")
    elif user_data["privilege_type"] == None:
        if message.text not in ("OWNER", "SPECIALIST"):
            await message.answer(text="Некорректный тип привилегии, повторите ввод")
            user_data["privilege_type"] = None
            await state.update_data(user_data=user_data)
        else:
            user_data["privilege_type"] = message.text.upper()
            await state.update_data(user_data=user_data)
            await db.add_user(user_id=user_data["user_id"], user_fio=user_data["user_fio"], privilege_type=user_data["privilege_type"])
            
            spec_forms = await db.get_specform(user_id=user_data["user_id"])
            spec_forms = [form["form_name"] for form in spec_forms]
            priority_list[user_data['privilege_type']].append({"user_id": user_data['user_id'], "user_fio": user_data['user_fio']})
            User_Keyboards.forms_keyboard.adjust(1)
            form_menu = await message.answer(text=f"Специалист {user_data['user_fio']} успешно добавлен в систему. Просим привязать его к формам для полноценной работы. Формы до изменения: {', '.join(spec_forms)}", reply_markup=User_Keyboards.forms_keyboard.as_markup())
            await state.set_state(Admin_states.form_linking)
            await state.update_data(form_menu=form_menu, spec_id=user_data["user_id"])

@router.message(F.document)
async def test(message: types.Message):
    print(message.document)

@router.message(F.text.contains('id'))
async def chat_id_extraction(message: types.Message):
    save_to_txt(chat_information=f'''chat_id={message.chat.id}\nthread_id={message.message_thread_id}\nchat_name={message.chat.full_name}\n\n''')

@router.message(F.text.regexp(r'^[\s]*([а-яА-ЯёЁ]+\s[а-яА-ЯёЁ]+\s?[а-яА-ЯёЁ]+)[\s|,]*\+?\d+\s?([\(\s\-]?\d+[\)\s\-]?[\d\s\-]+)?$'))
async def sending_information(message: types.Message) -> None:
    '''
    Отправка данных админу из чата координаторов
    '''
    from main import bot
    from cache_container import cache
    from additional_functions import account_link

    cache_data = await cache.get(f"greeting:{message.from_user.id}")
    subject = await db.get_subject_name(user_id=message.from_user.id)
    try:
        forward = await bot.send_message(chat_id=ADMIN_CHAT, text=f'Новые полученные данные от пользователя с user_id: {message.from_user.id}\nСубъект: {subject}\n{message.text}',
                                         reply_markup=await account_link(message.from_user.url))
        await bot.pin_chat_message(chat_id=ADMIN_CHAT, message_id=forward.message_id)
    except Exception as ex:
        pass
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    await bot.delete_message(chat_id=message.chat.id, message_id=str(cache_data))

@router.message(F.new_chat_member & F.chat.id == COORD_CHAT)
async def process_new_member(update: types.ChatMemberUpdated, state: FSMContext) -> None:
    from cache_container import cache
    from main import bot
    '''
    Отправка приветственного сообщения при входе пользователя в чат
    '''
    from main import bot
    greeting_message = await bot.send_message(chat_id=COORD_CHAT,
                           text=f'Добрый день, {update.from_user.full_name}! В целях качественного и оперативного взаимодействия в рамках годового отчета перед началом работы укажите, пожалуйста, Ваши <b>ФИО</b> и <b>номер телефона</b> в сообщении данного чата.\nПример:\nИванов Иван Иванович 8 999 999 99-99',
                           disable_notification=True)
    serialized_greeting_message = json.dumps(greeting_message.message_id)
    await cache.set(f"greeting:{update.from_user.id}", serialized_greeting_message)

@router.message(F.text.contains('model:'))
async def model_testing(message: types.Message):    
    u_querry = message.text.split(":")[1]
    reply = None
    
    async def keep_typing():
        nonlocal reply
        while reply is None:
            await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
            await asyncio.sleep(5)
            
    async def executor():
        nonlocal reply
        reply = llm_model.conversate(user_query=u_querry)

    result = await asyncio.gather(keep_typing(), executor())

    await message.answer(text=reply)        
    
@router.message(lambda x: x)
async def lost_msg(message: types.Message, state: FSMContext):
    pass
    
# @router.channel_post(F.text.contains('id'))
# async def chat_id_extraction(message: types.Message):
#     print(f"Информация о чате {message.chat.full_name} сохранена на сервере...")
#     save_to_txt(chat_information=f'''chat_id={message.chat.id}\nthread_id={message.message_thread_id}\nchat_name={message.chat.full_name}\n\n''')
    
