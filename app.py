import os
from flask import Flask, request, flash, url_for, redirect, render_template, abort, send_from_directory
from flask.ext.sqlalchemy import SQLAlchemy

import csv
import operator

# initialization
app = Flask(__name__)
app.secret_key = 'my_secret_key'
app.config.update(
    DEBUG = True,
    SQLALCHEMY_DATABASE_URI = "postgres://dliookvgiickhr:AWu6D5UXvPaVU1TLLdy557Dh8y@ec2-50-19-219-235.compute-1.amazonaws.com:5432/d3vrtvgf4s94pv"
)
db = SQLAlchemy(app)

class Pattern(db.Model):
    __tablename__ = 'patterns'
    id = db.Column('pattern_id', db.Integer, primary_key=True)
    pattern = db.Column(db.String(12))
    trim_id = db.Column(db.Integer)
    year = db.Column(db.Integer)
    make = db.Column(db.String)
    model = db.Column(db.String)
    trim_name = db.Column(db.String)
 
    def __init__(self, pattern, trim_id, year, make, model, trim_name):
        self.pattern = pattern
        self.trim_id = trim_id
        self.year = year
        self.make = make
        self.model = model
        self.trim_name = trim_name

    def __init__(self, args):
        self.pattern = args[0]
        self.trim_id = args[1]
        self.year = args[2]
        self.make = args[3]
        self.model = args[4]
        self.trim_name = args[5]

# controllers
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'ico/favicon.ico')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route("/", methods=['GET', 'POST'])
def index():
	if request.method == 'POST':
		term = request.form['searchterm']
		if term == None or len(term) != 12:
			flash('You must provide a 12-digit VSN')
		elif not term[:6].isalpha() or not term[6:].isnumeric():
			flash('Invalid VSN format')
		else:
			results = match_vsn(term)
			results.sort(key = operator.attrgetter('diff'))
			results.reverse()
			return render_template('index.html', results=results)
	return render_template('index.html')

def match_vsn(term):
	term = term.upper()
	regex = ''
	for c in term:
		regex += '[{}|*]'.format(c)
	print regex
	results = db.session.query(Pattern).filter("pattern ~ '{}'".format(regex)).all()
	ret = []
	for res in results:
		res.diff = char_matches(res.pattern, term)
		ret.append(res)
	print ret
	return results

def char_matches(str1, str2):
	if not str1 or not str2:
		return 0

	count = 0
	for i in xrange(0, len(str1)):
		if i >= len(str2):
			return count
		if str1[i] == str2[i]:
			count += 1
	return count

# This is the method that was used to do the initial population of the DB with the csv
# This could easily be exposed on the front-end to allow admins to update the DB
def populate_from_csv():
	ifile  = open('vsn_data.csv', "rb")
	reader = csv.reader(ifile)

	rownum = 0
	for row in reader:
		# Save header row.
		if rownum == 0:
			header = row
		else:
			colnum = 0
			args = []
			for col in row:
				args.append(col)
				colnum += 1
			pattern_obj = Pattern(args)
			db.session.add(pattern_obj)
		rownum += 1
	db.session.commit()

	ifile.close()

# launch
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)