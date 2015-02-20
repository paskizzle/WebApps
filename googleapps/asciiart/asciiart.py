import webapp2
import logging
import re
import jinja2
import os
import datetime
import time
from google.appengine.ext import db


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

class MyHandler(webapp2.RequestHandler):
    def write(self, *items):    
        self.response.write(" : ".join(items))

    def render_str(self, template, **params):
        tplt = JINJA_ENVIRONMENT.get_template('templates/'+template)
        return tplt.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))
class Art(db.Model):
    title = db.StringProperty()
    art = db.TextProperty()
    time = db.DateTimeProperty(auto_now_add = True)
class MainPage(MyHandler):
    def get(self):
        logging.info("********** MainPage GET **********")
        self.render_ascii()
    def post(self):
        title = self.request.get("title")
        art = self.request.get("art")
        error_message = "A title and art is needed!"
        if not (art and title):
            #self.write("art",art,"title",title)
            self.render_ascii(title, art, error_message)
        if (art and title):
            a = Art()
            a.title = title
            a.art = art
            a.put()
            id = a.key().id()   # get the id of instance
            logging.info("*** ID of this Art is "+str(id))
            time.sleep(0.2)
            self.render_ascii()
    def render_ascii(self, title = "", art = "",error=""):
        arts = db.GqlQuery("SELECT * FROM Art ORDER BY time DESC")
        #self.write("art2", art)
        self.render("template.html", title=title, artin=art, error=error, arts=arts)
class Favorite(MyHandler):
    def get(self):
            tplt = JINJA_ENVIRONMENT.get_template('templates/favorite.html')
            self.render("favorite.html", favoritetitle = Art.get_by_id(5639445604728832).title,favoriteart = Art.get_by_id(5639445604728832).art)

application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/favorite', Favorite)
], debug=True)
