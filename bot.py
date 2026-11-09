import telebot
from telebot import types
import threading
import time

TOKEN = '8243680262:AAF-4SqQSgvDZvmaiJBYcy-5kb9jZAUxr0w'
GROUP_ID = '@driverservice_kg'

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()
user_data = {}
user_languages = {}

# Uchet dobavlennyh lyudey: {user_id: kolichestvo}
invited_counts = {}
unlocked_users = set()

auto_posting_active = False
auto_post_interval = 60  # Po umolchaniyu kazhdye 60 minut

# Avtoposting (otpravka video i teksta v gruppu)
def auto_poster():
    global auto_posting_active, auto_post_interval
    while True:
        if auto_posting_active:
            ad_text = (
                "📍 Кто:                  DRIVER SERVICE\n\n"
                "📍 Откуда:       Бишкек / Иссык-Куль\n\n"
                "📍 Куда:           По всем направлениям\n\n"
                "📍 Когда:        В любое время 24/7\n\n"
                "📍 Место:        4/5/7     Только Салон\n\n"
                "📍 Цена:         Договорная\n\n"
                "📍 Авто:          Легковой, Минивэн\n\n"
                "                     Можно туда и обратно,\n"
                "                     а также принимаем\n"
                "                     предварительные заказы\n\n"
                "📍 Тел:                 +996705728728\n"
                "    WhatsApp:   +996705728728"
            )
            
            markup = types.InlineKeyboardMarkup()
            btn_order = types.InlineKeyboardButton("Создать заказ", url="https://t.me/driver_service_kg_bot?start=order")
            markup.add(btn_order)
            
            try:
                # Otpravka video iz toy zhe papki
                with open('IMG_3938.MP4', 'rb') as video_file:
                    bot.send_video(chat_id=GROUP_ID, video=video_file, caption=ad_text, reply_markup=markup)
            except Exception as e:
                print(f"Oshibka avtopostinga: {e}")
                    
        time.sleep(auto_post_interval * 60)

threading.Thread(target=auto_poster, daemon=True).start()

# Upravlenie avtopostingom iz lichki (/start_auto 30)
@bot.message_handler(commands=['start_auto'])
def start_auto(message):
    global auto_posting_active, auto_post_interval
    parts = message.text.split()
    
    if len(parts) > 1 and parts[1].isdigit():
        auto_post_interval = int(parts[1])
        auto_posting_active = True
        bot.reply_to(message, f"✅ Автопостинг включен! Объявление с видео будет отправляться каждые {auto_post_interval} минут.")
    else:
        auto_posting_active = True
        bot.reply_to(message, "✅ Автопостинг включен (каждые 60 минут). Чтобы задать свое время: /start_auto 30")

@bot.message_handler(commands=['stop_auto'])
def stop_auto(message):
    global auto_posting_active
    auto_posting_active = False
    bot.reply_to(message, "🛑 Автопостинг остановлен.")

# Uchet dobavlennyh lyudey v gruppu
@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    inviter = message.from_user
    if inviter and not inviter.is_bot:
        inviter_id = inviter.id
        added_count = len(message.new_chat_members)
        
        if inviter_id not in invited_counts:
            invited_counts[inviter_id] = 0
        invited_counts[inviter_id] += added_count
        
        current_total = invited_counts[inviter_id]
        user_name = inviter.first_name
        
        if current_total >= 10:
            unlocked_users.add(inviter_id)
            try:
                bot.send_message(message.chat.id, f"🎉 Поздравляем, {user_name}! Вы добавили 10 человек и можете писать в группу!")
            except:
                pass
        else:
            remaining = 10 - current_total
            try:
                bot.send_message(message.chat.id, f"📌 {user_name}, вы добавили {current_total}/10 человек. Осталось добавить еще {remaining}.")
            except:
                pass

# Proverka soobsheniy v gruppe (bez knopok)
@bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'])
def check_group_messages(message):
    if message.text and not message.text.startswith('/'):
        user_id = message.from_user.id
        if user_id in unlocked_users:
            return
            
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except Exception:
            pass
        
        try:
            user_mention = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
            current_count = invited_counts.get(user_id, 0)
            warning_text = f"‼ 🚀 {user_mention}, вы добавили {current_count}/10 человек. Добавьте еще {10 - current_count}, чтобы писать в группу!"
            
            # Otpravka preduprezhdeniya bez knopok
            bot.send_message(message.chat.id, warning_text)
        except Exception as e:
            print(f"Oshibka: {e}")

