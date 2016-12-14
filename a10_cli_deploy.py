#!/usr/bin/env python


import getpass
import json
import logging
import os
import requests
import threading
import time

try:
    from queue import Queue
    print('INFO: Imported queue')
except ImportError:
    try:
        # Python 2.7
        from Queue import Queue
        print('INFO: Imported Queue')
    except ImportError:
        print('ERROR: Unable to import the Queue module.')
        exit()


logging.captureWarnings(True)
hosts_file = 'hosts.txt'
commands_file = 'commands.txt'
output_folder_name = 'output'
number_of_threads = 5


def main():
    clean_output_folder()
    print("We are going to send the following commands to {} TPS.".format(len(hosts_list)))
    print("{}".format(commands_list))
    for device in hosts_list:
        q.put(device)

    start = time.time()

    for x in range(number_of_threads):
        t = threading.Thread(target=threader)

        # classifying as a daemon, so they will die when the main dies
        t.daemon = True

        # begins, must come after daemon definition
        t.start()

    q.join()
    print('Entire job took:', time.time() - start)


def threader():
    while True:
        # gets an worker from the queue
        device = q.get()

        # Run the example job with the avail worker in queue (thread)
        execute_command(device)

        # completed with the job
        q.task_done()


def clean_output_folder():
    for f in os.listdir(output_folder_name):
        filename = get_full_output_pathname(f)
        print("Cleaning up {}.".format(filename))
        os.remove(filename)


def execute_command(host):
    print("Connecting to {}.".format(host))
    logfile = get_full_output_pathname(host + '.txt')
    base_url = 'https://' + host
    auth_headers = {'content-type': 'application/json'}
    auth_payload = {"credentials": {"username": username, "password": password}}
    auth_endpoint = '/axapi/v3/auth'
    url = base_url + auth_endpoint
    r = requests.post(url, data=json.dumps(auth_payload), headers=auth_headers, verify=False)
    signature = r.json()['authresponse']['signature']

    # Headers beyond this point should include the authorization token
    common_headers = {'Content-type': 'application/json', 'Authorization': 'A10 {}'.format(signature)}

    clideploy_path = "/axapi/v3/clideploy/"
    url = base_url + clideploy_path
    clideploy_payload = {
        "commandList": commands_list
    }
    r = requests.post(url, data=json.dumps(clideploy_payload), headers=common_headers, verify=False)
    print(r.content)
    data = r.text
    save(logfile, data)

    # Log off
    logoff_endpoint = '/axapi/v3/logoff'
    url = base_url + logoff_endpoint
    print("Log off")
    requests.post(url, headers=common_headers, verify=False)


def load(name):
    """
    Loads a file into memory, if it exists

    :param name: The name of the file
    :return: The contents of the file as a list
    """
    data = []
    filename = get_full_pathname(name)
    if os.path.exists(filename):
        print("Loading {}...".format(filename))
        with open(filename) as fin:
            for entry in fin.readlines():
                data.append(entry.rstrip())
    return data


def save(name, data):
    """
    Saves the contents of memory to a file, if it exists

    :param name: The name of the file
    :param data: The contents of the as a list
    """
    filename = get_full_pathname(name)

    with open(filename, 'a') as fout:
        print('Saving results to {}'.format(filename))
        for entry in data:
            fout.write(entry)


def get_full_output_pathname(name):
    filename = get_full_pathname(os.path.join(output_folder_name, name))
    return filename


def get_full_pathname(name):
    filename = os.path.abspath(os.path.join('.', name))
    return filename


def get_authorization():
    user = 'GME\\' + getpass.getuser()
    #user = 'admin'
    passwd = getpass.getpass('Enter password for {}: '.format(user))
    return user, passwd


if __name__ == '__main__':
    hosts_list = load(hosts_file)
    commands_list = load(commands_file)
    username, password = get_authorization()
    q = Queue()

    main()
