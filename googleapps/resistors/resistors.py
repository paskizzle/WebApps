import webapp2
import logging
import re
import cgi
import jinja2
import os
import hmac

from google.appengine.ext import db


# Color names aranged by value (index=value)
COLORS = [
	'black',
	'brown',
	'red',
	'orange',
	'yellow',
	'green',
	'blue',
	'violet',
	'grey',
	'white']
MULTI = [
	'black',
	'brown',
	'red',
	'orange',
	'yellow',
	'green',
	'blue',
	'violet']
color1 = [
	'black',
	'brown',
	'red',
	'orange',
	'yellow',
	'green',
	'blue',
	'violet',
	'grey',
	'white']
color2 = [
	'black',
	'brown',
	'red',
	'orange',
	'yellow',
	'green',
	'blue',
	'violet',
	'grey',
	'white']
color3 = [
	'black',
	'brown',
	'red',
	'orange',
	'yellow',
	'green',
	'blue',
	'violet',
	'grey',
	'white']
color4 = [
	'black',
	'brown',
	'red',
	'orange',
	'yellow',
	'green',
	'blue',
	'violet']
# Multipliers in a dictionary, organized by value for ease of reading
MULTIPLIER = {
	1e0:    'black',
	1e1:    'brown',
	1e2:    'red',
	1e3:    'orange',
	1e4:    'yellow',
	1e5:    'green',
	1e6:    'blue',
	1e7:    'violet'}


# RGB Color Codes
COLORCODES = {
	"black":    "#000000",
	"brown":    "#a52a2a",
	"red":      "#ff0000",
	"orange":   "#ffa500",
	"yellow":   "#ffff00",
	"green":    "#008000",
	"blue":     "#0000ff",
	"violet":   "#800080",
	"grey":     "#808080",
	"white":    "#ffffff",
	"silver":   "#c0c0c0",
	"gold":     "#d4a017"}

VNAME_RE = re.compile(r"^.+\s.+")
def validname(name):
	return VNAME_RE.match(name)
def getColors(num):
	# To-be return value
	returnVals = []
	failReturnVals = [COLORS[0], COLORS[0], MULTIPLIER[1e0]]
	# Process the number
	indexPlaceholder = 0
	numStr = str(num)
	bandValues = ""
	indexPlaceholder = 2
	bandValues = numStr[:indexPlaceholder]
	# If there's 4 stripes
	if (num / float(bandValues)) % 10:
		indexPlaceholder = 3
		bandValues = numStr[:indexPlaceholder]
	# If there's a third band to add
	if len(numStr) > indexPlaceholder:
		if numStr[indexPlaceholder] != "0":
			bandValues = numStr[:indexPlaceholder + 1]
	# Needs another black band
	if len(bandValues) < 2:
		bandValues = bandValues + "0"
	for value in bandValues:
		if value == ".":
			continue
		returnVals.append(COLORS[int(value)])
	returnVals.append(MULTIPLIER[round(num / float(bandValues.replace(".", "")), 2)])
	return returnVals


#List of colors (strings) to ohms (float)
def getOhms(colors):
	bandValues = ""
	multiply = 0
	# Get the index numbers of the colors
	while len(colors) > 1:
		bandValues = bandValues + str(COLORS.index(colors.pop(0)))
	# Find the key (multiplier) based on color (no easy way to do this)
	for key, value in MULTIPLIER.items():
		if value == colors[0]:
			multiply = key
			break
	# Color value * multiplier
	return float(bandValues) * multiply

## see http://jinja.pocoo.org/docs/api/#autoescaping
def guess_autoescape(template_name):
   if template_name is None or '.' not in template_name:
	  return False
	  ext = template_name.rsplit('.', 1)[1]
	  return ext in ('html', 'htm', 'xml')

JINJA_ENVIRONMENT = jinja2.Environment(
   autoescape=guess_autoescape,     ## see http://jinja.pocoo.org/docs/api/#autoescaping
	loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
	extensions=['jinja2.ext.autoescape'])

