import os
import time
import telebot
import logging

'''
# If you can't set proxy outside, just use this with PySocks installed
import socket
import socks

# change the port to what you use
socks.set_default_proxy(socks.SOCKS5, "localhost", 7890)
socket.socket = socks.socksocket
'''

BOT_TOKEN = os.environ.get('BOT_TOKEN') # export BOT_TOKEN='your_bot_token_from_@botfather'
from_chat = int(os.environ.get('FROM_CHAT')) # chat_id, which chat to copy
to_chat = int(os.environ.get('TO_CHAT')) # chat_id, copy to which chat
user_id = int(os.environ.get('USER_ID'))
DELAY_TIME = 3 # after each copy delay 3s

whitelist = [] # user_id, who can use the bot
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
    Bot功能未完善，错误处理羸弱，请谨慎使用
    /start:  欢迎命令
    /last:  上一条copy命令的截止id
    /copy:  开始复制，请随指示操作
    /stop:  停止copy，由于未开启异步，意义不大
    '''
    logging.info(f'user {message.chat.id} use /start ...')
    bot.reply_to(message, text, parse_mode="Markdown")

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
    stop_task_flag = False
    bot.send_message(message.chat.id, "Copying ...", parse_mode="Markdown")
    for sign in range(start_id, end_id + 1):
        if stop_task_flag:         
            break
        
        bot.copy_message(chat_id=to_chat, from_chat_id=from_chat, message_id=sign)
        text = f'目前已经复制完第{sign}条'
        print(text)
        logging.info(text)
        time.sleep(DELAY_TIME)

    global record
    record = sign
    # unbound warning for sign here
    if stop_task_flag:
        text = f'任务已结束\n应复制 {end_id - start_id + 1 } 条消息\n实际复制 {sign - start_id} 条消息'
    else:
        text = f'任务已结束\n应复制 {end_id - start_id + 1 } 条消息\n实际复制 {sign - start_id + 1} 条消息'
    print(text)
    logging.info(text)


    bot.send_message(message.chat.id, text, parse_mode="Markdown")
    bot.clear_step_handler(message)


bot.infinity_polling()
