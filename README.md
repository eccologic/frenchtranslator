# FrenchTranslator

## Description
Using the wonderful site of https://larousse.fr to grab the english translation for french words and adding them to an sqlite database, if wanted.

It is presented through a Flask application website.

* Looks up word through request to larousse.fr
* Parses html code for the important parts
* Allows for saving of words with translation
* Saves all searches in a search history

## Setup

### Dependencies
* python3
* Flask
* BeautifulSoup
* Internet access

1. Set up the database through __setup_db.py__.
1. Run __export FLASK_APP=main.py__.
1. Start the app by running __python3 -m flask run__.

## Usage
Go to http://127.0.0.1:5000/

Words that are searched for will be placed in __History__.
You can save words to find them under __Saved__.
You can delete saved words from the searched word itself, or through the __Saved__ page.

Allez ! Apprenez le francais plus vite avec Frenchtranslator !
