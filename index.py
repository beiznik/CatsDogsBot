import json
import requests
import os
import telebot as tb
from telebot.util import quick_markup
import ydb


TG_TOKEN=os.environ.get('BOT_TOKEN')
bot = tb.TeleBot(TG_TOKEN)
URL = f"https://api.telegram.org/bot{TG_TOKEN}/"


def tgtext(text): # <-- преобзразует текст в формат, который может пережевать телеграм с разметкой типа MarkdownV2
    for char in [ '_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!' ]:
        text = text.replace(char, '\\' + char)
    return(text)
    
def send_messageF(text, chat_id, message,premium,message_id): #<-- тут вся основная логика. Проверят что пришло, высылает сообщение пользователю, вызывает другие функции
    DB_TOKEN = requests.post('https://iam.api.cloud.yandex.net/iam/v1/tokens', json={
        'yandexPassportOauthToken': os.environ.get('TOKEN')
    }).json()
    pool = dbstart(DB_TOKEN['iamToken'])

    markupanimals = quick_markup({
    "Собакен "+u"\U0001F415": {'callback_data': 'dog'},
    "Котейка "+u"\U0001F638": {'callback_data': 'cat'},
    "Анекдот от бати ": {'callback_data': 'dad'},
    "Анекдот про программистов ": {'callback_data': 'programming'},
    }, row_width=2)
    markupmark_cat = quick_markup({
    "Хороший котик": {'callback_data': 'good_cat'},
    "Нехороший котик": {'callback_data': 'bad_cat'},
    }, row_width=2)
    markupmark_dog = quick_markup({
    "Хороший пёсик": {'callback_data': 'good_dog'},
    "Нехороший пёсик": {'callback_data': 'bad_dog'},
    }, row_width=2)
    if text=='/start' and premium=="None":
        bot.send_message(chat_id, "Beiznik bot приветствует тебя, плебей без премиума! Выбирай. А еще я могу показать прогноз погоды, если ты напишешь координаты места, например так: /weather 52.52 14.14", reply_markup=markupanimals)
    elif text=='/start' and premium!="None":
        bot.send_message(chat_id, "Beiznik bot приветствует тебя, премиальный! Выбирай. А еще я могу показать прогноз погоды, если ты напишешь координаты места, например так: /weather 52.52 14.14", reply_markup=markupanimals)
    elif text=="dog": 
        photo=requests.get('https://api.thedogapi.com/v1/images/search').json()[0]['url']
        bot.send_photo(chat_id, photo, reply_markup=markupmark_dog)

    elif text=='cat': 
        photo=requests.get('https://api.thecatapi.com/v1/images/search').json()[0]['url']
        fact = requests.get('https://catfact.ninja/fact').json()['fact']
        bot.send_photo(chat_id, photo, reply_markup=markupmark_cat, caption=fact)
        
    elif text=="dad":
        dad = requests.get('https://official-joke-api.appspot.com/jokes/dad/random').json()[0]
        text = tgtext(str(dad['setup']))+' || '+tgtext(str(dad['punchline']))+' ||'
        bot.send_message(chat_id,text=text ,reply_markup=markupanimals, parse_mode = 'MarkdownV2')

    elif text=="programming":
        progr = requests.get('https://official-joke-api.appspot.com/jokes/programming/random').json()[0]
        text = tgtext(str(progr['setup']))+' || '+tgtext(str(progr['punchline']))+' || '
        bot.send_message(chat_id,text=text ,reply_markup=markupanimals, parse_mode = 'MarkdownV2')

    elif text=="good_cat":
        final_text="Кайф. Продолжаем!"
        bot.send_message(chat_id, final_text, reply_markup=markupanimals)
        markadd(pool, message_id, chat_id, 1, 0)

    elif text=="bad_cat":
        final_text="Ой. Попробуй еще раз!"
        bot.send_message(chat_id, final_text, reply_markup=markupanimals)
        markadd(pool, message_id, chat_id, -1, 0)

    elif text=="good_dog":
        final_text="Кайф. Продолжаем!"
        bot.send_message(chat_id, final_text, reply_markup=markupanimals)
        markadd(pool, message_id, chat_id, 0, 1)

    elif text=="bad_dog":
        final_text="Ой. Попробуй еще раз!"
        bot.send_message(chat_id, final_text, reply_markup=markupanimals)
        markadd(pool, message_id, chat_id, 0, -1)

    elif text.count('/weather')>0:
       
        z = weather(text)
        if z == 'Broken':
            bot.send_message(chat_id,text='Ты точно правильно написал команду для погоды?' ,reply_markup=markupanimals, parse_mode = 'MarkdownV2')
        elif "error" in z:
            bot.send_message(chat_id,text='Ты точно правильно написал команду для погоды?' ,reply_markup=markupanimals, parse_mode = 'MarkdownV2')
        else: 
            messagetext = 'В указанной точке на '+str(z["daily"]["time"][0])+' ожидается температура от '+str(z["daily"]["temperature_2m_min"][0])+' до '+str(z["daily"]["temperature_2m_max"][0])+' градусов, осадки - '+str(z["daily"]["rain_sum"][0])+'мм., на на '+str(z["daily"]["time"][1])+' ожидается температура от '+str(z["daily"]["temperature_2m_min"][1])+' до '+str(z["daily"]["temperature_2m_max"][1])+' градусов, осадки - '+str(z["daily"]["rain_sum"][1])+'мм.'
            bot.send_message(chat_id,text=messagetext,reply_markup=markupanimals)
    else:
        bot.send_message(chat_id,"Ничего не понял. ", reply_markup=markupanimals)

