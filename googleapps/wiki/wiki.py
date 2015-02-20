import webapp2
import logging
import re
import cgi
import jinja2
import os
import random
import string
import hashlib
import hmac
import Cookie
import urllib2
import time
from datetime import datetime, timedelta
from google.appengine.api import memcache
from google.appengine.ext import db
from xml.dom import minidom

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

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")  # 3-20 characters (a-zA-Z0-9_-)
def valid_username(username):
   return USER_RE.match(username)

PASSWORD_RE = re.compile(r"^.{3,20}$")          # 3-20 characters (any)
def valid_password(username):
   return PASSWORD_RE.match(username)

EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
def valid_email(username):
   return EMAIL_RE.match(username)


class WikiHandler(webapp2.RequestHandler):
   def write(self, *items):
      self.response.write(" : ".join(items))

   def render_str(self, template, **params):
      tplt = JINJA_ENVIRONMENT.get_template('templates/'+template)
      return tplt.render(params)

   def render(self, template, **kw):
      self.write(self.render_str(template, **kw))

   def render_json(self, d):
      json_txt = json.dumps(d)
      self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
      self.write(json_txt)


## def make_salt():
##    return "".join(random.choice(string.letters) for x in xrange(5))
def make_salt():
   salt = ""
   for i in range(0, 5):
      salt += string.letters[random.randint(0,51)]
   return salt

def make_pw_hash(name, pw, salt=None):
   if not salt:
      salt = make_salt()
   return hashlib.sha256(name+pw+salt).hexdigest()+'|'+salt

def valid_pw(name, pw, h):
   salt = h.split('|')[1]
   return h == make_pw_hash(name, pw, salt)

SECRET="imsosecret"
def hash_str(s):
   return hmac.new(SECRET,s).hexdigest()

def make_secure_val(s):
   return s+'|'+hash_str(s)

def check_secure_val(h):
   val = h.split('|')[0]
   if (h == make_secure_val(val)):
      return val

def username_from_cookie(cookie):
  if cookie:
    user_id = check_secure_val(cookie)
    if user_id:
       user = MyUsers.get_by_id(int(user_id))
       return user.username

class MyUsers(db.Model):
   username   = db.StringProperty()
   pwhashsalt = db.StringProperty()
   email      = db.StringProperty()
   created    = db.DateTimeProperty(auto_now_add = True)
class Pages(db.Model):
    pagesub = db.StringProperty()
    pageinfo = db.TextProperty()
    created = db.DateTimeProperty(auto_now_add = True)
class Posthistory(db.Model):
    pagesub = db.StringProperty()
    username = db.StringProperty()
    pageinfo = db.TextProperty()
    created = db.DateTimeProperty(auto_now_add = True)
class Signup(WikiHandler):
   def get(self):
      logging.info("********** SignUp GET **********")
      self.render("signup.html")

   def post(self):
      user_username = self.request.get('username')
      user_password = self.request.get('password')
      user_verify   = self.request.get('verify')
      user_email    = self.request.get('email')

      user_username_v = valid_username(user_username)
      user_password_v = valid_password(user_password)
      user_verify_v   = valid_password(user_verify)
      user_email_v    = valid_email(user_email)

      username_error_msg = password_error_msg = verify_error_msg = email_error_msg = ""
      if not(user_username_v):
         username_error_msg = "That's not a valid username."

      if (user_password != user_verify):
         password_error_msg = "Passwords do not match."
      elif not(user_password_v):
         password_error_msg = "That's not a valid password."
         if (user_email != "") and not(user_email_v):
            email_error_msg = "That's not a valid email."

      userQuery = db.GqlQuery("SELECT * FROM MyUsers WHERE username = '%s'" % user_username)
      if not(userQuery.count() == 0 or userQuery.count() == 1):
         logging.info("***DBerr(signup) username = " + user_username + " (count = " + str(userQuery.count()) + ")" )
      user = userQuery.get() ## .get() returns Null if no results are found for the database query

      if user and user.username == user_username:
         user_username_v = False
         username_error_msg = "That user already exists."

      logging.info("DBG: The inputs="      \
                   +user_username + " " \
                   +user_password + " " \
                   +user_verify   + " " \
                   +user_email)

      logging.info("DBG: The valids="+str(bool(user_username_v))+" " \
                   +str(bool(user_password_v))+" " \
                   +str(bool(user_verify_v))  +" " \
                   +str(bool(user_email_v)))


      if not(user_username_v and user_password_v and user_verify_v and ((user_email == "") or user_email_v) and (user_password == user_verify)):
         template_values = {'error_username': username_error_msg,
                            'error_password': password_error_msg,
                            'error_verify'  : verify_error_msg,
                            'error_email'   : email_error_msg,
                            'username_value': user_username,
                            'email_value'   : user_email}
         self.render("signup.html", **template_values)
      else:
         pw_hash = make_pw_hash(user_username, user_password)
         u = MyUsers(username=user_username, pwhashsalt=pw_hash, email=user_email)
         u.put()
         id = u.key().id()
         self.response.headers.add_header('Set-Cookie', 'user_id=%s; max-age=60; Path=/' % make_secure_val(str(id)))
         ## self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/' % make_secure_val(str(id)))
         self.redirect("/")

