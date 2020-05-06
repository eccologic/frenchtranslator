import sqlite3
import requests
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, render_template, redirect

app = Flask(__name__)

BASE_URL = 'https://larousse.fr/'
DATABASE = 'ecco.db'

def http_parse(searchtype, term):
	retObj = { 'success': 0, 'error': '', 'content': '' }

	res = requests.get(BASE_URL + searchtype + term)
	
	if res.status_code == 200:
		parsed = BeautifulSoup(res.text, 'html.parser')
		retObj['success'] = 1
		retObj['content'] = parsed

	else:
		retObj['error'] = res.text
	
	return retObj

def get_translation(term):
	retObj = { 'success': 0, 'error': '', 'content': '' }
	wordInfo = { 'word' : term, 'translation': '', 'type': '' }

	section = 'dictionnaires/francais-anglais/'

	data = http_parse(section, term)

	if data['success'] == 0:
		retObj['error'] = ('Error getting html data. ' + data['error'])

	else:
		data = data['content']

		if len(data.findAll('a', { 'class': 'lienconj' })) >= 1:
			data.find('a', { 'class': 'lienconj' }).decompose()
		if len(data.findAll('a', { 'class': 'lienconj2' })) >= 1:
			data.find('a', { 'class': 'lienconj2' }).decompose()
		if len(data.findAll('span', { 'class': 'Metalangue2' })) >= 1:
			data.find('span', { 'class': 'Metalangue2' }).decompose()

		try:
			searchGrammar = data.find_all('span', { 'class': 'CategorieGrammaticale' })[0]
			searchResult = data.find_all('span', { 'class': 'Traduction' })[0] 
		
			wordInfo['type'] = searchGrammar.get_text().strip()
			wordInfo['translation'] = searchResult.get_text().strip()
			if wordInfo['translation'].endswith(','):
				wordInfo['translation'] = wordInfo['translation'][:-1]
		
			retObj['success'] = 1
			
		except Exception as Err:
			wordInfo['translation'] = 'Not found'
			retObj['success'] = 0
			retObj['error'] = Err

		retObj['content'] = wordInfo

	return retObj

def get_db():
	db = sqlite3.connect(DATABASE)

	def make_dicts(cursor, row):
		return dict((cursor.description[idx][0], value)
			for idx, value in enumerate(row))

	db.row_factory = make_dicts

	return db

def query_db(query, args=(), one=False):
	cur = get_db().execute(query, args)
	rv = cur.fetchall()
	get_db().commit()
	cur.close()
	return (rv[0] if rv else None) if one else rv

def get_date():
	now = datetime.now(timezone.utc).astimezone()	
	dt_string = now.strftime("%FT%T%z")	
	return dt_string

def check_word_db(checkword):
	
	retObj = { 'success': 0, 'error': ''}	
	
	check = query_db('SELECT word,date FROM wordtable WHERE word=:term', {'term': checkword })

	if len(check) >= 1:
		retObj['error'] = 'The word already exists in the database.'
		retObj['success'] = 0
	else:
		retObj['success'] = 1

	return retObj

def insert_db(word, translation, table, userid=1):
	retObj = { 'success': 0, 'error': '', 'content': '' }

	word = word.lower()

	db = get_db()
	date = get_date()

	if table == 'wordtable':
		db.cursor().execute('INSERT INTO wordtable (word, translation, date, userid) VALUES (:word, :translation, :date, :userid)', { 'word': word, 'translation': translation, 'date': date, 'userid': userid } )

	if table == 'historytable':
		db.cursor().execute('INSERT INTO historytable (word, translation, date, userid) VALUES (:word, :translation, :date, :userid)', { 'word': word, 'translation': translation, 'date': date, 'userid': userid } )

	db.commit()
	db.close()
	retObj['success'] = 1
	retObj['content'] = ('Added word ' + word + 'to the database at time ' + date)

	return retObj

def delete_word_db(searchterm):
	retObj = { 'success': 0, 'error': '', 'content': '' }
	check = check_word_db(searchterm)
	
	if check['success'] == 1:
		retObj['success'] = 0
		retObj['error'] = 'The word does not exist in the database'

	else:
		db = get_db()
		db.cursor().execute('DELETE FROM wordtable WHERE word=(:word)', { 'word': searchterm } )
		db.commit()
		retObj['content'] = ('Deleted word ' + searchterm + ' from the database.')
		retObj['success'] = 1

	return retObj

def extract_words(table):
	
	alldb = query_db('SELECT * FROM ' + table)
	return alldb

@app.route('/')
def index():
        return render_template('index.html')

@app.route('/words')
def hostwords():
        words = extract_words('wordtable')
        return render_template('words.html',words=words)

@app.route('/history')
def history():
        words = extract_words('historytable')
        return render_template('history.html', words=words)


@app.route('/save', methods=['POST'])
def save():
	form_data = request.form

	word = form_data['save'].split(';')[0].lower()
	translation = form_data['save'].split(';')[1].lower()
	table = 'wordtable'

	post = insert_db(word, translation, table)
	return redirect("/search/" + word)

@app.route('/delete', methods=['POST'])
def delete():

	form_data = request.form

	if 'delete' in form_data:
		if form_data['delete'] == 'clear-history':
			db = get_db()
			db.execute('DELETE FROM historytable')
			db.commit()
			db.close()
			return redirect('/history')

		else:
			post = delete_word_db(form_data['delete'].lower())
			return redirect('/words')

	if 'delete-search' in form_data:
		post = delete_word_db(form_data['delete-search'].lower())
		return redirect('/search/' + form_data['delete-search'].lower())

@app.route('/search/<word>', methods=['GET'])
def search_word(word):
	check_db = check_word_db(word)	
	content = get_translation(word)
	
	word = content['content']['word']
	translation = content['content']['translation']
	table = 'historytable'
	
	insert_db(word, translation, table)

	if content['success'] == 0:
		return render_template('not_found.html', content=content['content'])
		
	else:
		content['content']['word'] = content['content']['word'].capitalize()
		content['content']['translation'] = content['content']['translation'].capitalize()
	
		return render_template('search.html', content=content['content'], not_in_db = check_db['success'])

@app.route('/search', methods=['GET', 'POST'])
def search_form():
	form_data = request.form
	return redirect("/search/" + form_data['inputSearch'].lower())

app.run(host='0.0.0.0')
