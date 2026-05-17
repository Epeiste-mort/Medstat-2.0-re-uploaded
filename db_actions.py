import asyncpg
from asyncpg import Record, UniqueViolationError
from asyncpg.exceptions import PostgresError, InterfaceError 
import asyncio
from os import path
from aiogram import types

def checking_file_decorator(func):
    async def async_wrapper(*args, **kwargs):
        
        full_data = path.exists("unloading.xlsx")
        reg_users = path.exists("miac_output.xlsx")
        
        if full_data == True and reg_users== True:
            return await func(*args, **kwargs)
        else:
            if full_data == False:
                await kwargs['callback'].answer(text="Сохраните файл вопросно-ответных форм или же дождитесь его загрузки")
            
            if reg_users == False:
                await kwargs['callback'].answer(text="Сохраните файл зарегистрированных пользователей или же дождитесь его загрузки")

    return async_wrapper

class Database():
    def __init__(self):
        self.connection = None
        self.create_connection()
        self.create_table()

    async def create_connection(self) -> None:
        '''
        Создание подключения к БД PostrgeSQL
        '''
        self.connection = await asyncpg.connect(database='telegram', user='postgres', password='!qwe@123#',
                                                host='localhost')

    async def create_table(self) -> None:
        '''
        Создание таблиц в БД
        '''
        if self.connection is None:
            await self.create_connection()
        await self.connection.execute('''
                            DO $$ BEGIN
                                CREATE TYPE STATE AS ENUM ('Decline', 'Accept', 'Pending');
                                CREATE TYPE LOWER_PRIOR AS ENUM ('USER', 'OWNER');
                                CREATE TYPE HIGHER_PRIOR AS ENUM ('USER', 'OWNER', 'ADMIN', 'SPECIALIST');
                                CREATE TYPE CHAT_TYPE AS ENUM ('Group', 'Section', 'Channel', 'Chat');
                                CREATE TYPE ACCESS_LEVEL AS ENUM ('General', 'Private', 'Authorized');
                                CREATE TYPE PUBLICATION_FORMAT AS ENUM ('Document', 'Photo', 'Text', 'Video', 'Answer');
                                CREATE TYPE PUBLICATION_TYPE AS (
                                      publication_format PUBLICATION_FORMAT,
                                      has_caption BOOL,
                                      caption_text TEXT,
                                      file_name TEXT);
                            EXCEPTION
                                WHEN duplicate_object THEN null;
                            END $$;''')
        await self.connection.execute('''CREATE TABLE IF NOT EXISTS registration_process(
                                    id SERIAL PRIMARY KEY,
                                    user_id BIGINT CHECK (user_id > 0) NOT NULL, 
                                    telegram_name VARCHAR(200) DEFAULT NULL,
                                    subject_name VARCHAR(100),
                                    post_name TEXT,
                                    organisation TEXT,
                                    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        await self.connection.execute('''CREATE TABLE IF NOT EXISTS high_priority_users(
                                    id SERIAL PRIMARY KEY,
                                    user_id BIGINT CHECK (user_id > 0) NOT NULL,
                                    user_fio VARCHAR(50),
                                    privilege_type HIGHER_PRIOR NOT NULL,
                                    telegramm_name VARCHAR(50) DEFAULT NULL)''')
        await self.connection.execute('''CREATE TABLE IF NOT EXISTS low_priority_users(
                                    id SERIAL PRIMARY KEY,
                                    user_id BIGINT CHECK (user_id > 0) NOT NULL,
                                    privilege_type LOWER_PRIOR DEFAULT 'USER',
                                    registration_process_id INTEGER CHECK (registration_process_id > 0) NOT NULL,
                                    FOREIGN KEY (registration_process_id) REFERENCES registration_process (id),
                                    registration_state STATE DEFAULT 'Pending',
                                    process_regulator INTEGER CHECK (process_regulator > 0) DEFAULT NULL,
                                    FOREIGN KEY (process_regulator) REFERENCES high_priority_users (id))''')
        await self.connection.execute('''CREATE TABLE IF NOT EXISTS form_types(
                                      id SERIAL PRIMARY KEY,
                                      form_name VARCHAR(250),
                                      form_tag VARCHAR(20))''')
        await self.connection.execute('''CREATE TABLE IF NOT EXISTS questions_forms(
                                      id SERIAL PRIMARY KEY,
                                      question_message INTEGER CHECK (question_message > 0) NOT NULL,
                                      lp_user_id INTEGER CHECK (lp_user_id > 0) NOT NULL,
                                      FOREIGN KEY (lp_user_id) REFERENCES low_priority_users (id),
                                      section_form SMALLINT CHECK (section_form > 0) NOT NULL,
                                      FOREIGN KEY (section_form) REFERENCES form_types (id),
                                      question_content TEXT,
                                      question_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                      question_chat_type VARCHAR(20) DEFAULT 'Personal',
                                      question_state STATE DEFAULT 'Pending')''')
        await self.connection.execute('''CREATE TABLE IF NOT EXISTS specialist_forms(
                                      specialist_id INT,
                                      form_id INT,
                                      FOREIGN KEY (specialist_id) REFERENCES high_priority_users (id),
                                      FOREIGN KEY (form_id) REFERENCES form_types (id),
                                      PRIMARY KEY (specialist_id, form_id))''')
        await self.connection.execute('''CREATE TABLE IF NOT EXISTS answer_process(
                                      id SERIAL PRIMARY KEY,
                                      question_id INTEGER CHECK (question_id > 0) NOT NULL,
                                      FOREIGN KEY (question_id) REFERENCES questions_forms (id),
                                      answer_content TEXT,
                                      answer_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                      answer_chat_type VARCHAR(20) DEFAULT 'Personal',
                                      specialist_id BIGINT CHECK (specialist_id > 0) NOT NULL,
                                      FOREIGN KEY (specialist_id) REFERENCES high_priority_users (id))''')
        await self.connection.execute('''CREATE TABLE IF NOT EXISTS miacs (
                                        id SERIAL PRIMARY KEY,
                                        miac_name VARCHAR(100),
                                        miac_adress VARCHAR(250),
                                        telephone_number VARCHAR(25),
                                        email VARCHAR(50) UNIQUE,
                                        site VARCHAR(200),
                                        miac_tag VARCHAR(20))''')
        await self.connection.execute('''CREATE TABLE IF NOT EXISTS regions (
                                        id SERIAL PRIMARY KEY,
                                        region_name VARCHAR(50),
                                        region_tag VARCHAR(20),
                                        miac_id SMALLINT NOT NULL,
                                        FOREIGN KEY (miac_id) REFERENCES miacs (id))''')
        await self.connection.execute('''CREATE TABLE IF NOT EXISTS federal_district (
                                        id SERIAL PRIMARY KEY,
                                        federal_name VARCHAR(45),
                                        district_tag VARCHAR(30))''')
        await self.connection.execute('''CREATE TABLE IF NOT EXISTS federal_district_regions (
                                        federal_district_id INT,
                                        region_id INT,
                                        FOREIGN KEY (federal_district_id) REFERENCES federal_district (id),
                                        FOREIGN KEY (region_id) REFERENCES regions (id),
                                        PRIMARY KEY (federal_district_id, region_id))''')
        await self.connection.execute('''CREATE TABLE IF NOT EXISTS publication_process (
                                      id SERIAL PRIMARY KEY,
                                      publication_content TEXT,
                                      publication_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                      publication_status STATE DEFAULT 'Pending',
                                      publication_type PUBLICATION_TYPE,
                                      post_suggester BIGINT CHECK (post_suggester > 0) NOT NULL,
                                      post_regulator BIGINT CHECK (post_regulator > 0),
                                      FOREIGN KEY (post_suggester) REFERENCES high_priority_users (id),
                                      FOREIGN KEY (post_regulator) REFERENCES high_priority_users (id))''')
        await self.connection.execute('''CREATE TABLE IF NOT EXISTS admin_file_uploading (
                                      id SERIAL PRIMARY KEY,
                                      file_id VARCHAR NOT NULL,
                                      file_format PUBLICATION_TYPE,
                                      upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                      button_type VARCHAR(50) NOT NULL,
                                      admin_id BIGINT CHECK (admin_id > 0) NOT NULL,
                                      FOREIGN KEY (admin_id) REFERENCES high_priority_users (id))''')
        await self.connection.execute('''CREATE TABLE IF NOT EXISTS regions_links (
                                      id SERIAL PRIMARY KEY,
                                      region_id INT CHECK (region_id > 0) NOT NULL,
                                      link VARCHAR(100),
                                      FOREIGN KEY (region_id) REFERENCES regions (id))''')

    async def add_registration_form(self, *args) -> None:
        '''
        Внесение данных пользователя из формы регистрации в registration_process
        :params: 
        subject - субъект МИАЦ
        post - должность сотрудника
        organisation - организация
        '''
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()
        
        await self.connection.execute('''INSERT INTO registration_process 
                                           (user_id, subject_name, post_name, organisation)
                                           VALUES ($1, $2, $3, $4)''', args[0], args[1]['subject'], args[1]['post'], args[1]['organisation'])

    async def add_higher_users(self) -> None:
        from non_script_files.config import priority_list
        '''
        Внесение данных о пользователей высшего ранга: Moder, Admin, Owner.
        Данные извлекаются из json-файла
        '''

        if self.connection is None or self.connection.is_closed():
            await self.create_connection()

        check_higher_users = await self.connection.fetch('''SELECT * FROM high_priority_users''')

        if check_higher_users: 
            pass
        else:
            for level in priority_list.keys():
                row = priority_list[level]
                [await self.connection.execute('''INSERT INTO high_priority_users (user_id, user_fio, privilege_type)
                                                SELECT $1, $2, $3
                                                WHERE NOT EXISTS (
                                                    SELECT 1
                                                    FROM high_priority_users
                                                    WHERE user_id = $1)''', row[string_num]["user_id"], row[string_num]["user_fio"], level) for string_num in range(len(row))]
        
    async def after_registration_process(self, *args) -> None:
        '''
        Частичное заполнение данных в low_priority_users с ссылкой на registration_process_id
        из registration_process 
        :params: 
        '''

        if self.connection is None or self.connection.is_closed():
            await self.create_connection()

        cursor = await self.connection.fetchrow('''SELECT id, registration_date FROM registration_process WHERE user_id = ($1) ORDER BY registration_date DESC LIMIT 1''', args[0])
        user_check = await self.connection.fetchrow('''SELECT * FROM low_priority_users WHERE user_id = ($1)''', args[0])

        if user_check:
            await self.connection.execute('''UPDATE low_priority_users SET registration_process_id = ($1), registration_state = 'Pending' WHERE user_id = ($2)''', cursor[0], args[0])
        else:
            await self.connection.execute('''INSERT INTO low_priority_users (user_id, registration_process_id) VALUES ($1, $2)''', args[0], cursor[0])

    async def get_unregistered(self, passed_values: int = 0, available_values: int = 10) -> tuple:
        '''
        Извлечение данных о пользователях, со статусом регистрации "Pending"
        '''
        user_reg_forms = []
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()
         
        users_rows = await self.connection.fetch("""SELECT registration_process_id FROM low_priority_users WHERE registration_state = 'Pending'""")
        [user_reg_forms.append(await self.connection.fetchrow('''SELECT registration_process.*, regions.region_name
                                                              FROM registration_process
                                                              JOIN regions ON registration_process.subject_name = regions.region_name
                                                              WHERE registration_process.id = ($1) ORDER BY registration_date DESC LIMIT 1''', elem[0])) for elem in users_rows]
        if len(user_reg_forms) >= 10:   
            return users_rows, user_reg_forms[passed_values:passed_values + available_values]
        if len(user_reg_forms) >= 10:   
            return users_rows, user_reg_forms[passed_values:passed_values + available_values]
        else:
            return users_rows, user_reg_forms

    async def get_massive_of_values(self, form_id: int = None, user_id: int = None) -> tuple:
        '''
            Извлечение всех данных о форме юзера (reg. process) или же о его данных (low_priority) по id формы или по user_id 
        '''
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()

        form_info = await self.connection.fetchrow('''SELECT * FROM registration_process WHERE id = ($1)''', form_id) if form_id else await self.connection.fetchrow('''SELECT * FROM registration_process WHERE user_id = ($1)''', user_id)
        user_info = await self.connection.fetchrow('''SELECT * FROM low_priority_users WHERE registration_process_id = ($1)''', form_id) if form_id else await self.connection.fetchrow('''SELECT * FROM low_priority_users WHERE user_id = ($1)''', user_id)

        return form_info, user_info
    
    async def get_lp_user_info(self, lp_user_id: int = None):
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()
        
        form_id = await self.connection.fetchrow('''SELECT registration_process_id FROM low_priority_users WHERE id = ($1)''', lp_user_id)
            
        form_information = await self.connection.fetchrow('''SELECT * FROM registration_process WHERE id = ($1)''', form_id[0])
        lp_user_information = await self.connection.fetchrow('''SELECT * FROM low_priority_users WHERE id = ($1)''', lp_user_id)
        
        return form_information, lp_user_information

    async def update_registration_status(self, string_id, admin_id, reg_status) -> None:
        string_id = int(string_id)
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()
        inspector_id = await self.connection.fetchrow('''SELECT id FROM high_priority_users WHERE user_id = ($1)''', admin_id)
        try:
            inspector_id = inspector_id[0]
        except TypeError:
            inspector_id = 0
        await self.connection.execute('''UPDATE low_priority_users SET registration_state = ($1), process_regulator = ($2) WHERE id = ($3)''', 
                                      reg_status, inspector_id, string_id)
        
    async def get_status(self, user_id: int = None, form_id: int = None) -> str:
        '''
        Получение данных пользователя по его заявке на регистрацию (reg. process) или же по его данным в low_priority таблице
        посредством user_id или form_id 
        '''
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()
            
        if user_id:            
            user_exist = await self.connection.fetchval('''SELECT EXISTS(SELECT 1 FROM low_priority_users WHERE user_id = $1)''', user_id)
            if user_exist:
                data = await self.connection.fetchval('''SELECT registration_state FROM low_priority_users WHERE user_id = ($1)''', user_id)
            else:
                return "Decline"
        else:
            data = await self.connection.fetchval('''SELECT registration_process_id FROM low_priority_users WHERE user_id = ($1)''', form_id)
        
        return data

    async def get_lp_user_id(self, user_id: int = None) -> str:

        if self.connection is None or self.connection.is_closed():
            await self.create_connection()

        return await self.connection.fetchval('''SELECT id FROM low_priority_users WHERE user_id = ($1)''', user_id)

    async def process_question(self, user_id: int, question: str, form: str, message_id: int, q_state: str) -> None:
        '''
        Ввод вопроса по форме в БД
        '''
        
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()
            
        form_id = await self.connection.fetchval('''SELECT id FROM form_types WHERE form_tag = $1''', form) 
        
        if q_state == "Pending":
            await self.connection.execute('''INSERT INTO questions_forms (lp_user_id, section_form, question_content, question_message)
                                      VALUES ($1, $2, $3, $4)''', await Database().get_lp_user_id(user_id=user_id), form_id, question, message_id)
        else:
            await self.connection.execute('''INSERT INTO questions_forms (lp_user_id, section_form, question_content, question_message, question_state)
                                      VALUES ($1, $2, $3, $4, $5)''', await Database().get_lp_user_id(user_id=user_id), form_id, question, message_id, q_state)
            
    async def get_specialits_questions(self, specialist_id: int = None, question_status: str = "Pending", return_all_records: bool = False) -> list:
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()
        
        if return_all_records == True:
            all_records = await self.connection.fetch('''SELECT qf.id, lpu.user_id, ft.form_name, qf.question_content, qf.question_date, ap.answer_content, ap.answer_date  
                                                  FROM questions_forms qf
                                                  JOIN answer_process ap ON qf.id = ap.question_id
                                                  JOIN form_types ft ON qf.section_form = ft.id
                                                  JOIN low_priority_users lpu ON qf.lp_user_id = lpu.id''')
            hpu_recs = await self.connection.fetch('''SELECT hpu.user_fio 
                                                        FROM answer_process ap
                                                        JOIN high_priority_users hpu ON ap.specialist_id = hpu.id''')
            
            return all_records, hpu_recs
        
        if question_status == "Accept":
            result = await self.connection.fetch('''SELECT q.id, q.question_content, q.lp_user_id, ft.form_name, q.question_message, rp.subject_name, ap.answer_content
                                                FROM questions_forms q
                                                JOIN form_types ft ON q.section_form = ft.id
                                                JOIN specialist_forms sf ON ft.id = sf.form_id
                                                JOIN high_priority_users hp ON sf.specialist_id = hp.id
                                                JOIN low_priority_users lp ON q.lp_user_id = lp.id
                                                JOIN registration_process rp ON lp.registration_process_id = rp.id
                                                JOIN answer_process ap ON q.id = ap.question_id
                                                WHERE hp.user_id = $1 AND q.question_state = $2''', specialist_id, question_status)
        else:
            result = await self.connection.fetch('''SELECT q.id, q.question_content, q.lp_user_id, ft.form_name, q.question_message, rp.subject_name
                                                FROM questions_forms q
                                                JOIN form_types ft ON q.section_form = ft.id
                                                JOIN specialist_forms sf ON ft.id = sf.form_id
                                                JOIN high_priority_users hp ON sf.specialist_id = hp.id
                                                JOIN low_priority_users lp ON q.lp_user_id = lp.id
                                                JOIN registration_process rp ON lp.registration_process_id = rp.id
                                                WHERE hp.user_id = $1 AND q.question_state = $2''', specialist_id, question_status)
        return result
    
    async def answer_process_report(self, question_id: int, answer: str, specialist_id: int) -> None:
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()

        specialist_id = await self.connection.fetchval('''SELECT id FROM high_priority_users WHERE user_id = ($1)''', specialist_id) if specialist_id > 10000 else specialist_id
        question_existence = await self.connection.fetchrow('''SELECT * FROM answer_process WHERE question_id = $1''', question_id)

        if answer == "Закрытие вопроса":
            await self.connection.execute('''UPDATE questions_forms SET question_state = 'Decline' WHERE id = ($1)''', question_id)
            await self.connection.execute('''INSERT INTO answer_process (question_id, answer_content, specialist_id) VALUES ($1, $2, $3)''', question_id, answer, specialist_id)
        elif answer == "Вопрос взят":
            await self.connection.execute('''UPDATE questions_forms SET question_state = 'Pending' WHERE id = ($1)''', question_id)
            
            if question_existence == None: 
                await self.connection.execute('''INSERT INTO answer_process (question_id, answer_content, specialist_id) VALUES ($1, $2, $3)''', question_id, answer, specialist_id) 
            else:
                await self.connection.execute('''UPDATE answer_process SET answer_content = $1, specialist_id = $2 WHERE question_id = $3''', answer, specialist_id, question_id)
        else:
            await self.connection.execute('''UPDATE questions_forms SET question_state = 'Accept' WHERE id = ($1)''', question_id)
            
            if question_existence == None: 
                await self.connection.execute('''INSERT INTO answer_process (question_id, answer_content, specialist_id) VALUES ($1, $2, $3)''', question_id, answer, specialist_id) 
            else:
                await self.connection.execute('''UPDATE answer_process SET answer_content = $1, specialist_id = $2 WHERE question_id = $3''', answer, specialist_id, question_id)

    async def check_question(self, question_id: int, message_id: int) -> str:
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()
        result = await self.connection.fetchval('''SELECT answer_process.answer_content 
                                                FROM answer_process
                                                JOIN questions_forms qf ON answer_process.question_id = qf.id
                                                WHERE answer_process.question_id = $1 
                                                AND qf.question_message = $2''', question_id, message_id)
        return result
    
    async def get_question_form(self, lp_user_id: int):
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()
        return await self.connection.fetchrow('''SELECT * FROM questions_forms WHERE lp_user_id = ($1)''', lp_user_id)
    
    async def get_miac_information(self, info_type: str, district_id: int = None, miac_id: int = None):
        '''
        Получение информации для создания inline кнопок
        '''
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()
        if info_type == 'federal_district':
            districts = await self.connection.fetch('''SELECT federal_name, district_tag FROM federal_district''')
            return districts
        elif info_type == 'region':
            regions = await self.connection.fetch('''SELECT regions.region_name, regions.region_tag
                                                  FROM regions
                                                  JOIN federal_district_regions ON regions.id = federal_district_regions.region_id
                                                  WHERE federal_district_regions.federal_district_id = $1''', district_id)
            return regions
        elif info_type == 'miac':
            miac = await self.connection.fetchval('''SELECT region_name FROM regions
                                                  WHERE id = $1''', miac_id)
            return miac
        
    async def get_user_history(self, question_id: int, values_range: list = [4, 0]):
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()
        
        temp_dict = dict() ; resulted_dict = dict()
        showed_values, hidden_values = values_range[0], values_range[1]
        
        lp_user_id = await self.connection.fetchval("""SELECT lp_user_id FROM questions_forms WHERE id = $1""", question_id)
        user_name_info = await self.connection.fetchrow("""SELECT lpu.user_id FROM low_priority_users AS lpu WHERE lpu.id = $1""", lp_user_id)
        history_info = await self.connection.fetch(r"""SELECT ft.form_name, qf.question_content, TO_CHAR(qf.question_date, 'DD.MM.YYYY \ HH:MI:SS') AS question_date, ap.answer_content, TO_CHAR(ap.answer_date, 'DD.MM.YYYY \ HH:MI:SS')  AS answer_date
                                                   FROM questions_forms AS qf
                                                   INNER JOIN form_types AS ft ON qf.section_form = ft.id
                                                   INNER JOIN answer_process AS ap ON qf.id = ap.question_id
                                                   WHERE qf.lp_user_id = $1 AND ap.answer_content != 'Вопрос взят' ORDER BY ap.answer_date DESC LIMIT $2 OFFSET $3""", lp_user_id, showed_values, hidden_values)
        number_of_rows = len(history_info)
        
        for i in range(len(history_info)):
            temp_dict.update(zip(["Название формы", "Содержание вопроса", "Дата\время вопроса", "Содержание ответа", "Дата\время ответа"], history_info[i][:5]))
            resulted_dict[f"Запись №{i + 1}"] = temp_dict.copy()
            temp_dict.clear()
        
        return resulted_dict, user_name_info, number_of_rows    
        
    async def get_question_id(self, inputed_question_id: int = 0, message_id: int = 0) -> int:
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()
        
        if inputed_question_id != 0:
            question_data = await self.connection.fetchrow('''
                SELECT questions_forms.*, form_types.form_name, rp.subject_name
                FROM questions_forms
                JOIN form_types ON questions_forms.section_form = form_types.id
                JOIN low_priority_users lp ON questions_forms.lp_user_id = lp.id
                JOIN registration_process rp ON lp.registration_process_id = rp.id
                WHERE questions_forms.id = $1
            ''', inputed_question_id)

            return question_data
        else:
            question_id = await self.connection.fetchval('''SELECT id FROM questions_forms
                                                     WHERE question_message = $1''', message_id)
            return question_id

    async def get_user_id(self, question: str, message_id: int = 0) -> int:
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()
        user_id = await self.connection.fetchval('''SELECT lp_user_id FROM questions_forms
                                                     WHERE question_content ILIKE '%' || $1 || '%' 
                                                     OR question_message = $2''', 
                                                     question, message_id)
        return user_id

    async def get_question_message_id(self, question_id: int) -> str:
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()

        message_id = await self.connection.fetchval('''SELECT question_message FROM questions_forms WHERE id = $1''', question_id)
        return message_id
    
    async def get_specform(self, form_name: str = None, user_id: int = None):
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()

        try:
            if form_name:
                form_info = await self.connection.fetchrow('''SELECT ft.*, sf.specialist_id FROM form_types AS ft
                                                    INNER JOIN specialist_forms AS sf ON ft.id = sf.form_id
                                                    WHERE form_name = $1''', form_name)
                return form_info    
            elif user_id:
                hpu_user_id = await self.connection.fetchval('''SELECT hpu.id FROM high_priority_users AS hpu WHERE hpu.user_id = $1''', user_id)
                form_info = await self.connection.fetch('''SELECT ft.*, sf.specialist_id FROM form_types AS ft
                                                        INNER JOIN specialist_forms AS sf ON ft.id = sf.form_id
                                                        WHERE sf.specialist_id = $1''', hpu_user_id)
                return form_info
        except InterfaceError:
            await asyncio.sleep(3)
            # time.sleep(2)
            await self.get_specform(form_name, user_id)

    async def get_all_spec(self):    
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()
        
        return await self.connection.fetch('''SELECT id, user_fio FROM high_priority_users''')

    async def link_spec_to_form(self, spec_id: int, form_id):
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()
        spec_id = await self.connection.fetch('''SELECT id FROM high_priority_users WHERE user_id = $1''', spec_id)
            
        await self.connection.execute('''INSERT INTO specialist_forms (specialist_id, form_id) VALUES ($1, $2)''', spec_id[0]["id"], form_id)

    async def get_spec_info_by_user_id(self, user_id: int):
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()
        
        result = await self.connection.fetchrow('''SELECT hpu.*, sf.form_id FROM high_priority_users AS hpu
                                       INNER JOIN specialist_forms AS sf ON sf.specialist_id = hpu.id
                                       WHERE hpu.user_id = $1''', user_id)
        
        if result is None:
            return await self.connection.fetchrow('''SELECT hpu.* FROM high_priority_users AS hpu WHERE hpu.user_id = $1''', user_id)
        else:
            return result
    
    async def add_user(self, user_id: int, user_fio: str, privilege_type: str):
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()
        try:
            await self.connection.execute('''INSERT INTO high_priority_users (user_id, user_fio, privilege_type, telegramm_name) VALUES ($1, $2, $3, $4)''', user_id, user_fio, privilege_type, None)
        except UniqueViolationError:
            last_id = await self.connection.fetchval('''SELECT id FROM high_priority_users ORDER BY id DESC LIMIT 1''')
            await self.connection.execute('''INSERT INTO high_priority_users (id, user_id, user_fio, privilege_type, telegramm_name) VALUES ($1, $2, $3, $4, $5)''', last_id + 1,user_id, user_fio, privilege_type, None)
    
    async def delete_user(self, spec_id: int):
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()
            
        spec_id = await self.connection.fetch('''SELECT id, privilege_type FROM high_priority_users WHERE user_id = $1''', spec_id)    
            
        return spec_id[0]["privilege_type"]
        
    async def get_registrated_db(self):
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()

        miac_users = await self.connection.fetch("""SELECT registration_process.* 
                                                 FROM registration_process
                                                 JOIN low_priority_users lp ON registration_process.id = lp.registration_process_id
                                                 WHERE lp.registration_state = 'Accept'""")
        miac_users = await self.connection.fetch("""SELECT registration_process.* 
                                                 FROM registration_process
                                                 JOIN low_priority_users lp ON registration_process.id = lp.registration_process_id
                                                 WHERE lp.registration_state = 'Accept'""")
        return miac_users
    
    async def add_suggestion_to_post(self, post_content: str, post_suggestor: int, pub_type_tuple: tuple, pub_state: str = 'Pending') -> None:
        '''
        Добавление данных для поста публикации в открытый канал или в раздел форм
        '''
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()

        await self.connection.execute('''INSERT INTO publication_process (publication_content, publication_status, post_suggester)
                                      SELECT $1, $2, hp.id
                                      FROM high_priority_users hp
                                      WHERE $3 = hp.user_id''', post_content, pub_state, post_suggestor)
        last_row_id = await self.connection.fetchval('''SELECT pp.id FROM publication_process AS pp ORDER BY publication_date DESC LIMIT 1;''')
        await self.connection.execute('''UPDATE publication_process SET publication_type = ROW($1, $2, $3, $4), publication_status = $5 WHERE id = $6''', pub_type_tuple[0], pub_type_tuple[2], pub_type_tuple[3], pub_type_tuple[1], pub_state, last_row_id)

    async def get_posts_to_public(self) -> list[Record]:
        '''
        Получение данных запроса на публикацию
        '''
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()

        result = await self.connection.fetch("""SELECT * FROM publication_process
                                             WHERE publication_status = 'Pending'""")
        
        return result
    
    async def update_publication_status(self, publication_status: str, pub_id: int) -> None:
        '''
        Обновление статуса публикации и столбца с данным о принявшем решение
        '''
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()

        await self.connection.execute("""UPDATE publication_process
                                      SET publication_status = $1, post_regulator = hp.id
                                      FROM high_priority_users hp
                                      WHERE publication_process.id = $2 """, publication_status, pub_id)
        
    async def extract_form_info_by_tag(self, tag_info: str):
        '''
        Извлечение данных о форме по тэгу формы
        '''
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()
        
        form_info = await self.connection.fetchrow("""SELECT ft.*, sf.specialist_id  FROM form_types AS ft
                                       INNER JOIN specialist_forms AS sf ON ft.id = sf.form_id
                                       WHERE ft.form_tag = $1""", tag_info)
        return form_info

    async def get_subject_name(self, user_id: int) -> str:
        '''
        Возврат имени субьекта
        '''
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()

        result = await self.connection.fetchval('''SELECT subject_name
                                                FROM registration_process
                                                WHERE user_id = $1''', user_id)
        return result

    async def add_form(self, form_name: str, form_tag: str):
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()
        
        await self.connection.execute('''INSERT INTO form_types (form_name, form_tag) VALUES ($1, $2)''', form_name, form_tag)
    
    async def delete_form(self, form_tag: str):
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()
        
        form_id = await self.connection.fetchval('''SELECT id FROM form_types WHERE form_tag = $1''', form_tag)
        await self.connection.execute('''DELETE FROM specialist_forms WHERE form_id = $1''', form_id)
        await self.connection.execute('''DELETE FROM form_types WHERE form_tag = $1''', form_tag)        
    
    async def uploading_file(self, file_id: str, button_type: str, upload_tuple: tuple, admin_id: int = 4):
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()
        
        await self.connection.execute('''INSERT INTO admin_file_uploading (file_id, file_format, button_type, admin_id) VALUES 
                                      ($1, ROW($2, $3, $4, $5), $6, $7)''', file_id, upload_tuple[0], upload_tuple[2], upload_tuple[3], upload_tuple[1], button_type, admin_id)

    async def loading_files(self, button_type: str, time: str):
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()
            
        if time == '1 week':
            files_info = await self.connection.fetch("""SELECT * FROM admin_file_uploading 
                                                     WHERE button_type = $1 AND
                                                     upload_date >= CURRENT_DATE - INTERVAL '1 week'
                                                     ORDER BY upload_date ASC""", button_type)
        else:
            files_info = await self.connection.fetch("""SELECT * FROM admin_file_uploading
                                                     WHERE button_type = $1 AND
                                                     upload_date >= 'epoch'::timestamp
                                                     ORDER BY upload_date ASC""", button_type)
        return files_info
    
    async def update_user_info(self, **kwargs):
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()
        
        try:
            await self.connection.execute('''UPDATE registration_process SET telegram_name = $1 WHERE user_id = $2''', kwargs['telegram_name'], kwargs['user_id'])
        except PostgresError:
            return "Failed to find the string"

    async def get_form_questions(self, form_name: str = None, question_status: str = "Pending", ignore_forms = False) -> Record:
        '''
        Возвращает список вопросов по определенной форме
        '''
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()

        if ignore_forms == False:
            if question_status == "Pending":
                result = await self.connection.fetch('''SELECT q.id, q.question_content, q.lp_user_id, ft.form_name, q.question_message, rp.subject_name
                                                FROM questions_forms q
                                                JOIN form_types ft ON q.section_form = ft.id
                                                JOIN low_priority_users lp ON q.lp_user_id = lp.id
                                                JOIN registration_process rp ON lp.registration_process_id = rp.id
                                                WHERE ft.form_tag = $1 AND q.question_state = $2''', form_name, question_status)
            else: 
                result = await self.connection.fetch('''SELECT q.id, q.question_content, q.lp_user_id, ft.form_name, q.question_message, ap.answer_content, ft.form_tag, rp.subject_name
                                                FROM questions_forms q
                                                JOIN form_types ft ON q.section_form = ft.id
                                                JOIN low_priority_users lp ON q.lp_user_id = lp.id
                                                JOIN answer_process ap ON q.id = ap.question_id
                                                JOIN registration_process rp ON lp.registration_process_id = rp.id
                                                WHERE ft.form_tag = $1 AND q.question_state = $2 AND ap.answer_content != 'Вопрос взят';''', form_name, question_status)
        else:
            result = await self.connection.fetch('''SELECT q.id, q.question_content, q.lp_user_id, ft.form_name, ft.form_tag, q.question_message, rp.subject_name
                                                FROM questions_forms q
                                                JOIN form_types ft ON q.section_form = ft.id
                                                JOIN low_priority_users lp ON q.lp_user_id = lp.id
                                                JOIN registration_process rp ON lp.registration_process_id = rp.id
                                                WHERE q.question_state = $1''', question_status)
        return result
    
    async def get_link(self, user_id: int):
        '''
        Возвращает ссылку на чат по согласованию форм
        '''
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()

        result = await self.connection.fetch('''SELECT rl.link
                                                FROM regions_links rl
                                                JOIN regions rg ON rl.region_id = rg.id
                                                JOIN registration_process rp ON rg.region_name = rp.subject_name
                                                WHERE rp.user_id = $1''', user_id)
        
        return result
    
    async def get_files_to_delete(self, button_type: str):
        '''
        Возвращает список файлов, доступных для определенного отдела    
        '''
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()

        result = await self.connection.fetch('''SELECT * FROM admin_file_uploading
                                                    WHERE button_type = $1''', button_type)
        
        return result

    async def delete_files(self, file_id: int):
        '''
        Удаляет файлы по их id
        '''
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()

        await self.connection.execute('''DELETE FROM admin_file_uploading
                                            WHERE id = $1''', file_id)
        
    async def execute_query(self, query: str, arguments: list):
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()
        query = query.replace('\n', '')
        result = await self.connection.fetch(query, *arguments)
        return result
    
    @checking_file_decorator
    async def truncate_data(self, callback):
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()
        await self.connection.execute("""TRUNCATE answer_process, questions_forms, low_priority_users, registration_process""")
        return True
    
    async def forms_question_group(self, form_id):
        if self.connection is None or self.connection.is_closed():
            await self.create_connection()
        result = await self.connection.fetch("""SELECT q_forms.question_content, a_process.answer_content FROM answer_process AS a_process 
                                    JOIN questions_forms AS q_forms ON a_process.question_id = q_forms.id WHERE q_forms.section_form = $1 AND a_process.answer_content NOT IN ('Закрытие вопроса', 'Вопрос взят')""", form_id)
        return result
    
    
    
    
    
    

    
    
    
    
    
    
    
    
    