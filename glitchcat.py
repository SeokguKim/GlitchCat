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
import requests
import re
if sys.platform == 'win32':
    import win_unicode_console
    win_unicode_console.enable()

def my_exit(exit_code, uid): # Exit the program and disable the unicode console if it is enabled
    if sys.platform == 'win32':
        win_unicode_console.disable()
    
    if exit_code == 1: # If the exit code is 1, close the program
        print('The program will now close.')
        for thread in threading.enumerate():
            if thread.name != 'MainThread':
                thread.join()

    elif exit_code == 2: # If the exit code is 2, print an error message
        print('An error occurred.' + (uid and ' (UID: ' + uid + ')' or '') + ' The program will now close.')

    elif exit_code == 3: # If the exit code is 3, restart the program
        for thread in threading.enumerate():
            if thread.name != 'MainThread':
                thread.join()
        os.execl(sys.executable, sys.executable, *sys.argv)
    
    
    sys.exit(exit_code)

def get_input(file_path): # Get the user input
    global flags
    global gflag
    user_input = sys.stdin.readline().rstrip()
    if user_input == 'qa': # If the user input is 'qa', close all threads
        for uid in flags:
            flags[uid] = False
        gflag = False
        return
    elif user_input.split()[0] == 'q': # If the user input is 'q', close the thread with the given UID
        if len(user_input.split()) > 1:
            uid = user_input.split()[1]

            if uid in flags:
                flags[uid] = False
            else:
                if re.match(r'^[a-z0-9]{32}$', uid):
                    print('The thread with the given UID is already running.')
                else:
                    print('Invalid UID.')
        else:
            print('Invalid UID or the thread has already been closed.')
    elif user_input.split()[0] == 'n': # If the user input is 'n', start a new thread with the given UID
        if len(user_input.split()) > 1:
            uid = user_input.split()[1]
            if uid in flags and flags[uid] == True:
                print('The thread with the given UID is already running.')
            else:
                if re.match(r'^[a-z0-9]{32}$', uid):
                    flags[uid] = True
                    threading.Thread(target=listen_to_ch, args=(uid, file_path, )).start()
                else:
                    print('Invalid UID.')
        else:
            print('Invalid UID.')
    elif user_input.split()[0] == 'l': # If the user input is 'l', list all reunning threads
        print('Running Threads:')
        for uid in flags:
            print(uid)
    elif user_input.split()[0] == 'u': # If the user input is 'u', update the UID files and restart the program
        uids_path = os.path.join(os.path.dirname(file_path), 'uids.csv')
        if not os.path.exists(uids_path):
            f = open(uids_path, 'w')
            f.write('uid\n')
            f.close()
        uids_data = pandas.read_csv(uids_path)
        uids = []
        for i in range(len(uids_data)):
            uids.append(uids_data['uid'][i])
        for uid in flags:
            if uid not in uids:
                uids.append(uid)
        uids_data = pandas.DataFrame(uids, columns=['uid'])
        uids_data.to_csv(uids_path, index=False)
        my_exit(3, 'main')
    elif user_input == 'h' or user_input == 'help': # If the user input is 'h' or 'help', show the help message
        print('Commands:')
        print('q [UID] - Quit the thread with the given UID')
        print('n [UID] - Start a new thread with the given UID')
        print('l - List all running threads')
        print('u - Update the UID files and restart the program')
        print('qa - Quit all threads and close the program')
        print('h or help - Show this message')

    threading.Thread(target=get_input, args=(file_path,)).start() # Start a new thread to get the user input