def weather(message):#<-- Запрос погоды в точке
    
    #message=message.replace(",",".")
    messagesplited=message.split()
    if len(messagesplited)!=3: 
        
        return("Broken")
    else:
        longtitude = messagesplited[1]
        altitude = messagesplited[2]
        weather_c = requests.get('https://api.open-meteo.com/v1/forecast?latitude='+altitude+'&longitude='+longtitude+'&daily=temperature_2m_max,temperature_2m_min,rain_sum&forecast_days=2').json()
        
        return(weather_c)
    
def jsonprepare(text): # <-- Преобразователь типа данных User в json
    text=text.replace('\'', '"')
    text=text.replace('False','"False"')
    text = text.replace('True', '"True"')
    text = text.replace('None', '"None"')
    return text

def handler(event, context): #<-- запрос идет сюда, обрабатывает команды типа / и нажатия на кнопки
    message = json.loads(event['body'])
    message_id = message["update_id"]
    if "callback_query" in message:
        reply = message['callback_query']['data']
        chat_id = message['callback_query']['from']['id']
        fn = message['callback_query']['from']['first_name']
    elif 'message' in message: 
        reply = message['message']['text']
        
        chat_id = message['message']['chat']['id']
        fn = message['message']['chat']['first_name']
    current_user = tb.types.User(id=chat_id, is_bot=False, first_name=fn)
    user_status=jsonprepare(str(tb.types.User(id=chat_id, is_bot=False, first_name=fn)))
    send_messageF(reply, chat_id, message, json.loads(user_status)["is_premium"], message_id)
    return {
        'statusCode': 200
    }

def dbstart(DB_TOKEN): #<-- Подключение к БД
    driver_config = ydb.DriverConfig(
        'grpcs://ydb.serverless.yandexcloud.net:2135', '/ru-central1/b1goaa2gdd9t2vq4q9ks/etnlc045jmpmqh9na66f',
        credentials=ydb.credentials.AccessTokenCredentials(f'Bearer {DB_TOKEN}'),
        root_certificates=ydb.load_ydb_root_certificate()
    )
    driver = ydb.Driver(driver_config)
    driver.wait(fail_fast=True, timeout=5)
    pool = ydb.SessionPool(driver)
    return (pool)

def markadd(pool, message_id, user_id, cat_mark, dog_mark): #<--Добавление записи в БД
    text = f"""UPSERT INTO catdogstats
    (id, id_user, voice_cat, voice_dog)
    VALUES ({message_id}, {user_id},{cat_mark},{dog_mark});
    """
    return pool.retry_operation_sync(lambda s: s.transaction().execute(
        text,
        commit_tx=True,
        settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2)
    ))