class Login(WikiHandler):
   def get(self):
      logging.info("********** LogIn GET **********")
      self.render("login.html",error="")

   def post(self):
      logging.info("DBG: Login POST")
      user_username = self.request.get('username')
      user_password = self.request.get('password')

      users = db.GqlQuery("SELECT * FROM MyUsers ")
      users = list(users)    # save posts in a list to avoid doing DB queries whereever posts is used

      ## NOTE: make sure that username is a db.StringProperty() and not db.TextProperty
      userQuery = db.GqlQuery("SELECT * FROM MyUsers WHERE username = '%s'" % user_username)
      if userQuery.count() != 1:
         logging.info("***DBerr (login) username = " + user_username + " (count = " + str(userQuery.count()) + ")" )
      user = userQuery.get() ## .get() returns Null if no results are found for the database query

      if user and user.username == user_username and valid_pw(user_username,user_password,user.pwhashsalt):
         id = user.key().id()
         self.response.headers.add_header('Set-Cookie', 'user_id=%s; max-age=6000; Path=/' % make_secure_val(str(id)))
         self.redirect("/")
      else:
         self.render("login.html",error="Invalid login")

class Logout(WikiHandler):
   def get(self):
      self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')
      self.redirect(self.request.referer)
class EditPage(WikiHandler):
   def get(self, pagename):
      username = username_from_cookie(self.request.cookies.get('user_id',''))
      version = self.request.get('version','')
      mob = memcache.get(pagename)
      if username == None:
          self.redirect(pagename)
      if version:
          version = int(version)
          mob = Posthistory.get_by_id(version).pageinfo
      self.render("editpage.html",name=pagename, username = username, postin = mob)
   def post(self, pagename):
      username = username_from_cookie(self.request.cookies.get('user_id',''))
      pgname = pagename
      post = self.request.get("post")
      if post:
          p = Pages(pagesub = pagename, pageinfo = post)
          p.put()
          q = Posthistory(pagesub = pagename, pageinfo = post, username = username)
          q.put()
          time.sleep(.2)
          memcache.set(pagename,post)
          logging.info(pagename + "**********************")
          self.redirect(pagename)

class WikiPage(WikiHandler):
   def get(self, pagename):
      username = username_from_cookie(self.request.cookies.get('user_id',''))
      if memcache.get(pagename):
          logging.info("CACHE HIT $$$$$$$$$$$$$$$$$")
          cachesign = "*"
          post = memcache.get(pagename)

      else:
          logging.info("DB ACCESS")
          check = db.GqlQuery("SELECT * FROM Pages WHERE pagesub = :1", pagename).get()
          cachesign = ""
          if check:
              memcache.set(pagename, check.pageinfo)
              post = memcache.get(pagename)
          elif username:
              post = ""
              self.redirect("/_edit" + pagename)
          else:
              post = ""
              self.redirect("/")
      version = self.request.get('version','')
      if version:
          version = int(version)
          post = Posthistory.get_by_id(version).pageinfo
          cachesign = ""
      self.render("wikipage.html",name1 = pagename, username = username, edit = 1, post = post, caches = cachesign)

class MainPage(WikiHandler):
   def get(self):
      username = username_from_cookie(self.request.cookies.get('user_id',''))  ## None if user is not logged in
      self.render("main.html",username = username)
class Delete(WikiHandler):
    def get(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')
        db_info = MyUsers.all()
        db_info1 = Posthistory.all()
        db_info2 = Pages.all()
        for x in db_info:
            x.delete()
        for x in db_info1:
            x.delete()
        for x in db_info2:
            x.delete()
        self.redirect("/")
class Flush(WikiHandler):
    def get(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')
        memcache.flush_all()
        self.redirect("/")
class HistoryHandler(WikiHandler):
    def get(self, pagename):
        username = username_from_cookie(self.request.cookies.get('user_id',''))
        history = db.GqlQuery("SELECT * FROM Posthistory WHERE pagesub = :1 ORDER BY created DESC", pagename)
        for x in history:
            logging.info(x.username)
        self.render("history.html", username = username, name1 = pagename, edit = 1, history = history)

## (?: ) is a non-capturing group - see http://stackoverflow.com/questions/3512471/non-capturing-group
PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'  ## anything in parenthesis is passed as a parameter to WikiPage or EditPage get()

application = webapp2.WSGIApplication([
                               ('/', MainPage),
                               ('/delete', Delete),
                               ('/flush', Flush),
                               ('/signup', Signup),
                               ('/login', Login),
                               ('/logout', Logout),
                               ('/_edit' + PAGE_RE, EditPage),
                               ('/_history' + PAGE_RE, HistoryHandler),
                               (PAGE_RE, WikiPage)
                               ],
                              debug=True)