class Handler(webapp2.RequestHandler):
	## saves you from having to type self.response.out.write
	def write(self, a):            
		self.response.out.write(a)
	
	## takes a template and dictionary and returns a string with the rendered template
	def render_str(self, template, **params): 
		template = JINJA_ENVIRONMENT.get_template('templates/'+template)
		return template.render(params)

	## takes a template and dictionary and writes the rendered template
	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))

SECRET="imsosecret"
def hash_str(s):
   return hmac.new(SECRET,s).hexdigest()

def make_secure_val(s):
   return s+'|'+hash_str(s)

def check_secure_val(h):
   val = h.split('|')[0]
   if (h == make_secure_val(val)):
	  return val
#def write_page(c1 = 0, c2 = 0, c3 = 0, c4 = 0):
#	self.render("resistors.html", COLORS = COLORS, MULTI = MULTI, resis = resis, c1 = c1, c2= c2, c3 = c3, c4 = c4)
class MainPage(Handler):   
	def get(self):
	   title1 = "Web Applications Midterm"
	   title2 = "Good Luck"
	   error = "Please enter a first and last name"
	   self.render("front.html",
				   place_holder1=title1,
				   place_holder2=title2)
	def post(self):
		title1 = "Web Applications Midterm"
		title2 = "Good Luck"
		error = "Please enter a first and last name"
		name = self.request.get("q")
		if validname(name):
			temp = name.split(" ")
			nameval = str(temp[0])+"+"+str(temp[1])
			hashnameval = make_secure_val(nameval)
			self.response.headers.add_header('Set-Cookie', 'myUser=%s; Path=/;' % hashnameval)
			self.redirect("/resistors")
			logging.info("front working")
		else:
			self.render("front.html",
			place_holder1= title1,
			place_holder2= title2,
			error = error)
class resisdb(db.Model):
	name = db.StringProperty()
	resis = db.IntegerProperty()
	quant = db.IntegerProperty()
	colors = db.StringListProperty()
	created = db.DateTimeProperty(auto_now_add = True)
class Resistorhandler(Handler):
	def get(self):
		self.render("resistors.html", C1 = COLORS, C2 = COLORS, C3 = COLORS, MULTI = MULTI)
	def post(self):
		c1 = self.request.get("co1")
		c2 = self.request.get("co2")
		c3 = self.request.get("co3")
		c4 = self.request.get("co4")
		selcolor = [self.request.get("co1"),self.request.get("co2"),self.request.get("co3"),self.request.get("co4")]
		logging.info(selcolor)
		resis = getOhms(selcolor)
		resis = int(resis)
		if resis == 0:
			resis = str(0)
		if self.request.get("k"):
			if check_secure_val(self.request.cookies.get("myUser")):
				temp = self.request.cookies.get("myUser").split("+")
				temp2 = temp[1].split("|")
				name = temp[0] + " " + temp2[0]
				d = resisdb()
				d.name = name
				d.resis = int(resis)
				d.quant = int(self.request.get("k"))
				d.colors = selcolor
				d.put()
			else:
				self.redirect("/")
		if resis%1000000 == 0:
			resis = str(resis).replace("0","",6)+"m"
		elif int(resis) % 1000 == 0 and int(resis) % 1000000 != 0:
			resis = str(resis).replace("0","",4)+"k"
		#color1 = COLORS
		color1.remove(c1)
		color1.insert(0, c1)
		logging.info(color1)
		
		#color2 = COLORS
		color2.remove(c2)
		color2.insert(0, c2)
		logging.info(color2)
		#color3 = COLORS
		color3.remove(c3)
		color3.insert(0, c3)
		logging.info(color3)
		#color4 = MULTI
		color4.remove(c4)
		color4.insert(0, c4)
		logging.info(color4)
		self.render("resistors.html", resis = resis, C1 = color1, C2 = color2, C3 = color3, MULTI = color4)
class Databasehandler(Handler):
	def get(self):
		dbs = db.GqlQuery("SELECT * FROM resisdb ORDER BY resis ASC")
		self.render("db.html", db = dbs)
application = webapp2.WSGIApplication([
	('/', MainPage),
	('/resistors', Resistorhandler),
	('/database', Databasehandler)
], debug=True)
