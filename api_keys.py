import json
import os

PRIVATE_FILE = 'config/private.json'
EXAMPLE_FILE = 'config/example.json'

if os.path.isfile(PRIVATE_FILE):
    api_key_json = json.load(open(PRIVATE_FILE, 'r'))
else:
    print('Can not find file "{}". Example api key loaded.'
          .format(PRIVATE_FILE))
    print('To resolve this issue create new "{}" file and fill it with your data as shown in "{}".'
          .format(PRIVATE_FILE, EXAMPLE_FILE))
    api_key_json = json.load(open(EXAMPLE_FILE, 'r'))

secret = api_key_json['secret']
public = api_key_json['public']


def get_public():
    return public


def get_secret():
    return secret


if __name__ == '__main__':
    print('Api key:\n secret: {} \n public: {}'.format(secret, public))