@bot.message_handler(commands=['pin'])
def send_pinned_menu(message):
    if message.chat.type in ['group', 'supergroup']:
        markup = types.InlineKeyboardMarkup()
        btn_order = types.InlineKeyboardButton("Создать заказ", url="https://t.me/driver_service_kg_bot?start=order")
        markup.add(btn_order)
        bot.send_message(message.chat.id, "🚗 DRIVER SERVICE\nНажмите кнопку ниже, чтобы создать заказ:", reply_markup=markup)

# Start v lichnyh soobshcheniyah
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_driver = types.InlineKeyboardButton("🚗 Водитель", callback_data="role_driver")
    btn_pass = types.InlineKeyboardButton("👤 Пассажир", callback_data="role_pass")
    markup.add(btn_driver, btn_pass)
    
    bot.reply_to(
        message, 
        f"🚗 DRIVER SERVICE\n\nЗдравствуйте, {user_name}! 👋\nВыберите вашу роль:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('role_'))
def set_role(call):
    user_id = call.message.chat.id
    user_data[user_id] = {}
    
    if call.data == 'role_driver':
        user_data[user_id]['role'] = 'Водитель'
        bot.answer_callback_query(call.id, "Роль: Водитель")
    else:
        user_data[user_id]['role'] = 'Пассажир'
        bot.answer_callback_query(call.id, "Роль: Пассажир")
        
    ask_regions(call.message, "Откуда выезжаете (выберите или напишите):", "from")

def ask_regions(message, text_msg, step):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("Бишкек", callback_data=f"reg_{step}_bishkek"),
        types.InlineKeyboardButton("Чуйская обл.", callback_data=f"reg_{step}_chui"),
        types.InlineKeyboardButton("Иссык-Куль", callback_data=f"reg_{step}_issyk"),
        types.InlineKeyboardButton("Нарын", callback_data=f"reg_{step}_naryn"),
        types.InlineKeyboardButton("Талас", callback_data=f"reg_{step}_talas"),
        types.InlineKeyboardButton("Джалал-Абад", callback_data=f"reg_{step}_jalal"),
        types.InlineKeyboardButton("Ош", callback_data=f"reg_{step}_osh"),
        types.InlineKeyboardButton("Баткен", callback_data=f"reg_{step}_batken"),
    )
    
    if message.content_type == 'text':
        bot.send_message(message.chat.id, text_msg, reply_markup=markup)
    else:
        try:
            bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=text_msg, reply_markup=markup)
        except:
            bot.send_message(message.chat.id, text_msg, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('reg_'))
def handle_region_choice(call):
    parts = call.data.split('_')
    step = parts[1]
    region = parts[2]
    
    region_names = {
        'bishkek': 'Бишкек', 'chui': 'Чуйская область', 'issyk': 'Иссык-Куль',
        'naryn': 'Нарын', 'talas': 'Талас', 'jalal': 'Джалал-Абад', 'osh': 'Ош', 'batken': 'Баткен'
    }
    selected_name = region_names.get(region, region)
    user_id = call.message.chat.id
    
    if step == 'from':
        user_data[user_id]['from_where'] = selected_name
        bot.answer_callback_query(call.id, f"Выбрано: {selected_name}")
        ask_regions(call.message, "Куда едете (выберите или напишите):", "to")
    else:
        user_data[user_id]['to_where'] = selected_name
        bot.answer_callback_query(call.id, f"Выбрано: {selected_name}")
        ask_date(call.message)

@bot.message_handler(func=lambda message: message.chat.id in user_data and 'from_where' not in user_data[message.chat.id])
def get_from_text(message):
    if message.text.startswith('/'): return
    user_data[message.chat.id]['from_where'] = message.text
    ask_regions(message, "Куда едете (выберите или напишите):", "to")

@bot.message_handler(func=lambda message: message.chat.id in user_data and 'from_where' in user_data[message.chat.id] and 'to_where' not in user_data[message.chat.id])
def get_to_text(message):
    if message.text.startswith('/'): return
    user_data[message.chat.id]['to_where'] = message.text
    ask_date(message)

def ask_date(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📅 Сегодня", callback_data="date_today"),
        types.InlineKeyboardButton("📅 Завтра", callback_data="date_tom")
    )
    bot.send_message(message.chat.id, "Когда поездка (выберите дату):", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('date_'))
def set_date(call):
    user_id = call.message.chat.id
    user_data[user_id]['when'] = 'Сегодня' if 'today' in call.data else 'Завтра'
    bot.answer_callback_query(call.id, "Дата выбрана")
    ask_seats(call.message)

def ask_seats(message):
    role = user_data[message.chat.id].get('role', 'Водитель')
    text = "Какая машина по вместимости?" if role == 'Водитель' else "Сколько мест нужно?"
    bot.send_message(message.chat.id, text)
    bot.register_next_step_handler(message, get_seats)

