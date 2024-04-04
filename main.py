import os
import time
import telebot,requests,urllib3,ssl
import logging

BOT_TOKEN = os.environ.get('BOT_TOKEN') # export BOT_TOKEN='your_bot_token_from_@botfather'
from_chat = int(os.environ.get('FROM_CHAT')) # chat_id, which chat to copy
to_chat = int(os.environ.get('TO_CHAT')) # chat_id, copy to which chat
user_id = int(os.environ.get('USER_ID'))
DELAY_TIME = 3 # after each copy delay 2s
whitelist = [] # user_id, who can use the bot
error_list = (requests.exceptions.SSLError, urllib3.exceptions.SSLError,ssl.SSLEOFError,
              requests.exceptions.ReadTimeout,urllib3.exceptions.ReadTimeoutError)
stop_task_flag = False
record = 0

bot = telebot.TeleBot(BOT_TOKEN)

logging.basicConfig(filename='run.log', level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s')


# Init, now only support one user.
whitelist.append(user_id)

# Avoid abused
@bot.message_handler(func=lambda message: message.from_user.id not in whitelist)
def not_in_whitelist(message):
    logging.info(f'user {message.chat.id} try to use bot ...')
    bot.send_message(message.chat.id, "抱歉，你没有权限使用该机器人。")

@bot.message_handler(commands=['start'])
def start_info(message):
    text = '''Hi
    /start:  欢迎命令
    /show:  展示目前所有配置
    /from:  设置来源群组id
    /to:    设置目的群组id
    /last:  上一条copy命令的截止id
    /copy:  开始复制，请随指示操作
    /stop:  停止copy，由于未开启异步，意义不大
    '''
    logging.info(f'user {message.chat.id} use /start ...')
    bot.reply_to(message, text, parse_mode="Markdown")


@bot.message_handler(commands=['show'])
def show_config(message):
    logging.info(f'user {message.chat.id} use /show ...')
    text=f'''参数：
    当前用户：`{message.chat.id}`
    来源群组：`{from_chat}`
    目标群组：`{to_chat}`
    最后一次copy记录：`{record}`
    '''
    bot.reply_to(
        message, text, parse_mode="Markdown")


@bot.message_handler(commands=['from'])
def change_from_id(message):
    logging.info(f'user {message.chat.id} use /from ...')
    send_msg = bot.send_message(
        message.chat.id, "请转发一条来源群组的消息")
    bot.register_next_step_handler(send_msg, get_from)

def get_from(message):
    global from_chat
    from_chat = message.forward_from_chat.id
    logging.info(f'user {message.chat.id} set from_chat to {from_chat} ...')
    bot.reply_to(
        message, f"已设置 `from_chat` 的 id 为: `{from_chat}`", parse_mode="Markdown")

@bot.message_handler(commands=['to'])
def change_from_id(message):
    logging.info(f'user {message.chat.id} use /to ...')
    send_msg = bot.send_message(
        message.chat.id, "请转发一条目的群组的消息")
    bot.register_next_step_handler(send_msg, get_to)

def get_to(message):
    global to_chat
    to_chat = message.forward_from_chat.id
    logging.info(f'user {message.chat.id} set to_chat to {to_chat} ...')
    bot.reply_to(
        message, f"已设置 `to_chat` 的 id 为: `{to_chat}`", parse_mode="Markdown")

@bot.message_handler(commands=['stop'])
def stop_task(message):
    global stop_task_flag
    stop_task_flag = True
    logging.info(f'user {message.chat.id} use /stop ...')
    bot.reply_to(message, "Task stopped.")
 
@bot.message_handler(commands=['last'])
def get_last_info(message):
    text = f'上一次copy的截止id是 {record}'
    logging.info(f'user {message.chat.id} use /last ...')
    bot.send_message(message.chat.id, text)

# main function
@bot.message_handler(commands=['copy'])
def copy_handler(message):
    text = "请输入起始、结束消息id，用空格分开：\n(此部分暂未编写任何错误处理，请谨慎设置id)"
    send_msg = bot.send_message(
        message.chat.id, text, parse_mode="Markdown")
    logging.info(f'user {message.chat.id} use /copy ...')
    bot.register_next_step_handler(send_msg, file_handler)

def file_handler(message):
    logging.info(f'with the text {message.text}')
    start_id, end_id = map(int, message.text.split())
    global stop_task_flag
    global record
    passed = 0
    stop_task_flag = False
    bot.send_message(message.chat.id, "Copying ...", parse_mode="Markdown")
    
    sign = start_id
    while sign <= end_id:
    # for sign in range(start_id, end_id + 1):
        if stop_task_flag:         
            break
        
        try:
            bot.copy_message(chat_id=to_chat, from_chat_id=from_chat, message_id=sign)
        except telebot.apihelper.ApiTelegramException as e:
            if e.error_code == 400:
                bot.reply_to(message, f"无法复制消息 {sign}，消息无法访问或已被删除")
                bot.send_message(message.chat.id, "跳过该条消息...")
                passed += 1
                logging.error(f'跳过消息 {sign} ')
                continue
            else:
                bot.reply_to(message, "复制出现错误，请重试或检查服务器状况")
                break
            
        except () as ssl_error:
            # bot.send_message(message.chat.id, "服务器ssl连接错误，这可能出于网络波动 ...")
            print("""
                  ====================
                  =      ERROR       =
                  ====================
                  """)
            logging.error(f'SSLError: {ssl_error}')
            print(f'SSLError: {ssl_error}')
            time.sleep(DELAY_TIME)
            
            continue

        except Exception as other:
            other_err = f"发生未知错误 {other}"
            bot.send_message(message.chat.id, other_err)
            print("""
                  ====================
                  =      ERROR       =
                  ====================
                  """)
            print(other_err)
            logging.error(other_err)
            break


        text = f'目前已经复制完第{sign}条'
        print(text)
        time.sleep(DELAY_TIME)

        record = sign
        sign += 1

    # unbound warning for sign here
    if stop_task_flag:
        text = f'任务已结束\n应复制 {end_id - start_id } 条消息\n实际复制 {sign - start_id - passed - 1} 条消息'
    else:
        text = f'任务已结束\n应复制 {end_id - start_id + 1} 条消息\n实际复制 {sign - start_id - passed} 条消息'
    print(text)
    logging.info(text)


    bot.send_message(message.chat.id, text, parse_mode="Markdown")
    bot.clear_step_handler(message)




print("Bot start")
bot.infinity_polling()
