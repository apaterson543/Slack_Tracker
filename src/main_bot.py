import os
import time
from datetime import datetime
import re
import math
from slack import WebClient
from slack.errors import SlackApiError
from getpass import getpass
import pandas as pd
import numpy as np
import smtplib, ssl
import sqlite3

conn = sqlite3.connect('slack_user.db')
increment = 1
# ps -elf | grep python

#nohup watch -n 2 sudo python3 Driver.py &
#sleep 20
#echo "Continuous Driver initiated"

# sudo pkill -f Driver.py
# echo Continuous Driver has stopped



def send_email(content):
    port = 465
    email_address = input("Input email address: ")
    password = getpass()
    receiver_email = input("Input destination email")
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(email_address, password)
        server.sendmail(email_address, receiver_email, str(content))


def get_slack_client(type):
    if type == 'bot':
        return WebClient(os.environ['SLACK_BOT_TOKEN'])
    elif type == 'user':
        return WebClient(os.environ['SLACK_AUTH'])
    else:
        return None


def get_team(client):
    try:
        request = client.api_call("users.list")
    except SlackApiError as e:
        assert e.response["ok"] is False
        assert e.response["error"]
        print(f"Error: {e.response['error']}")

    return request


def get_users_presence(team, client):
    #statuses = pd.DataFrame(columns=['User', 'Presence', 'TotalTime'])
    statuses = pd.DataFrame(columns=['User', 'Presence'])
    if team['ok']:
        for user in team['members']:
            presence = client.users_getPresence(user=user['id'])
            user = {'User': user['name'], 'Presence': presence['presence']}
            statuses = statuses.append(user, ignore_index=True)

    # print(statuses)
    return statuses


def update_active_time(client_data, local_data):
    #math.isnan(value) -> returns bool
    if client_data.shape[0] != local_data.shape[0]:
        ''' 
        Add row to local_data from non-tracked user in client_Data
            without modifying other rows
        '''
    # statuses.loc[(statuses.User == 'apaterson543'), 'TotalTime'] = '0:0'
    for index, row in client_data.iterrows():
        local_user = local_data.iloc[index]
        if row['Presence'] == 'active' and local_user['Presence'] == 'active':
            total_time = local_user['TotalTime'].split(':')
            '''
            Needs to increment with time object instead of just incrementing based on nohup watch value
            '''

            new_time = calculate_time(total_time)
            local_data.iloc[index, local_data.columns.get_loc('TotalTime')] = new_time
            # local_data.iloc[index, 'TotalTime'] = '0:01:0'
        '''
        update active value
        '''
    write_to_db(local_data)

    #print(local_data)
    return None

def calculate_time(total_time):
    min = int(total_time[1])+increment
    hour = int(total_time[0])
    if min >= 60:
        hour += 1
        min -= 60
    new_time = '%s:%s' % (hour,min)
    return new_time

def send_chat_message(client, channel, text):
    """
    Send message to channel
    :param client: Slack bot client
    :param channel: String with channel name Ex: '#general'
    :param text: String with desired message text
    """
    response = client.chat_postMessage(channel=channel, text=text)
    assert response["message"]["text"] == text


def write_to_db(userdata):
    # if 'TotalTime' not in userdata.columns:
    #     userdata['TotalTime'] = np.nan
    #     reset_total_time(userdata)
    userdata.to_sql(name='userdata', con=conn, if_exists='replace',index=False)


def read_from_db():
    userdata = pd.read_sql('SELECT * from userdata', con=conn)
    return userdata


def check_weekly_reset():
    now = datetime.now()
    dt = pd.DataFrame(columns=['date','time'])
    dt = dt.append({'date':now.date(),'time':now.time()},ignore_index=True)
    conn.execute('DELETE FROM weekly_time')
    dt.to_sql(name='weekly_time',con=conn, if_exists='replace', index=False)
    week_start = pd.read_sql('SELECT * from weekly_time', con=conn)

    read_time = week_start['time'].values[0]
    time = read_time.split(':')
    read_date = week_start['date'].values[0]
    date = read_date.split('-')

def reset_total_time(stored_data):
    stored_data['TotalTime'] = np.nan
    stored_data['TotalTime'].fillna('00:00', inplace=True)

def main():
    client = get_slack_client('bot')
    user_info = get_team(client)
    statuses = get_users_presence(user_info, client)

    try:
        stored_data = read_from_db()

    except:
        reset_total_time(statuses)
        write_to_db(statuses)
        stored_data = read_from_db()
    update_active_time(statuses, stored_data)
    stored_data = read_from_db()
    print(stored_data)
    # check_weekly_reset()
    send_chat_message(client,'#random',str(stored_data))
    print(str(stored_data))


if __name__ == "__main__":
    main()