def get_seats(message):
    if message.text and message.text.startswith('/'): return
    user_data[message.chat.id]['seats'] = message.text
    ask_price(message)

def ask_price(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🤝 Договорная", callback_data="price_dog"))
    bot.send_message(message.chat.id, "Какая цена? (Или введите сумму):", reply_markup=markup)
    bot.register_next_step_handler(message, get_price)

@bot.callback_query_handler(func=lambda call: call.data == 'price_dog')
def set_price_dog(call):
    user_data[call.message.chat.id]['price'] = 'Договорная'
    bot.answer_callback_query(call.id, "Цена: Договорная")
    ask_comment(call.message)

def get_price(message):
    if message.text and message.text.startswith('/'): return
    user_data[message.chat.id]['price'] = message.text
    ask_comment(message)

def ask_comment(message):
    bot.send_message(message.chat.id, "Комментарии (например: От дома до дома, с багажом):")
    bot.register_next_step_handler(message, get_comment)

def get_comment(message):
    if message.text and message.text.startswith('/'): return
    user_data[message.chat.id]['comment'] = message.text
    role = user_data[message.chat.id]['role']
    if role == 'Водитель':
        ask_auto(message)
    else:
        ask_phone(message)

def ask_auto(message):
    bot.send_message(message.chat.id, "Какая марка авто?")
    bot.register_next_step_handler(message, get_auto)

def get_auto(message):
    if message.text and message.text.startswith('/'): return
    user_data[message.chat.id]['auto'] = message.text
    ask_media(message)

def ask_media(message):
    bot.send_message(message.chat.id, "Отправьте фотографию или видео вашего автомобиля:")
    bot.register_next_step_handler(message, get_media)

def get_media(message):
    if message.content_type == 'photo':
        user_data[message.chat.id]['media_type'] = 'photo'
        user_data[message.chat.id]['media_id'] = message.photo[-1].file_id
        ask_phone(message)
    elif message.content_type == 'video':
        user_data[message.chat.id]['media_type'] = 'video'
        user_data[message.chat.id]['media_id'] = message.video.file_id
        ask_phone(message)
    else:
        bot.send_message(message.chat.id, "Пожалуйста, отправьте именно фотографию или видео!")
        bot.register_next_step_handler(message, get_media)

def ask_phone(message):
    bot.send_message(message.chat.id, "Введите ваш номер телефона для связи:")
    bot.register_next_step_handler(message, finalize)

def finalize(message):
    if message.text and message.text.startswith('/'): return
    data = user_data[message.chat.id]
    phone = message.text.strip()
    role = data['role']
    
    if role == 'Водитель':
        text = (
            f"🚗 Водитель: DRIVER SERVICE\n"
            f"✅ Проверенный водитель ✅\n\n"
            f"📍 Откуда: {data['from_where']}\n"
            f"📍 Куда: {data['to_where']}\n\n"
            f"📅 Когда: {data['when']}\n"
            f"👥 Количество мест: {data['seats']}\n"
            f"💬 Комментарии: {data['comment']}\n"
            f"💰 Цена: {data['price']}\n"
            f"🚗 Авто: {data['auto']}\n\n"
            f"☎️ Номер телефона: {phone}"
        )
    else:
        text = (
            f"👤 Пассажир: DRIVER SERVICE\n\n"
            f"📍 Откуда: {data['from_where']}\n"
            f"📍 Куда: {data['to_where']}\n\n"
            f"📅 Когда: {data['when']}\n"
            f"👥 Количество мест: {data['seats']}\n"
            f"💬 Комментарии: {data['comment']}\n"
            f"💰 Цена: {data['price']}\n\n"
            f"☎️ Номер телефона: {phone}"
        )
    
    markup = types.InlineKeyboardMarkup()
    clean_phone = phone.replace('+', '').replace(' ', '')
    whatsapp_btn = types.InlineKeyboardButton("Написать ватсап", url=f"https://wa.me/{clean_phone}")
    markup.add(whatsapp_btn)
    
    try:
        if role == 'Водитель' and 'media_id' in data:
            if data['media_type'] == 'photo':
                bot.send_photo(chat_id=GROUP_ID, photo=data['media_id'], caption=text, reply_markup=markup)
            else:
                bot.send_video(chat_id=GROUP_ID, video=data['media_id'], caption=text, reply_markup=markup)
        else:
            bot.send_message(chat_id=GROUP_ID, text=text, reply_markup=markup)
    except Exception as e:
        print(f"Oshibka: {e}")
            
    bot.send_message(message.chat.id, "✅ Ваше объявление успешно опубликовано в группе!")

print("DRIVER SERVICE bot is running...")
bot.infinity_polling()