import webapp2
import logging
import re
import jinja2
import os
import datetime
import time
import random
import string
from google.appengine.ext import db


## see http://jinja.pocoo.org/docs/api/#autoescaping
def guess_autoescape(template_name):
    if template_name is None or '.' not in template_name:
        return False
    ext = template_name.rsplit('.', 1)[1]
    return ext in ('html', 'htm', 'xml')
def make_salt():
    salt = (''.join(random.choice(string.ascii_letters + string.digits)) for i in range(25))
    return salt
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
class post(db.Model):
    subject = db.StringProperty()
    content = db.TextProperty()
    created = db.DateTimeProperty(auto_now_add = True)
class MainPage(MyHandler):
    def get(self):
        logging.info("********** MainPage GET **********")
        self.redirect('/blog')
class Newpost(MyHandler):
    def get(self):
        logging.info("*****newpost******")
        self.render("newpost.html")
    def post(self):
        subject = self.request.get('subject')
        content = self.request.get('content')
        error = "please enter both subject and content!"
        if not (content and subject):
            self.render("newpost.html", ph_subject = subject, ph_content = content, ph_error = error)
        if (content and subject):
            p = post()
            p.subject = subject
            p.content = content
            p.put()
            time.sleep(0.5)
            id = p.key().id()
            self.redirect("/blog/"+str(id))
class BlogFront(MyHandler):
    def get(self):
        make_salt()
        self.render_blog()
    def render_blog(self, subject = "", content = ""):
        template = JINJA_ENVIRONMENT.get_template('templates/post.html')
        posts = db.GqlQuery("SELECT * FROM post ORDER BY created DESC limit 10")
        params = {'post':"", "posts":posts}
        logging.info(posts)
        self.render("post.html", posts = posts)
class Posthandler(MyHandler):
    def get(self, post_id):
        template = JINJA_ENVIRONMENT.get_template('templates/post.html')
        id = int(post_id)
        logging.info(id)
        self.render("post.html", posts  = {post.get_by_id(id)})
application = webapp2.WSGIApplication([
    (r'/', MainPage),
    (r'/blog/?', BlogFront),
    (r'/blog/newpost/?', Newpost),
    (r'/blog/(\d+)', Posthandler)
], debug=True)