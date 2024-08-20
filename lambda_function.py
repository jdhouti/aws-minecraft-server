from telegram import Update, Bot
from telegram.ext import Dispatcher, CommandHandler, CallbackContext
from minecraft_aws_client import MinecraftAwsClient, ServerStatus
import json
import boto3

TELEGRAM_SECRET_NAME = "prod/telegram/bot_token"
TELEGRAM_SECRET_USERS = "prod/telegram/users"

minecraft_aws_client = MinecraftAwsClient()

INSTANCE_ID = 'i-0a70e43874886f1fe'

telegram_bot_token = minecraft_aws_client.get_secret(TELEGRAM_SECRET_NAME)['TELEGRAM_BOT_TOKEN']
bot = Bot(token=telegram_bot_token)


#LOOK INTO WHAT THE PARAMS OF THESE FUNCTIONS DO!
def start_instance(update: Update, context: CallbackContext) -> None:
    if update.message.chat.username.lower() in get_admins():
        begin_state, end_state = minecraft_aws_client.start_server()

        if begin_state == ServerStatus.RUNNING:
            update.message.reply_text("Did nothing, server is already on")
        else:
            update.message.reply_text("Starting server")
    else:
        update.message.reply_text("Unauthorized command")

def stop_instance(update: Update, context: CallbackContext) -> None:
    if update.message.chat.username.lower() in get_admins():
        begin_state, end_state = minecraft_aws_client.stop_server()

        if begin_state == end_state:
            update.message.reply_text("Did nothing, server already stopped")
        else:
            update.message.reply_text("Stopped server")
    else:
        update.message.reply_text("Unauthorized command")


def info(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("The server host is:\n34.234.0.133:25565")
    

def status(update: Update, context: CallbackContext) -> None:
    if minecraft_aws_client.minecraft_server_is_running():
        update.message.reply_text("Running! Connect to the server\n34.234.0.133:25565\nIf u just turned the server on, give it a few mins")
    else:
        update.message.reply_text("It's off")

def help(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('''/start_server: Starts the server
/stop_server: stops the server
/info: gives the server host ip
/status: gives the status of the server
                              
remember: give it a few mins to start the mc server as it needs to start the server then the mc world.''')
    
def add_user(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("NOT SET UP YET!")


def get_users_list(list_name):
    users_raw = minecraft_aws_client.get_secret(TELEGRAM_SECRET_USERS)[list_name]
    users = users_raw.split(",")

    return set(users)

def get_admins():
    return get_users_list("admins")


def get_allowed_users():
    return get_users_list("allowed-users")


def lambda_handler(event, context):
    dispatcher = Dispatcher(bot, None, workers=0, use_context=True)

    dispatcher.add_handler(CommandHandler("start_server", start_instance))
    dispatcher.add_handler(CommandHandler("stop_server", stop_instance))
    dispatcher.add_handler(CommandHandler("status", status))
    dispatcher.add_handler(CommandHandler("info", info))
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(CommandHandler("start", help))
    dispatcher.add_handler(CommandHandler("add_user", add_user))


    # Process the incoming update
    update = Update.de_json(json.loads(event['body']), bot)

    chat_id = update.message.chat_id
    username = update.message.chat.username


    dispatcher.process_update(update)

    return {
        'statusCode': 200,
        'body': json.dumps('OK')
    }
