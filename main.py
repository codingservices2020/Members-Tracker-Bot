import logging
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
    CallbackQueryHandler,
)
# from dotenv import load_dotenv
# load_dotenv()

# Fetch bot token and allowed group ID from environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
ALLOWED_GROUP_ID = int(os.getenv('ALLOWED_GROUP_ID', 0))  # Default to 0 if not set

# Validate environment variables
if not BOT_TOKEN:
    raise EnvironmentError("BOT_TOKEN environment variable not set!")
if ALLOWED_GROUP_ID == 0:
    raise EnvironmentError("ALLOWED_GROUP_ID environment variable not set or invalid!")

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# This dictionary will store the count of added members for each user
user_add_count = {}

# The number of members needed to trigger the reward
member_need_to_add = 5


# Function to create an inline button for checking member count
async def create_check_count_button(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = user.id
    username = user.username or user.first_name or "Anonymous"

    # Create the inline button to check how many members the user has added
    keyboard = [
        [InlineKeyboardButton("How many members have I added?", callback_data="check_count")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send the welcome message with the button
    await update.message.reply_text(
        f"<b>🔰WELCOME🔰</b>\n"
        f"Hello @{username}, welcome to the group! 🎉\n"
        f"Here, every time you add {member_need_to_add} members to this group, you will receive a free plagiarism "
        f"report. So, what are you waiting for? Start now!\n\n"
        f"<b>✅NOTE:</b> To check how many members you have added, press the button below or type /count command in the group.",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )


# Function to handle callback queries when the user presses the "How many members have I added?" button
async def handle_check_count_callback(update: Update, context: CallbackContext):
    user = update.callback_query.from_user
    user_id = user.id
    username = user.username or user.first_name or "Anonymous"

    # Check how many members the user has added
    if user_id in user_add_count:
        total_count = user_add_count[user_id]
        added_count = total_count % member_need_to_add
        remaining = member_need_to_add - added_count

        # Send the user's progress in a pop-up message
        await update.callback_query.answer(f"You have added {added_count} members.\nYou need to add {remaining} more members for a free plagiarism report!")
    else:
        await update.callback_query.answer("You haven't added any members yet.")


# Function to create an inline button for sending the article
async def create_send_article_button(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = user.id
    username = user.username or user.first_name or "Anonymous"

    keyboard = [
        [InlineKeyboardButton("Send your article here", url="https://t.me/FreePlagiarismReport_bot")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send the message with the button
    message = await update.message.reply_text(
        f"<b>🔰Added Successfully🔰</b>\n"
        f"Congratulations @{username}! 🎉 You have added {member_need_to_add} members.\n"
        f"Now, you can send your file to our bot for free plagiarism report.",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

    # Set up a job to delete the message after 5 minutes
    await context.job_queue.run_once(delete_message, 10, context=(message.chat.id, message.message_id))


# Function to delete the message after 5 minutes
async def delete_message(context: CallbackContext):
    chat_id, message_id = context.job.context
    await context.bot.delete_message(chat_id=chat_id, message_id=message_id)


# Modify the track_new_member function to include the new button
async def track_new_member(update: Update, context: CallbackContext):
    if update.message.chat.id != ALLOWED_GROUP_ID:
        return  # Ignore updates from other groups

    user = update.message.from_user
    user_id = user.id
    username = user.username or user.first_name or "Anonymous"

    # Check if there are new members
    if update.message.new_chat_members:
        for new_member in update.message.new_chat_members:
            # If the new member is the same as the one who triggered the event, it's a self-join
            if new_member.id == user_id:
                # Send a welcome message to the newly joined member
                await create_check_count_button(update, context)
                continue

            # Increment the count for the user who added new members
            if user_id not in user_add_count:
                user_add_count[user_id] = 0
            user_add_count[user_id] += 1

        # Notify the user of their progress if they added members
        if user_id in user_add_count and user_id != update.message.new_chat_members[0].id:
            count_member = user_add_count[user_id] % member_need_to_add
            if count_member == 0 and user_add_count[user_id] > 0:
                await create_send_article_button(update, context)


# Function to handle the /count command
async def count_added_members(update: Update, context: CallbackContext):
    if update.message.chat.id != ALLOWED_GROUP_ID:
        return  # Ignore updates from other groups

    user = update.message.from_user
    user_id = user.id
    username = user.username or user.first_name or "Anonymous"

    # Check if the user has added any members
    if user_id in user_add_count:
        total_count = user_add_count[user_id]
        added_count = total_count % member_need_to_add
        remaining = member_need_to_add - added_count
        if added_count == 0:
            await create_send_article_button(update, context)  # Create the button only when the user reaches the required count
        else:
            await update.message.reply_text(
                f"<b>‼️Add More‼️</b>\n"
                f"Hi @{username}, you have added {added_count} members.\n"
                f"You need to add {remaining} more members for free plagiarism report!"
            )
    else:
        await update.message.reply_text(
            f"Hi @{username}, you haven't added any members yet!"
        )


# Main function to set up the bot
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, track_new_member))
    application.add_handler(CommandHandler('count', count_added_members))
    application.add_handler(CallbackQueryHandler(handle_check_count_callback, pattern="check_count"))

    # Start the bot
    application.run_polling()


if __name__ == '__main__':
    main()
