import os
import time
import telebot

BOT_TOKEN = os.environ.get('BOT_TOKEN') # export BOT_TOKEN='your_bot_token_from_@botfather'
FROM_CHAT = 0 # chat_id, which chat to copy
TO_CHAT = 0 # chat_id, copy to which chat
DELAY_TIME = 2 # after each copy delay 2s

whitelist = [] # user_id, who can use the bot
stop_task_flag = False

bot = telebot.TeleBot(BOT_TOKEN)

# Avoid abused
@bot.message_handler(func=lambda message: message.from_user.id not in whitelist)
def not_in_whitelist(message):
    bot.send_message(message.chat.id, "抱歉，你没有权限使用该机器人。")

@bot.message_handler(commands=['start'])
def start_info(message):
    text = '''Hi
    Bot功能未完善，错误处理羸弱，请谨慎使用
    /start:  欢迎命令
    /copy:  开始复制，请随指示操作
    /stop:  停止copy，由于未开启异步，意义不大
    '''
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['stop'])
def stop_task(message):
    global stop_task_flag
    stop_task_flag = True
    bot.reply_to(message, "Task stopped.")

# main function
@bot.message_handler(commands=['copy'])
def copy_handler(message):
    text = "请输入起始、结束消息id，用空格分开：\n(此部分暂未编写任何错误处理，请谨慎设置id)"
    send_msg = bot.send_message(
        message.chat.id, text, parse_mode="Markdown")
    print(message.chat.id)
    bot.register_next_step_handler(send_msg, file_handler)

def file_handler(message):
    start_id, end_id = map(int, message.text.split())
    global stop_task_flag
    stop_task_flag = False
    bot.send_message(message.chat.id, "Copying ...", parse_mode="Markdown")
    for sign in range(start_id, end_id + 1):
        if stop_task_flag:
            text = f'目前已经复制完第{sign-1}条'
            print(text)
            bot.send_message(
                message.chat.id, text, parse_mode="Markdown")
            
            break
        
        bot.copy_message(chat_id=TO_CHAT, from_chat_id=FROM_CHAT, message_id=sign)
        text = f'目前已经复制完第{sign}条'
        print(text)
        time.sleep(DELAY_TIME)

    if stop_task_flag:
        text = f'任务已结束\n应复制 {end_id - start_id + 1 } 条消息\n实际复制 {sign - start_id} 条消息'
    else:
        text = f'任务已结束\n应复制 {end_id - start_id + 1 } 条消息\n实际复制 {sign - start_id + 1} 条消息'
    print(text)


    bot.send_message(message.chat.id, text, parse_mode="Markdown")
    bot.clear_step_handler(message)


bot.infinity_polling()