def listen_to_ch(uid, origin_file): # Main function
    global flags
    flags[uid] = True
    
    print_w_uid = lambda x: print(uid + ': ' + x) # Print the given message with the UID

    print_w_uid('Loading Commands...')
    commands = {}
    commands_file = os.path.join(os.path.dirname(origin_file), 'commands_' + uid + '.csv')
    if not os.path.exists(commands_file): # If the file does not exist, print an error message and exit the program
        f = open(commands_file, 'w')
        f.write('command,response\n')
        f.close()
        
    commands_data = pandas.read_csv(commands_file)
    for i in range(len(commands_data)):
        commands[commands_data['command'][i]] = commands_data['response'][i]

    print_w_uid('Loading auth file...') # chzzk_auth.csv
    auth_file = os.path.join(os.path.dirname(origin_file), 'chzzk_auth_' + uid + '.csv')
    if not os.path.exists(auth_file): # If the file does not exist, print an error message and exit the program
        f = open(auth_file, 'w')
        f.write('bot_id,bot_pw\n')
        f.close()

    auth_data = pandas.read_csv(auth_file, nrows=1)

    bot_id = auth_data['bot_id'][0] if len(auth_data['bot_id']) > 0 else ''
    bot_pw = auth_data['bot_pw'][0] if len(auth_data['bot_pw']) > 0 else ''

    print_w_uid('Loading chat...') # Open the chat page
    dest_ch = 'https://chzzk.naver.com/live/' + uid + '/chat'
    naver_login = 'https://nid.naver.com/nidlogin.login'
    naver_main = 'https://www.naver.com/'
    broadcast_info = 'https://studio.chzzk.naver.com/' + uid + '/live'
    blocklist_info = 'https://studio.chzzk.naver.com/' + uid + '/blocklist'

    driver = webdriver.Chrome()
    driver.get(naver_login)
    time.sleep(2)

    pyperclip.copy(bot_id)
    driver.find_element(By.CSS_SELECTOR, '#id').send_keys(Keys.CONTROL, 'v')
    pyperclip.copy(bot_pw)
    driver.find_element(By.CSS_SELECTOR, '#pw').send_keys(Keys.CONTROL, 'v')
    pyperclip.copy('')
    driver.find_element(By.XPATH,'//*[@id="log.login"]').click()

    while driver.current_url != naver_main:
        print_w_uid('Please manually log in to Naver and go to the Naver main page...')
        time.sleep(5)
    time.sleep(2)

    try:
        driver.find_element(By.CSS_SELECTOR, '[class="MyView-module__desc_email___JwAKa"] ')
    except:
        print_w_uid('Login failed. Please check your ID and password.')
        driver.quit()
        my_exit(2, uid)

    driver.get(dest_ch)

    print_w_uid('Chat loaded.') # The chat is now loaded
    print_w_uid('Listening...') # The program is now listening to the chat

    refresh_counter = 60
    prv_chat = []
    
    send_text = lambda driver, text, element: driver.execute_script(f'arguments[0].innerText = "{text}"', element) # Send the given text to the chat
    
    while flags[uid]:
        try:
            bs = BeautifulSoup(driver.page_source, 'html.parser')
            chat = bs.select('button.live_chatting_message_wrapper__xpYre')
            time.sleep(1)
        except:
            print_w_uid('An error occurred while getting the chat. Please check your internet connection.')
            try:
                driver.quit()
            except:
                pass
            my_exit(2, uid)
        
        refresh_counter -= 1
        if refresh_counter == 0: # If the refresh counter is 0, refresh the page
            driver.refresh()
            refresh_counter = 60
            prv_chat = []

        if prv_chat == []: # If there is no previous chat, set the previous chat to the current chat
            prv_chat = chat
            continue

        if chat != prv_chat: # If there is a new chat, check if it is a command
            for i in range(len(chat) - len(prv_chat), 0, -1): # Check the new chat from the end
                cur_chat = chat[-i]

                is_user_mod = cur_chat.find('img', alt='스트리머') or cur_chat.find('img', alt='채널 관리자')
                is_user_tiny_mod = cur_chat.find('img', alt='채팅 운영자')

                cur_user = cur_chat.select('span.live_chatting_username_nickname__dDbbj')[0].text.rstrip(':')
                cur_msg = cur_chat.select('span.live_chatting_message_text__DyleH')[0].text
                cur_command = len(cur_msg.split()) > 0 and cur_msg.split()[0] or ''
                
                if cur_command == "!추가": # If the command is '!추가', add the command
                    if not is_user_mod and not is_user_tiny_mod:
                        continue
                
                    if len(cur_msg.split()) < 3:
                        continue

                    new_command = cur_msg.split()[1]
                    new_response = ' '.join(cur_msg.split(' ')[2:])
                    commands[new_command] = new_response
                    commands_data = pandas.DataFrame(commands.items(), columns=['command', 'response'])
                    commands_data.to_csv(commands_file, index=False)
                    print_w_uid('Command added: ' + new_command + ' -> ' + new_response)

                    chat_input = driver.find_element(By.CSS_SELECTOR, '[placeholder="채팅을 입력해주세요"]')
                    chat_input.click()
                    new_chat_input = driver.find_element(By.CSS_SELECTOR, '[placeholder="채팅을 입력해주세요"]')
                    send_text(driver, '명령어가 추가되었습니다: ' + new_command + ' -> ' + new_response, new_chat_input)
                    new_chat_input.send_keys(Keys.ENTER)

                elif cur_command == "!삭제": # If the command is '!삭제', delete the command
                    if not is_user_mod and not is_user_tiny_mod:
                        continue

                    if len(cur_msg.split()) < 2:
                        continue

                    del_command = cur_msg.split()[1]
                    if del_command in commands: # If the command exists, delete the command
                        del commands[del_command]
                        commands_data = pandas.DataFrame(commands.items(), columns=['command', 'response'])
                        commands_data.to_csv(commands_file, index=False)
                        print_w_uid('Command deleted: ' + del_command)

                        chat_input = driver.find_element(By.CSS_SELECTOR, '[placeholder="채팅을 입력해주세요"]')
                        chat_input.click()
                        new_chat_input = driver.find_element(By.CSS_SELECTOR, '[placeholder="채팅을 입력해주세요"]')
                        new_chat_input.send_keys('명령어가 삭제되었습니다: ' + del_command)
                        new_chat_input.send_keys(Keys.ENTER)

                    else: # If the command does not exist, print an error message
                        chat_input = driver.find_element(By.CSS_SELECTOR, '[placeholder="채팅을 입력해주세요"]')
                        chat_input.click()
                        new_chat_input = driver.find_element(By.CSS_SELECTOR, '[placeholder="채팅을 입력해주세요"]')
                        new_chat_input.send_keys('삭제할 명령어가 존재하지 않습니다: ' + del_command)
                        new_chat_input.send_keys(Keys.ENTER)    
                
                elif cur_command == "!밴": # If the command is '!밴', ban the user
                    if not is_user_mod:
                        continue

                    if len(cur_msg.split()) < 2:
                        continue
                    
                    ban_user = cur_msg.split()[1]
                    print_w_uid('Banning user: ' + ban_user)
                    driver.get(blocklist_info)
                    time.sleep(2)

                    if driver.find_element(By.XPATH, '//*[text()="이 페이지를 이용할 수 있는 권한이 없습니다."]'):
                        driver.get(dest_ch)
                        time.sleep(1)
                        continue

                    blocklist = driver.find_element(By.CSS_SELECTOR, '[placeholder="닉네임 또는 UID를 입력해주세요"]')
                    blocklist.click()
                    new_blocklist = driver.find_element(By.CSS_SELECTOR, '[pladceholder="닉네임 또는 UID를 입력해주세요"]')
                    new_blocklist.send_keys(Keys.CONTROL, 'a')
                    new_blocklist.send_keys(Keys.DELETE)
                    new_blocklist.send_keys(ban_user)
                    new_blocklist.send_keys(Keys.ENTER)
                    time.sleep(1)
                    driver.get(dest_ch)
                    time.sleep(1)
                    
                    chat_input = driver.find_element(By.CSS_SELECTOR, '[placeholder="채팅을 입력해주세요"]')
                    chat_input.click()
                    new_chat_input = driver.find_element(By.CSS_SELECTOR, '[placeholder="채팅을 입력해주세요"]')
                    new_chat_input.send_keys('밴을 시도했습니다: ' + ban_user)
                    new_chat_input.send_keys(Keys.ENTER)
                
                elif cur_command == "!방제": # If the command is '!방제', change the title of the broadcast
                    if not is_user_mod:
                        continue
                    
                    if len(cur_msg.split()) < 2:
                        continue

                    new_title_name = ' '.join(cur_msg.split()[1:])
                    print_w_uid('Changing broadcast title: ' + new_title_name)
                    driver.get(broadcast_info)
                    time.sleep(2)

                    try:
                        driver.find_element(By.XPATH, '//*[text()="이 페이지를 이용할 수 있는 권한이 없습니다."]')
                        driver.get(dest_ch)
                        time.sleep(1)
                        continue
                    except:
                        pass

                    title = driver.find_element(By.CSS_SELECTOR, '[placeholder="방송 제목을 입력해주세요."]')
                    title.click()
                    new_title = driver.find_element(By.CSS_SELECTOR, '[placeholder="방송 제목을 입력해주세요."]')
                    new_title.send_keys(Keys.CONTROL, 'a')
                    new_title.send_keys(Keys.DELETE)
                    send_text(driver, new_title_name, new_title)
                    time.sleep(1)
                    upate_btn = driver.find_element(By.CLASS_NAME, 'live_form_footer__lDYmf').find_element(By.CSS_SELECTOR, 'button')
                    
                    try:
                        upate_btn.click()
                    except:
                        pass

                    driver.get(dest_ch)
                    time.sleep(2)
                    
                    chat_input = driver.find_element(By.CSS_SELECTOR, '[placeholder="채팅을 입력해주세요"]')
                    chat_input.click()
                    new_chat_input = driver.find_element(By.CSS_SELECTOR, '[placeholder="채팅을 입력해주세요"]')
                    send_text(driver, '방제 변경을 시도했습니다: ' + new_title_name, new_chat_input)
                    new_chat_input.send_keys(Keys.ENTER)

                elif cur_command == "!게임": # If the command is '!게임', change the game of the broadcast
                    if not is_user_mod:
                        continue

                    if len(cur_msg.split()) < 2:
                        continue

                    new_game_name = ' '.join(cur_msg.split()[1:])
                    print_w_uid('Changing broadcast game: ' + new_game_name)
                    driver.get(broadcast_info)
                    time.sleep(2)

                    try:
                        driver.find_element(By.XPATH, '//*[text()="이 페이지를 이용할 수 있는 권한이 없습니다."]')
                        driver.get(dest_ch)
                        time.sleep(1)
                        continue
                    except:
                        pass

                    game = driver.find_element(By.CSS_SELECTOR, '[placeholder="카테고리 검색"]')
                    game.click()
                    new_game = driver.find_element(By.CSS_SELECTOR, '[placeholder="카테고리 검색"]')
                    new_game.send_keys(Keys.CONTROL, 'a')
                    new_game.send_keys(Keys.DELETE)
                    new_game.send_keys(new_game_name)
                    time.sleep(1)
                    searched_game = driver.find_element(By.CSS_SELECTOR, '[role="listbox"]')
                    searched_game.click()

                    time.sleep(1)
                    upate_btn = driver.find_element(By.CLASS_NAME, 'live_form_footer__lDYmf').find_element(By.CSS_SELECTOR, 'button')
                    
                    try:
                        upate_btn.click()
                    except:
                        pass

                    driver.get(dest_ch)
                    time.sleep(2)

                    chat_input = driver.find_element(By.CSS_SELECTOR, '[placeholder="채팅을 입력해주세요"]')
                    chat_input.click()
                    new_chat_input = driver.find_element(By.CSS_SELECTOR, '[placeholder="채팅을 입력해주세요"]')
                    new_chat_input.send_keys('게임 변경을 시도했습니다: ' + new_game_name)
                    new_chat_input.send_keys(Keys.ENTER)

                elif cur_command in commands: # If the command exists, execute the command
                    print_w_uid('Command detected: ' + cur_command)
                    chat_input = driver.find_element(By.CSS_SELECTOR, '[placeholder="채팅을 입력해주세요"]')
                    chat_input.click()
                    new_chat_input = driver.find_element(By.CSS_SELECTOR, '[placeholder="채팅을 입력해주세요"]')
                    send_text(driver, commands[cur_command], new_chat_input)
                    new_chat_input.send_keys(Keys.ENTER)

                else:
                    continue

                break

            prv_chat = chat
            
        time.sleep(5)

    print_w_uid('Closing Thread...') # The program is now closing
    driver.quit()
        
def main(file_path):
    global flags
    flags = {}

    global gflag
    gflag = True
    print('Welcome to GlitchCat!')

    uids = []
    uids_path = os.path.join(os.path.dirname(file_path), 'uids.csv')
    if not os.path.exists(uids_path): # If the file does not exist, print an error message and exit the program
        f = open(uids_path, 'w')
        f.write('uid\n')
        f.close()

    uids_data = pandas.read_csv(uids_path)
    for i in range(len(uids_data)):
        uids.append(uids_data['uid'][i])

    for uid in uids: # Start a new thread for each UID
        if not re.match(r'^[a-z0-9]{32}$', uid):
            print('Invalid UID: ' + uid)
            continue
        flags[uid] = True
        threading.Thread(target=listen_to_ch, args=(uid, file_path, )).start()
        time.sleep(1)
    
    if len(uids) == 0: # If there are no UIDs, print an error message and exit the program
        print('No UIDs found. Please update the UID files and restart the program.')
        my_exit(1, 'main')

    while gflag:
        time.sleep(5)

    print('Closing GlitchCat...')

main_th = threading.Thread(target=main, args=(__file__,))
input_th = threading.Thread(target=get_input, args=(__file__,))
main_th.start()
input_th.start()