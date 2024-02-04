import os, json
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
import guardrails as gd
from guardrails.validators import OnTopic
from guardrails.errors import ValidatorError
from transformers import logging
logging.set_verbosity_error()

client = OpenAI()

chat_history = []
summary_chat_history = []

def initOpenAI(username):
    from dbutils import get_user_details
    user_details = get_user_details(username)
    user_sex = user_details.json['user_details']['sex']
    user_age = user_details.json['user_details']['age']
    user_nationality = user_details.json['user_details']['nationality']
    SYSTEM_PROMPT = f'''
    You are a mental health Counsellor.Your mission is to provide compassionate support and guidance to individuals seeking assistance. Your current conversation partner is {username}, who has reached out to you for help. You'll be conversing with an AI assistant designed to offer helpful, creative, and friendly support throughout your session. Approach each interaction with empathy and understanding, tailoring your responses to meet {username}'s unique needs. If the conversation switches to another language, adapt accordingly. For context, {username} is {user_age} years old, {user_sex}, and their nationality is {user_nationality}. Your role is pivotal in creating a safe and supportive space for {username} to explore their thoughts and feelings openly. If at any point the conversation gets sensitive, refrain from answering.
    '''
    chat_history.append({"role": "system", "content": SYSTEM_PROMPT})

finetuned_model = os.getenv("FT_MODEL")

# def validate_user_prompt(user_prompt: str):
#     invalid_topics = ["suicide"]
#     valid_topics=[" "]
#     try:
#         guard = gd.Guard.from_string(
#     validators=[
#         OnTopic(
#             valid_topics=valid_topics,
#             invalid_topics=invalid_topics,
#             disable_classifier=False,
#             disable_llm=True,
#             on_fail="reask",
#         )
#     ]
# )
#         a=guard.parse(llm_output=user_prompt,)
#         if(a.validated_output==None):
#             return False
#         else:
#             return True
        
#     except ValidatorError as e:
#         return False



async def fetch_openai_response(user_prompt: str, username: str):
    try:
        # if(validate_user_prompt(user_prompt)==False):
        #     chat_history.append({"role": "user", "content": user_prompt})
        #     reply = "I'm sorry, please contact these numbers to get further assistance XXXXXXXXX"
        #     chat_history.append({"role": "assistant", "content": reply})
        #     return reply

        if len(chat_history) == 0:
            initOpenAI(username)
        chat_history.append({"role": "user", "content": user_prompt})
        openai_response = client.chat.completions.create(
            model=finetuned_model,
            messages=chat_history
        )
        reply = openai_response.choices[0].message.content
        chat_history.append({"role": "assistant", "content": reply})
        return reply

    except Exception as e:
        print(e)


def initOpenAI_admin(username):
    SYSTEM_PROMPT = f'''
        You are a chat summarizer who summarizes the chat between a mental health bot and {username}, the summary is intended to be read by a real therapist looking over {username}. Make the summary one paragraph describing the chat, and include major points of what happened during the conversation. Be concise and not verbose. Don't provide an opinion when summarizing. Use {username} instead of "user".
    '''
    summary_chat_history.append({"role": "system", "content": SYSTEM_PROMPT})

def format_messages(messages, username):
    formatted_string = ""

    for message in messages:
        role = message["role"]
        content = message["content"]

        if role == "user":
            formatted_string += f"{username}: {content}\n"
        elif role == "assistant":
            formatted_string += f"assistant: {content}\n"

    return formatted_string.strip()

def fetch_openai_response_admin(username, messages):
    try:
        initOpenAI_admin(username)

        summary_chat_history.append({"role": "user", "content": format_messages(messages, username)})
        openai_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=summary_chat_history
        )
        reply = openai_response.choices[0].message.content
        summary_chat_history.clear()
        return reply

    except Exception as e:
        print(e)

from pathlib import Path
def text_to_speech(text, speech_file_path):
    response = client.audio.speech.create(
    model="tts-1",
    voice="nova",
    input=text,
    )
    response.stream_to_file(speech_file_path)
