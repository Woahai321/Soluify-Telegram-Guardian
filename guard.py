import logging
import json
from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Start command handler
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Hi! I am your group guardian bot!')

# Help command handler
def help_command(update: Update, context: CallbackContext) -> None:
    help_text = (
        'Commands:\n'
        '/start - Start the bot\n'
        '/help - Show this help message\n'
        '/setwelcome <message> - Set welcome message\n'
        '/setgoodbye <message> - Set goodbye message\n'
        '/setschedule <message> - Set scheduled message\n'
        '/setinterval <seconds> - Set schedule interval\n'
        '/addbadword <word> - Add a bad word to the filter\n'
        '/removebadword <word> - Remove a bad word from the filter\n'
    )
    update.message.reply_text(help_text)

# Delete messages with bad words
def delete_bad_words(update: Update, context: CallbackContext) -> None:
    message_text = update.message.text.lower()
    logger.info(f"Received message: {message_text}")
    if any(word in message_text for word in config['BAD_WORDS']):
        logger.info(f"Bad word detected in message: {message_text}")
        update.message.delete()

# Welcome new members
def welcome(update: Update, context: CallbackContext) -> None:
    for member in update.message.new_chat_members:
        update.message.reply_text(config['WELCOME_MESSAGE'].format(name=member.full_name))

# Goodbye to leaving members
def goodbye(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(config['GOODBYE_MESSAGE'].format(name=update.message.left_chat_member.full_name))

# Scheduled message
def scheduled_message(context: CallbackContext) -> None:
    context.bot.send_message(chat_id=config['CHAT_ID'], text=config['SCHEDULED_MESSAGE'], parse_mode=ParseMode.HTML)

# Set welcome message
def set_welcome(update: Update, context: CallbackContext) -> None:
    config['WELCOME_MESSAGE'] = ' '.join(context.args)
    update.message.reply_text('Welcome message updated!')

# Set goodbye message
def set_goodbye(update: Update, context: CallbackContext) -> None:
    config['GOODBYE_MESSAGE'] = ' '.join(context.args)
    update.message.reply_text('Goodbye message updated!')

# Set scheduled message
def set_schedule(update: Update, context: CallbackContext) -> None:
    config['SCHEDULED_MESSAGE'] = ' '.join(context.args)
    update.message.reply_text('Scheduled message updated!')

# Set schedule interval
def set_interval(update: Update, context: CallbackContext) -> None:
    try:
        config['SCHEDULE_INTERVAL'] = int(context.args[0])
        update.message.reply_text('Schedule interval updated!')
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /setinterval <seconds>')

# Add bad word
def add_bad_word(update: Update, context: CallbackContext) -> None:
    word = ' '.join(context.args).lower()
    if word not in config['BAD_WORDS']:
        config['BAD_WORDS'].append(word)
        update.message.reply_text(f'Added "{word}" to bad words list.')
    else:
        update.message.reply_text(f'"{word}" is already in the bad words list.')

# Remove bad word
def remove_bad_word(update: Update, context: CallbackContext) -> None:
    word = ' '.join(context.args).lower()
    if word in config['BAD_WORDS']:
        config['BAD_WORDS'].remove(word)
        update.message.reply_text(f'Removed "{word}" from bad words list.')
    else:
        update.message.reply_text(f'"{word}" is not in the bad words list.')

def main() -> None:
    # Create the Updater and pass it your bot's token
    updater = Updater(config['TOKEN'])

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("setwelcome", set_welcome))
    dispatcher.add_handler(CommandHandler("setgoodbye", set_goodbye))
    dispatcher.add_handler(CommandHandler("setschedule", set_schedule))
    dispatcher.add_handler(CommandHandler("setinterval", set_interval))
    dispatcher.add_handler(CommandHandler("addbadword", add_bad_word))
    dispatcher.add_handler(CommandHandler("removebadword", remove_bad_word))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, delete_bad_words))
    dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, welcome))
    dispatcher.add_handler(MessageHandler(Filters.status_update.left_chat_member, goodbye))

    # Set up job queue for scheduled messages
    job_queue = updater.job_queue
    job_queue.run_repeating(scheduled_message, interval=config['SCHEDULE_INTERVAL'], first=0)  # every interval

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT
    updater.idle()

if __name__ == '__main__':
    main()