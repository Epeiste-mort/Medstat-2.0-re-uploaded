import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from rag_run import SmartModel
from non_script_files.config import API_TELEGRAM
from db_actions import Database
from keyboards import Admin_Keyboards, User_Keyboards
import non_script_files
import pickle
import os 
import json 

dp = Dispatcher(storage=MemoryStorage())
db = Database()
bot = Bot(API_TELEGRAM, parse_mode=ParseMode.HTML)
llm_model = SmartModel(chunk_num=5, yandex_connect=False, db_connect=False)

async def on_startup():
    await db.create_connection()
    await db.create_table()
    await db.add_higher_users()
    
    pickle_file = r'non_script_files\forms_keyboard.pickle'
    
    if os.path.exists(pickle_file):
        with open(pickle_file, 'rb') as f:
            pkl_data = pickle.load(f)
            
            User_Keyboards.forms_keyboard = pkl_data["user_key"]
            Admin_Keyboards.forms_keyboard = pkl_data["adm_key"]
            non_script_files.config.forms_data = pkl_data["forms_data"]
            
    else:
        with open(pickle_file, 'wb') as f:
            pkl_data = {
                "adm_key":Admin_Keyboards.forms_keyboard,
                "user_key":User_Keyboards.forms_keyboard,
                "forms_data":non_script_files.config.forms_data
                }
            
            pickle.dump(pkl_data, f)
    print('Бот запущен!')

async def on_shutdown():
    with open(r'non_script_files\forms_keyboard.pickle', 'wb') as f:
        pkl_data = {
                "adm_key":Admin_Keyboards.forms_keyboard,
                "user_key":User_Keyboards.forms_keyboard,
                "forms_data":non_script_files.config.forms_data
                }
            
        pickle.dump(pkl_data, f)
    
    with open(r"priority_list.json", 'w', encoding='utf-8') as file:
        json.dump(non_script_files.config.priority_list, file, ensure_ascii=False, indent=4)
    
    print('Бот выключен!')

async def main() -> None:
    from handlers import message_handlers, callback_handlers
    await bot.delete_webhook(drop_pending_updates=True)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    dp.include_routers(message_handlers.router,
                       callback_handlers.router)

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == '__main__':
    asyncio.run(main())