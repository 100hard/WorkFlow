python
# File: joke_cli.py
import requests

def get_random_joke():
    response = requests.get('https://official-joke-api.appspot.com/random_joke')
    joke = response.json()
    return joke['setup'] + '\n' + joke['punchline']

if __name__ == '__main__':
    print(get_random_joke())
