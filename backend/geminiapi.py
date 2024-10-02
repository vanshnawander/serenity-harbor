import google.generativeai as genai
import os
from dotenv import load_dotenv
from dbutils import get_db_connection, get_user_details  # Import your database connection function
import pymongo
import datetime  

load_dotenv()
client = genai.GenerativeModel(model_name="gemini-1.5-flash")


def initGoogleI(username,initial_prompts):
    try:
        db = get_db_connection()

        user_details = get_user_details(username).json['user_details']
        user_sex = user_details['sex']
        user_age = user_details['age']
        user_nationality = user_details['nationality']
        
        SYSTEM_PROMPT = f'''
        You are a mental health Counsellor. Your mission is to provide compassionate support and guidance to individuals seeking assistance. Your current conversation partner is {username}, who has reached out to you for help. You'll be conversing with an AI assistant designed to offer helpful, creative, and friendly support throughout your session. Approach each interaction with empathy and understanding, tailoring your responses to meet {username}'s unique needs. If the conversation switches to another language, adapt accordingly. For context, {username} is {user_age} years old, {user_sex}, and their nationality is {user_nationality}. Your role is pivotal in creating a safe and supportive space for {username} to explore their thoughts and feelings openly. If at any point the conversation gets sensitive, refrain from answering.
        '''
        chat_id = db.chat_sessions.count_documents({'username': username})
        db.chat_sessions.insert_one({
            'username': username,
            'active': True,
            'chat_history': [
                {'role':'user','parts':SYSTEM_PROMPT},
                {'role': 'model', 'parts': "Welcome to Serenity Harbor. How can I support you today?"},
                {'role': 'user', 'parts': initial_prompts[0]},
            ],
            'id': chat_id+1
        })

    except Exception as e:
        print(e)

async def fetch_gemini_response(user_prompt: str, username: str,initial_prompts: list = []):
    try:
        db = get_db_connection()
        chat_session = db.chat_sessions.find_one({'username': username, 'active': True})
        if not chat_session:
            initGoogleI(username,initial_prompts)
            chat_session = db.chat_sessions.find_one({'username': username, 'active': True})
        
        chat_history = chat_session['chat_history']
        # print(chat_history)
        chat = client.start_chat(
            history=chat_history
        )
        new_message = {
            "role": "user",
            "parts": user_prompt,
        }
        # print(chat_history)
        chat_history.append(new_message)
        reply = chat.send_message(user_prompt).text

        assistant_response = {
            "role": "model",
            "parts": reply,
        }
        chat_history.append(assistant_response)
        db.chat_sessions.update_one({'username': username, 'active': True}, {'$set': {'chat_history': chat_history}})
        return reply

    except Exception as e:
        print(e)