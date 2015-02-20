import webapp2
import logging
import re
import cgi
import jinja2
import os
import hashlib

from google.appengine.ext import db

## see http://jinja.pocoo.org/docs/api/#autoescaping
def guess_autoescape(template_name):
   if template_name is None or '.' not in template_name:
      return False
      ext = template_name.rsplit('.', 1)[1]
      return ext in ('html', 'htm', 'xml')
def hash_str(s):
    s = str(s)
    s = hashlib.md5(s)
    return s.hexdigest()
def make_secure_val(s):
    string = str(s) + '|' + hash_str(s)
    return string
def check_secure_val(h):
    temp = h.split('|')
    s = temp[0]
    if make_secure_val(s) == h:
        return s
    else:
        return None
JINJA_ENVIRONMENT = jinja2.Environment(
   autoescape=guess_autoescape,     ## see http://jinja.pocoo.org/docs/api/#autoescaping
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'])

class Handler(webapp2.RequestHandler):
    def write(self, *items):    
        self.response.write(" : ".join(items))

    def render_str(self, template, **params):
        tplt = JINJA_ENVIRONMENT.get_template('templates/'+template)
        return tplt.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class MainPage(Handler):   
    def get(self):
        logging.info("********** MainPage GET **********")
        self.response.headers['Content-Type'] = 'text/plain'
        ##1 Assign the variable 'visits' to the value of the 'visits'

        ##1 cookie obtained from the browsers HTTP response. If the cookie 
        ##1 does not exist, set the variable 'visits' to '0'
        start = make_secure_val(0)
        visits = self.request.cookies.get('visits', start) 
        ##2 If the variable visits is an integer (i.e. use str.isdigit())
        ##2 increment visits by 1
        ##2 else set visits to 0
        if check_secure_val(visits):
            visits = int(check_secure_val(visits))
            visits = visits + 1
            visits = make_secure_val(visits)
        else:
            visits = "dont mess with my cookies"     
        ##3 Add the 'Set-Cookie:' header with the value set to the 
        ##3 variable 'visits' to the HTTP response
        self.response.headers.add_header('Set-Cookie', 'visits=%s' % visits)
        logging.info(visits)
        if check_secure_val(visits):
            if (check_secure_val(visits) and int(check_secure_val(visits))) > 15:
                self.response.write("congrats")
            else:
                self.response.write("Keep refreshing. Current refreshes:" + check_secure_val(visits))
        else:
            self.response.write(visits)
    def post(self):
        logging.info("DBG: MainPage POST")

application = webapp2.WSGIApplication([
    ('/', MainPage)
], debug=True)
