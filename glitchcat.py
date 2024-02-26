from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pandas
import pyperclip
import requests
import sys
import os
import time
import threading

def get_input():
    global flag
    user_input = input()
    if user_input == 'q':
        flag = False
    else:
        threading.Thread(target=get_input).start()

def main(my_file):
    global flag
    flag = True
    print('Initialing GlitchCat...') # GlitchCat is a chat bot for chzzk.naver.com

    print('Loading Commands...')
    commands = {}
    commands_file = os.path.join(os.path.dirname(my_file), 'commands.csv')
    if not os.path.exists(commands_file): # If the file does not exist, print an error message and exit the program
        print('Commands file not found. Please create a file named "commands.csv" in the same directory as this script.')
        sys.exit(1)

    commands_data = pandas.read_csv(commands_file)
    for i in range(len(commands_data)):
        commands[commands_data['command'][i]] = commands_data['response'][i]

    moderator = []
    moderator_file = os.path.join(os.path.dirname(my_file), 'moderators.csv')
    if not os.path.exists(moderator_file): # If the file does not exist, print an error message and exit the program
        print('Moderators file not found. Please create a file named "moderators.csv" in the same directory as this script.')
        sys.exit(1)
    
    moderator_data = pandas.read_csv(moderator_file)
    for i in range(len(moderator_data)):
        moderator.append(moderator_data['name'][i])

    print('Loading auth file...') # chzzk_auth.csv
    auth_file = os.path.join(os.path.dirname(my_file), 'chzzk_auth.csv')
    if not os.path.exists(auth_file): # If the file does not exist, print an error message and exit the program
        print('Auth file not found. Please create a file named "chzzk_auth.csv" in the same directory as this script.')
        sys.exit(1)

    auth_data = pandas.read_csv(auth_file, nrows=1)
    if auth_data.empty: # If the file is empty, print an error message and exit the program
        print('Auth file is empty. Please fill in the required fields.')
        sys.exit(1)

    chzzk_uid = auth_data['chzzk_uid'][0]
    bot_id = auth_data['bot_id'][0]
    bot_pw = auth_data['bot_pw'][0]

    print('Loading chat...') # Open the chat page
    dest_ch = 'https://chzzk.naver.com/live/' + chzzk_uid + '/chat'
    naver_login = 'https://nid.naver.com/nidlogin.login'

    driver = webdriver.Chrome()
    driver.get(naver_login)
    time.sleep(2)

    pyperclip.copy(bot_id)
    driver.find_element(By.CSS_SELECTOR, '#id').send_keys(Keys.CONTROL, 'v')
    pyperclip.copy(bot_pw)
    driver.find_element(By.CSS_SELECTOR, '#pw').send_keys(Keys.CONTROL, 'v')
    pyperclip.copy('')
    driver.find_element(By.XPATH,'//*[@id="log.login"]').click()
    time.sleep(1)
    if driver.current_url == naver_login: # If the login fails, print an error message and exit the program
        print('Login failed. Please check your ID and password.')
        sys.exit(1)

    driver.get(dest_ch)

    print('Chat loaded.') # The chat is now loaded
    print('Listening...') # The program is now listening to the chat

    prv_chat = []
    while flag:
        bs = BeautifulSoup(driver.page_source, 'html.parser')
        chat = bs.select('button.live_chatting_message_wrapper__xpYre')
        time.sleep(1)

        if prv_chat == []:
            prv_chat = chat
            continue
        
        if chat != prv_chat: # If there is a new chat, check if it is a command
            for i in range(len(chat) - len(prv_chat), 0, -1): # Check the new chat from the end
                cur_chat = chat[-i]
                cur_user = cur_chat.select('span.live_chatting_username_nickname__dDbbj')[0].text.rstrip(':')
                cur_msg = cur_chat.select('span.live_chatting_message_text__DyleH')[0].text
                cur_command = len(cur_msg.split()) > 0 and cur_msg.split()[0] or ''
                
                if cur_command == "!추가":
                    if cur_user not in moderator:
                        continue
                    
                    if len(cur_msg.split()) < 3:
                        continue
                    new_command = cur_msg.split()[1]
                    new_response = ' '.join(cur_msg.split()[2:])
                    commands[new_command] = new_response
                    commands_data = pandas.DataFrame(commands.items(), columns=['command', 'response'])
                    commands_data.to_csv(commands_file, index=False)
                    print('Command added: ' + new_command + ' -> ' + new_response)

                    chat_input = driver.find_element(By.CSS_SELECTOR, '[placeholder="채팅을 입력해주세요"]')
                    chat_input.click()
                    new_chat_input = driver.find_element(By.CLASS_NAME, 'live_chatting_input_input__2F3Et')
                    new_chat_input.send_keys('명령어가 추가되었습니다: ' + new_command + ' -> ' + new_response)
                    chat_btn = driver.find_element(By.CLASS_NAME, 'live_chatting_input_send_button__8KBrn')
                    chat_btn.click()
                     
                elif cur_command == "!삭제":
                    if cur_user not in moderator:
                        continue

                    if len(cur_msg.split()) < 2:
                        continue
                    del_command = cur_msg.split()[1]
                    if del_command in commands:
                        del commands[del_command]
                        commands_data = pandas.DataFrame(commands.items(), columns=['command', 'response'])
                        commands_data.to_csv(commands_file, index=False)
                        print('Command deleted: ' + del_command)

                        chat_input = driver.find_element(By.CSS_SELECTOR, '[placeholder="채팅을 입력해주세요"]')
                        chat_input.click()
                        new_chat_input = driver.find_element(By.CLASS_NAME, 'live_chatting_input_input__2F3Et')
                        new_chat_input.send_keys('명령어가 삭제되었습니다: ' + del_command)
                        chat_btn = driver.find_element(By.CLASS_NAME, 'live_chatting_input_send_button__8KBrn')
                        chat_btn.click()
                    else:
                        chat_input = driver.find_element(By.CSS_SELECTOR, '[placeholder="채팅을 입력해주세요"]')
                        chat_input.click()
                        new_chat_input = driver.find_element(By.CLASS_NAME, 'live_chatting_input_input__2F3Et')
                        new_chat_input.send_keys('삭제할 명령어가 존재하지 않습니다: ' + del_command)
                        chat_btn = driver.find_element(By.CLASS_NAME, 'live_chatting_input_send_button__8KBrn')
                        chat_btn.click()
                elif cur_command in commands:
                    chat_input = driver.find_element(By.CSS_SELECTOR, '[placeholder="채팅을 입력해주세요"]')
                    chat_input.click()
                    new_chat_input = driver.find_element(By.CLASS_NAME, 'live_chatting_input_input__2F3Et')
                    new_chat_input.send_keys(commands[cur_command])
                    chat_btn = driver.find_element(By.CLASS_NAME, 'live_chatting_input_send_button__8KBrn')
                    chat_btn.click()
            prv_chat = chat
        time.sleep(5)

    print('Closing GlitchCat...') # The program is now closing

main_th = threading.Thread(target=main, args=(os.path.abspath(__file__),))
input_th = threading.Thread(target=get_input)
main_th.start()
input_th.start()