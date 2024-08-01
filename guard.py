import logging
import json
from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Load config
def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("Config file not found, loading defaults.")
        return {
            'TOKEN': '',
            'CHAT_ID': '',
            'WELCOME_MESSAGE': 'Welcome, {name}!',
            'GOODBYE_MESSAGE': 'Goodbye, {name}!',
            'SCHEDULED_MESSAGE': 'This is a scheduled message.',
            'SCHEDULE_INTERVAL': 3600,  # Default to 1 hour
            'BAD_WORDS': [],
            'AUTO_REPLY_ENABLED': False,
            'AUTO_REPLY_TRIGGER': '',
            'AUTO_REPLY_RESPONSE': ''
        }

# Save config
def save_config(config):
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)

config = load_config()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Start command handler
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        'Hi! I am your group guardian bot! 🤖',
        parse_mode=ParseMode.MARKDOWN
    )

# Help command handler
def help_command(update: Update, context: CallbackContext) -> None:
    help_text = (
        '📜 *Commands:*\n'
        '/start - Start the bot\n'
        '/help - Show this help message\n'
        '/setwelcome <message> - Set welcome message\n'
        '/setgoodbye <message> - Set goodbye message\n'
        '/setschedule <message> - Set scheduled message\n'
        '/setinterval <minutes> - Set schedule interval\n'
        '/addbadword <word> - Add a bad word to the filter\n'
        '/removebadword <word> - Remove a bad word from the filter\n'
        '/autoreplyon - Turn auto-reply on\n'
        '/autoreplyoff - Turn auto-reply off\n'
        '/setautoreply <trigger> <response> - Set auto-reply trigger and response\n'
    )
    update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

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
    save_config(config)
    update.message.reply_text(
        'Welcome message updated! 🎉',
        parse_mode=ParseMode.MARKDOWN
    )

# Set goodbye message
def set_goodbye(update: Update, context: CallbackContext) -> None:
    config['GOODBYE_MESSAGE'] = ' '.join(context.args)
    save_config(config)
    update.message.reply_text(
        'Goodbye message updated! 👋',
        parse_mode=ParseMode.MARKDOWN
    )

# Set scheduled message
def set_schedule(update: Update, context: CallbackContext) -> None:
    config['SCHEDULED_MESSAGE'] = ' '.join(context.args)
    save_config(config)
    update.message.reply_text(
        'Scheduled message updated! 🗓️',
        parse_mode=ParseMode.MARKDOWN
    )

# Set schedule interval (in minutes)
def set_interval(update: Update, context: CallbackContext) -> None:
    try:
        minutes = int(context.args[0])
        config['SCHEDULE_INTERVAL'] = minutes * 60  # Convert minutes to seconds
        save_config(config)
        update.message.reply_text('Schedule interval updated!')
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /setinterval <minutes>')

# Add bad word
def add_bad_word(update: Update, context: CallbackContext) -> None:
    word = ' '.join(context.args).lower()
    if word not in config['BAD_WORDS']:
        config['BAD_WORDS'].append(word)
        save_config(config)
        update.message.reply_text(
            f'Added "{word}" to bad words list. 🛑',
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        update.message.reply_text(
            f'"{word}" is already in the bad words list. ⚠️',
            parse_mode=ParseMode.MARKDOWN
        )

# Remove bad word
def remove_bad_word(update: Update, context: CallbackContext) -> None:
    word = ' '.join(context.args).lower()
    if word in config['BAD_WORDS']:
        config['BAD_WORDS'].remove(word)
        save_config(config)
        update.message.reply_text(
            f'Removed "{word}" from bad words list. ✅',
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        update.message.reply_text(
            f'"{word}" is not in the bad words list. ❌',
            parse_mode=ParseMode.MARKDOWN
        )

# Auto-reply on
def auto_reply_on(update: Update, context: CallbackContext) -> None:
    config['AUTO_REPLY_ENABLED'] = True
    save_config(config)
    update.message.reply_text('Auto-reply is now enabled.')

# Auto-reply off
def auto_reply_off(update: Update, context: CallbackContext) -> None:
    config['AUTO_REPLY_ENABLED'] = False
    save_config(config)
    update.message.reply_text('Auto-reply is now disabled.')

# Set auto-reply trigger and response
def set_auto_reply(update: Update, context: CallbackContext) -> None:
    if len(context.args) < 2:
        update.message.reply_text('Usage: /setautoreply <trigger> <response>')
        return
    trigger = context.args[0].lower()
    response = ' '.join(context.args[1:])
    config['AUTO_REPLY_TRIGGER'] = trigger
    config['AUTO_REPLY_RESPONSE'] = response
    save_config(config)
    update.message.reply_text(f'Auto-reply set for trigger "{trigger}".')

# Auto-reply handler
def auto_reply(update: Update, context: CallbackContext) -> None:
    if not config['AUTO_REPLY_ENABLED']:
        return
    message_text = update.message.text.lower()
    if config['AUTO_REPLY_TRIGGER'] in message_text:
        update.message.reply_text(config['AUTO_REPLY_RESPONSE'])

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
    dispatcher.add_handler(CommandHandler("autoreplyon", auto_reply_on))
    dispatcher.add_handler(CommandHandler("autoreplyoff", auto_reply_off))
    dispatcher.add_handler(CommandHandler("setautoreply", set_auto_reply))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, delete_bad_words))
    dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, welcome))
    dispatcher.add_handler(MessageHandler(Filters.status_update.left_chat_member, goodbye))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, auto_reply))

    # Set up job queue for scheduled messages
    job_queue = updater.job_queue
    job_queue.run_repeating(scheduled_message, interval=config['SCHEDULE_INTERVAL'], first=0)  # every interval

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT
    updater.idle()

if __name__ == '__main__':
    main()
