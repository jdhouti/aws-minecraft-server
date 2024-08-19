import json
import boto3
from telegram import Update, Bot
from telegram.ext import Dispatcher, CommandHandler, CallbackContext

REGION_NAME = "us-east-1"
TELEGRAM_SECRET_NAME = "prod/telegram/bot_token"
TELEGRAM_SECRET_USERS = "prod/telegram/users"
session = boto3.session.Session()
secrets_client = session.client(
    service_name='secretsmanager',
    region_name=REGION_NAME
)
ec2_client = session.client(
    'ec2',
    region_name=REGION_NAME
)

def get_secret(secret_name):
    try:
        response = secrets_client.get_secret_value(SecretId=secret_name)
        
        # Depending on the secret type, it could be a string or binary
        if 'SecretString' in response:
            secret = response['SecretString']
        else:
            secret = base64.b64decode(response['SecretBinary'])

        # If it's a JSON, parse it
        secret_dict = json.loads(secret)
        return secret_dict

    except Exception as e:
        print(f"Error retrieving secret: {e}")
        return None

INSTANCE_ID = 'i-0a70e43874886f1fe'

telegram_bot_token = get_secret(TELEGRAM_SECRET_NAME)['TELEGRAM_BOT_TOKEN']
bot = Bot(token=telegram_bot_token)


#LOOK INTO WHAT THE PARAMS OF THESE FUNCTIONS DO!
def start_instance(update: Update, context: CallbackContext) -> None:
    if update.message.chat.username.lower() in get_admins():
        ec2_client.start_instances(InstanceIds=[INSTANCE_ID])
        update.message.reply_text("Starting server")
    else:
        update.message.reply_text("Unauthorized to start the server")

def stop_instance(update: Update, context: CallbackContext) -> None:
    if update.message.chat.username.lower() in get_admins():
        ec2_client.stop_instances(InstanceIds=[INSTANCE_ID])
        update.message.reply_text("Stopping server")
    else:
        update.message.reply_text("Unauthorized to stop the server")


def info(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("The server host is:\n34.234.0.133:25565")
    


def status(update: Update, context: CallbackContext) -> None:
    response = ec2_client.describe_instance_status(InstanceIds=[INSTANCE_ID])
    
    # update.message.reply_text(response)

    if len(response['InstanceStatuses']) != 0:
        update.message.reply_text("Running! Connect to the server\n34.234.0.133:25565\nIf u just turned the server on, give it a few mins")
    else:
        update.message.reply_text("It's off")

def help(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('''/start_server: Starts the server
/stop_server: stops the server
/info: gives the server host ipppp
/status: gives the status of the server
                              
remember: give it a few mins to start the mc server as it needs to start the server then the mc world.''')
    
def add_user(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("NOT SET UP YET!")


def get_users_list(list_name):
    users_raw = get_secret(TELEGRAM_SECRET_USERS)[list_name]
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
