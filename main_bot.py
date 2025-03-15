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
        self.user_reminders = {}  # Stores reminders as {chat_id: [(task, timing)]}
        self.active_reminders = {}  # Stores asyncio tasks for active reminders
        self.BOT_USERNAME = 'MemoMateBot'

        self.app = Application.builder().token(self.TOKEN).build()
        self.app.add_handler(CommandHandler('start', self.start_cmd))
        self.app.add_handler(CommandHandler('about', self.help_cmd))
        self.app.add_handler(CommandHandler('reminder', self.reminder_cmd))
        self.app.add_handler(MessageHandler(filters.TEXT, self.handle_message))
        self.app.add_error_handler(self.error)

    async def start_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Welcome message and quick instructions for 24-hour format."""
        await update.message.reply_text("Thanks for using me! I'm glad to remind you to do your tasks.")
        await asyncio.sleep(1.4)
        await update.message.reply_text(
            "💬 To set a reminder, use the /reminder command followed by your task and timing.\n"
            "========\n"
            "💬 For example: /reminder Buy groceries today/tomorrow at 14:00"
        )
        await asyncio.sleep(1.2)
        await update.message.reply_text(
            "💬 Please use 24-hour format (e.g., 13:30, 00:15, 09:00)."
        )
        await asyncio.sleep(1.2)
        await update.message.reply_text("Here, copy this and modify it as you need!")
        await asyncio.sleep(1)
        await update.message.reply_text("/reminder Wake John today at 17:00")
        await asyncio.sleep(1.2)
        await update.message.reply_text(
            "🛑 This bot was developed by MARIO SIMAAN, all rights reserved.\nLinkedIn: "
            "https://www.linkedin.com/in/mario-simaan-6a0928167/"
        )

    async def help_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Displays help and examples (24-hour format)."""
        chat_id = update.message.chat_id
        await update.message.reply_text(
            "💬 To set a reminder, use the /reminder command followed by your task and timing.\n"
            "For example: /reminder Buy groceries tomorrow at 10:00\n\n"
            "💬 Please use 24-hour format (e.g., 13:30, 00:15, 09:00)."
        )
        await asyncio.sleep(1.3)
        await update.message.reply_text(
            "💬 The reminder will be sent at the exact scheduled time."
        )
        await asyncio.sleep(1)
        await update.message.reply_text("💬 Here, you can copy the following and modify it as you need:")
        await asyncio.sleep(1)
        await update.message.reply_text("/reminder pick up Lisa today at 11:00")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generic message handler for text messages."""
        message_type = update.message.chat.type
        text = update.message.text
        print(f'User ({update.message.chat.id}) in {message_type}: "{text}"')

        if message_type in ['private', 'group']:
            response = self.handle_response(text)
            print('Bot:', response)
            await update.message.reply_text(response)

    def handle_response(self, text: str) -> str:
        """Simple text-based responses."""
        txt_lower = text.lower()
        if 'hi' in txt_lower:
            return 'Hello! I am glad to chat!'
        if 'thanks' in txt_lower:
            return 'Glad to help!'
        return "Thank you for using this bot."

    async def reminder_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        The /reminder command. Usage example:
          /reminder Buy groceries tomorrow at 14:00
        """
        chat_id = update.message.chat_id
        args = context.args

        # Basic validation
        if len(args) < 2:
            await update.message.reply_text(
                "Please provide both the task and timing for the reminder.\n"
                "For example: /reminder Buy groceries tomorrow at 14:00\n"
                "Use 24-hour format like 14:00 or 09:30."
            )
            return

        # Split into task and timing
        task = ' '.join(args[:-2])
        timing = ' '.join(args[-2:])

        if chat_id not in self.user_reminders:
            self.user_reminders[chat_id] = []

        self.user_reminders[chat_id].append((task, timing))

        # Schedule the reminder in a separate asyncio task
        task_obj = asyncio.create_task(self.schedule_reminder(chat_id, task, timing))

        # Store the task in active_reminders
        if chat_id not in self.active_reminders:
            self.active_reminders[chat_id] = []
        self.active_reminders[chat_id].append(task_obj)

        await update.message.reply_text(f"✅ Reminder set for: {task} at {timing}!")

    async def schedule_reminder(self, chat_id, task, timing):
        """
        Creates a scheduled reminder based on the parsed time.
        The reminder is run in a separate asyncio task so multiple
        reminders can run concurrently for each user.
        """
        reminder_time = self.parse_timing(timing)

        if reminder_time is None:
            await Bot(token=self.TOKEN).send_message(
                chat_id=chat_id,
                text=(
                    "⚠️ Invalid time format. Please use something like "
                    "'today at 14:00' or 'tomorrow at 08:30'. (24-hour format)"
                )
            )
            return

        # calc how long we wait until sending the reminder
        delay = (reminder_time - datetime.now()).total_seconds()
        print(f"Reminder for {chat_id}: Waiting {delay} seconds.")

        # If the time is in the past even after parsing, shift to next day
        if delay <= 0:
            reminder_time += timedelta(days=1)
            delay = (reminder_time - datetime.now()).total_seconds()
            await Bot(token=self.TOKEN).send_message(
                chat_id=chat_id,
                text=(
                    "⚠️ It looks like the time you set is already in the past today. "
                    "I'll automatically shift this reminder to the next day at the same time."
                )
            )
            print(f"New delay after shifting: {delay} seconds.")

        # Wait until the reminder time
        await asyncio.sleep(delay)
        await self.send_reminder(chat_id, task)

    async def send_reminder(self, chat_id, task):
        """
        Sends the reminder message to the user when time is up.
        Also removes completed tasks from active_reminders.
        """
        bot = Bot(token=self.TOKEN)
        new_task = self.clear_task_result(task)
        await bot.send_message(chat_id=chat_id, text=f"🔶 REMINDER: Don't forget to {new_task}!")

        # Remove the completed task from active reminders
        if chat_id in self.active_reminders:
            self.active_reminders[chat_id] = [t for t in self.active_reminders[chat_id] if not t.done()]

    def parse_timing(self, timing):
        """
        Parses the user's timing string, e.g. "today at 14:00" or "tomorrow at 08:30" (24-hour format).
        Returns a datetime if successful, or None if invalid.
        """
        now = datetime.now()

        day_shift = 0
        timing_lower = timing.lower()
        if "tomorrow" in timing_lower:
            day_shift = 1
        # 'today' is the default if 'tomorrow' not found

        # extract the time part after "at"
        if "at" in timing_lower:
            try:
                time_str = timing_lower.split("at", 1)[1].strip()
            except IndexError:
                return None
        else:
            return None

        parsed_time = None
        time_formats = ["%H:%M", "%H"]

        for fmt in time_formats:
            try:
                parsed_time_obj = datetime.strptime(time_str, fmt).time()
                parsed_time = parsed_time_obj
                break
            except ValueError:
                continue

        if not parsed_time:
            #could not parse any known format
            return None

        #combine the date with the parsed time
        final_date = now.date() + timedelta(days=day_shift)
        parsed_datetime = datetime.combine(final_date, parsed_time)

        return parsed_datetime

    def clear_task_result(self, task):
        """
        Clean up the task text if it has 'at' in it (so the final message isn't awkward).
        E.g., "Buy groceries at" => "Buy groceries"
        """
        if 'at' in task:
            return task.split('at')[0].strip()
        else:
            return task

    async def error(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Logs errors raised by updates."""
        print(f'{update} caused an error: {context.error}')

    def run(self):
        """Starts the bot's event loop."""
        print("...RUNNING...")
        self.app.run_polling(poll_interval=3)


if __name__ == '__main__':
    TOKEN = open('C:\\Users\\wajds\\OneDrive\\Documents\\TK.txt', 'r').readline()
    bot = ReminderBot(TOKEN)
    bot.run()
