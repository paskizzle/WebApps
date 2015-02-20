import webapp2
import logging
import re
import cgi
import jinja2
import os
import time
from google.appengine.api import memcache
from google.appengine.ext import db
global update
update = False
## see http://jinja.pocoo.org/docs/api/#autoescapin
def guess_autoescape(template_name):
    if template_name is None or '.' not in template_name:
        return False
    ext = template_name.rsplit('.', 1)[1]
    return ext in ('html', 'htm', 'xml')

JINJA_ENVIRONMENT = jinja2.Environment(
    autoescape=guess_autoescape,     ## see http://jinja.pocoo.org/docs/api/#autoescaping
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'])

def escape_html(s):
   return cgi.escape(s, quote = True)
def top_arts():
  global update
  if update == True:
    arts = db.GqlQuery("SELECT * FROM Art "
                    "ORDER BY created DESC "
                    "Limit 10" )
    arts = list(arts)
    memcache.set("toparts",arts)
    logging.info("db hit")
    update = False
    return memcache.get("toparts")
  else:
    logging.info("cache hit")
    update = False
    return memcache.get("toparts")
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

class Art(db.Model):
   title = db.StringProperty()  
   art = db.TextProperty()
   created = db.DateTimeProperty(auto_now_add = True)

class MainPage(Handler):   
    def render_ascii(self, title="", art="", error=""):
      arts = top_arts()
      self.render("ascii.html", title=title, art=art, error=error, arts=arts)

    def get(self):
        logging.info("********** MainPage GET **********")
        self.render_ascii()

    def post(self):
        global update
        logging.info("********** MainPage POST *********")

        title = self.request.get("title")
        art   = self.request.get("art")
        
        if title and art:
           a = Art(title=title,art=art)
           a.put()
           time.sleep(0.2)
           self.redirect("/")
           update = True
        else:
           error = "we need both a title and some artwork!"
           self.render_ascii(title, art, error)


application = webapp2.WSGIApplication([
    ('/', MainPage)
], debug=True)
