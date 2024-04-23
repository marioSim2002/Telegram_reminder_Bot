import asyncio
import os
import time
from datetime import datetime, timedelta

from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)


class ReminderBot:
    def __init__(self, token):
        self.TOKEN = token
        self.user_reminders = {}
        self.BOT_USERNAME = 'MemoMateBot'

        self.app = Application.builder().token(self.TOKEN).build()
        self.app.add_handler(CommandHandler('start', self.start_cmd))
        self.app.add_handler(CommandHandler('about', self.help_cmd))
        self.app.add_handler(CommandHandler('reminder', self.reminder_cmd))
        self.app.add_handler(MessageHandler(filters.TEXT, self.handle_message))
        self.app.add_error_handler(self.error)

    async def start_cmd(self, update: Update, contexts: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Thanks for using me! I'm glad to remind you to do your tasks.")
        time.sleep(1.4)
        await update.message.reply_text(
            "💬 To set a reminder, use the /reminder command followed by your task and timing\n========\n💬 For example: "
            "/reminder Buy groceries tomorrow/today at 10:00 AM/PM")
        time.sleep(1.2)
        await update.message.reply_text(
            f'💬 DONT use 24HR format*\n''💬 The reminder will be sent at the exact scheduled time.\n*')
        time.sleep(1.2)
        await update.message.reply_text('here ,copy this and modify it as you need!')
        time.sleep(1)
        await update.message.reply_text('/reminder wake john today at 5:00 PM')
        time.sleep(1.2)
        await update.message.reply_text(
            f'🛑 !this bot was developed by MARIO SIMAAN , copyrights preserved.*\nlinkedIn: '
            f'https://www.linkedin.com/in/mario-simaan-6a0928167/')

    async def help_cmd(self, update: Update, contexts: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        await update.message.reply_text(
            "💬 To set a reminder, use the /reminder command followed by your task and timing\n========\nFor example: "
            "/reminder Buy "
            "groceries tomorrow/today at 10:00 AM/PM")
        time.sleep(1.3)
        await update.message.reply_text(
            f'💬 DONT use 24HR format*\n''-*The reminder will be sent at the exact scheduled time.*')
        await update.message.reply_text(f'💬Here, you can copy the following and modify it as you need : ')
        time.sleep(1)
        await update.message.reply_text('/reminder pick up lisa today at 11 AM')

    def handle_response(self, text: str) -> str:
        txt_lower = text.lower()
        if 'hi' in txt_lower:
            return 'Hello! I am glad to chat!'
        if 'thanks' in txt_lower:
            return 'Glad to help!'

        return "Thank you for using this bot."

    async def handle_message(self, update: Update, contexts: ContextTypes.DEFAULT_TYPE):
        message_type = update.message.chat.type
        text = update.message.text
        print(f'User ({update.message.chat.id}) in {message_type}: "{text}"')

        if message_type in ['private', 'group']:
            response = self.handle_response(text)
            print('Bot:', response)
            await update.message.reply_text(response)

    async def schedule_reminders(self, chat_id):
        reminders = self.user_reminders.get(chat_id, [])
        for task, timing in reminders:
            await self.schedule_reminder(chat_id, task, timing)

    async def reminder_cmd(self, update: Update, contexts: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        args = contexts.args

        if len(args) < 2:
            await update.message.reply_text(
                "Please provide both the task and timing for the reminder\n=======\nFor example: /reminder Buy groceries "
                "tomorrow "
                "at 10:00 AM\nDON'T use 24HR format")
            return

        task = ' '.join(args[:len(args) - 1])
        timing = ' '.join(args[1:])

        if chat_id not in self.user_reminders:
            self.user_reminders[chat_id] = []

        self.user_reminders[chat_id].append((task, timing))
        await self.schedule_reminders(chat_id)

    async def schedule_reminder(self, chat_id, task, timing):
        reminder_time = self.parse_timing(timing)
        await Bot(token=self.TOKEN).send_message(chat_id=chat_id, text=f"✅ Reminder set to {task}!")
        if reminder_time is None:
            return

        delay = (reminder_time - datetime.now()).total_seconds()
        print(f"Delay until reminder: {delay} seconds")

        await asyncio.sleep(delay)
        await self.send_reminder(chat_id, task)
        self.user_reminders[chat_id].remove((task, timing))

    async def send_reminder(self, chat_id, task):
        bot = Bot(token=self.TOKEN)
        new_task = self.clear_task_result(task)
        await bot.send_message(chat_id=chat_id, text=f"🔶 REMINDER: Don't forget to {new_task}!")

    def parse_timing(self, timing):
        now = datetime.now()

        if "today" in timing.lower():
            pass
        elif "tomorrow" in timing.lower():
            now += timedelta(days=1)
        else:
            return None

        if "at" in timing:
            try:
                time_str = timing.split("at")[1].strip()
            except IndexError:
                return None
        else:
            return None

        try:
            time_format = "%I:%M %p"
            parsed_time = datetime.strptime(time_str, time_format).time()
        except ValueError:
            return None

        parsed_datetime = datetime.combine(now.date(), parsed_time)
        return parsed_datetime

    async def error(self, update: Update, contexts: ContextTypes.DEFAULT_TYPE):
        print(f'{update} cases an error: {contexts.error}')

    def clear_task_result(self, task):
        if 'at' in task:
            return task.split('at')[0].strip()
        else:
            return task

    def run(self):
        print("...RUNNING...")
        self.app.run_polling(poll_interval=3)

    def get_token(self):
        return self.TOKEN


if __name__ == '__main__':
    TOKEN = open('C:\\Users\\wajds\\OneDrive\\Documents\\TK.txt', 'r').readline()
    bot = ReminderBot(TOKEN)
    bot.run()
