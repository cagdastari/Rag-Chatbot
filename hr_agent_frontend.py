import streamlit as st
from hr_agent_backend import responser
# from streamlit_star_rating import st_star_rating
# import keyboard
# import psutil
# from get_ip import get_remote_ip
import time
# from ldap3 import Server, Connection, ALL
# import sys
import os
import sqlite3
# import datetime
import requests
import uuid
from openai import OpenAI






st.set_page_config(
    page_title='Şans',
    page_icon=':cat:',
    initial_sidebar_state="collapsed"
    )

def connectDb():
    con = sqlite3.connect("comment.db",check_same_thread=False)
    cursor = con.cursor()
    res = cursor.execute("SELECT name FROM sqlite_master")
    if res.fetchone() is None:
        cursor.execute("CREATE TABLE comments(name,star,comment)")
    return cursor,con

def exit():
    data = [(st.session_state.username,st.session_state.user_rating,st.session_state.user_comment)]
    st.session_state.cursor.executemany("INSERT INTO comments VALUES(?,?,?)",data)
    st.session_state.con.commit()
    res = st.session_state.cursor.execute("SELECT * from comments")
    print(res.fetchall())
    st.session_state.con.close()

    # keyboard.press_and_release('ctrl+w')
    st.stop()
    os.exit(0)
    #sys.exit(0)

# if ("con" not in st.session_state) or ("cursor" not in st.session_state):
#     st.session_state.cursor, st.session_state.con = connectDb()
    

if "authenticator" not in st.session_state:
    st.session_state.authenticator = True

if "stay" not in st.session_state:
    st.session_state.stay = True

if "username" not in st.session_state:
    st.session_state.username = ''

# if "api_endpoint" not in st.session_state:
#     st.session_state.api_endpoint = "http://127.0.0.1:8000/ask_question/"

if "user_rating" not in st.session_state:
    st.session_state.user_rating = ''

if "user_comment" not in st.session_state:
    st.session_state.user_comment = ''




# def user_check(username,password):
#     LDAP_SERVER = "ldap.axa.com.tr"
    
#     ldap_server = Server(LDAP_SERVER,use_ssl=False, get_info=ALL)
#     conn = Connection(ldap_server, username +'@axa.com.tr',
#                                     password, auto_bind=False, raise_exceptions=False)
#     conn.bind()
    
#     if conn.result['result'] == 0:
#         return True
#     else:
#         return False

def user_check(username,password):
    if username == 'ctari' and password == '123':
        return True
    else:
        return False

if not st.session_state.authenticator:
    st.session_state.username = st.text_input("Username",key='user_name')
    password = st.text_input("Password",type='password',key='password')
    login_button = st.button('Login',key='login')

    if login_button:
        st.session_state.authenticator =  user_check(username=st.session_state.username,password=password)

        if st.session_state.authenticator:
            st.success('Giriş başarılı')
            time.sleep(1)
            st.experimental_rerun()
        else:
            st.error('Yanlış kullanıcı adı ya da şifre')
            st.stop()
        

if st.session_state.authenticator :
    if st.session_state.stay:

        if "messages" not in st.session_state:
            st.session_state.messages = []

        if "count" not in st.session_state:
            st.session_state["count"] = 0
        
        if "thread" not in st.session_state:
            st.session_state.thread = OpenAI().beta.threads.create()

        if "response" not in st.session_state:
            st.session_state["response"] = responser()
        


        def process_input(user_input): 
            response = st.session_state["response"].get_response(user_input,st.session_state.thread)
            return response
        
        # def process_input(user_input): 
        #     #response = st.session_state["response"].get_response(user_input)
        #     data = {'input':user_input}
        #     response = requests.post(url=st.session_state.api_endpoint, json=data, headers={"Content-Type": "application/json"})

        #     return response.text.strip('"')

        
        # col1, col2 = st.columns(2,gap="small")
        # col1.header("ŞANS")
        # col2.image('cute_cat.png',use_column_width=True)
        st.header("ŞANS :cat:")
        st.markdown("Merhaba ben Şans, Bana aklına takılan her şeyi sorabilirsin. Sana nasıl yardımcı olabilirim?")

        def messages(user_input):
            with st.chat_message("user"): 
                st.markdown(user_input)
                st.session_state.messages.append({"role": "user", "content": user_input})
            
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                # full_response = ""
                # with st.spinner("Lütfen bekleyiniz..."):
                assistant_response = process_input(user_input)
                # f=open('log.txt','a',encoding='utf-8')
                # f.writelines(f"time:{datetime.datetime.now()}-prompt:{user_input}-answer:{assistant_response}\n")
                # f.close()
                message_placeholder.markdown(assistant_response)

            # if function_name == 'exit_tool':
            #     st.session_state.stay = False
            #     st.experimental_rerun()
            # else:
            #     pass
                # for text in assistant_response.response_gen:
                # # for chunk in assistant_response.split():
                #     full_response += text + " "
                #     time.sleep(0.05)
                #     # Add a blinking cursor to simulate typing
                #     message_placeholder.markdown(full_response + "▌")
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": assistant_response})



        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        user_input = st.chat_input("Type your message and press Enter to send.")

        if user_input:
            messages(user_input)
    
    else:
        # st.session_state.user_rating = st_star_rating(label = "Deneyiminizi puanlayın", maxValue = 5,defaultValue=0, key = "rating",dark_theme=True)
        st.session_state.user_comment = st.text_input(label ='Deneyiminizi yorumlayın',label_visibility='hidden',placeholder='Görüşleriniz bizim için önemli')
        exit_button = st.button('Gönder',on_click=exit)
