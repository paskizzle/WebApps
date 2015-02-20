import webapp2
import re
import cgi
import logging
#import jinja2
#import os

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'])
form = """<!DOCTYPE HTML>
<html>
  <head>
    <meta charset="utf-8">
    <title>Signup Page</title>
    <link rel="stylesheet" type="text/css" href="stylesheets/signup.css">
  </head>
  <body>
    <h1>Signup</h1>
    <form method="post">
      <table>
        <tr>
          <td class="label">Username</td>
          <td><input type="text" name="username" value="%(user)s"></td>
          <td class="error">%(erroruser)s</td>
        </tr>
        <tr>
          <td class="label">Password</td>
          <td><input type="password" name="password" value="%(password)s"></td>
          <td class="error">%(errorpassword)s</td>
        </tr>

        <tr>
          <td class="label">Verify Password</td>
          <td><input type="password" name="verify" value="%(verify)s"></td>
          <td class="error">%(errorverify)s</td>
        </tr>

        <tr>
          <td class="label">Email (optional)</td>
          <td><input type="text" name="email" value="">%(email)s</td>
          <td class="error">%(erroremail)s</td>
        </tr>
      </table>

      <input type="submit">

    </form>
  </body>
</html>"""
welcome = """<!DOCTYPE HTML>
<html>
  <head>
    <meta charset="utf-8">
    <title>Welcome</title>
  </head>
  <body>
    <h1>Welcome Cholo</h1>
    <img src="images/gangstazz.jpg"></br>
  </body>
</html>"""
USER_RE = re.compile(r"^[a-z,A-Z,0-9,_,-]{3,20}$")
PASSWORD_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r"[\w._%-]+@[\w.-]+\.[a-zA-Z]{2,4}")
def escape_html(s):
    return cgi.escape(s, quote = True)
def valid_user(username):
    return USER_RE.match(username)
def valid_password(password1, password2):
    if password1 == password2:
        logging.info("***PASWORDS MATCH***")
        if PASSWORD_RE.match(password1) and PASSWORD_RE.match(password2):
            logging.info("**********passowords legit**********")
            return True
        else:
            logging.info("*************passwords not legit**********")
            return False
    else:
        return 3
        logging.info("****************PASWORDS do not match**********")
def valid_email(email):
    if EMAIL_RE.match(email):
        return True
    elif len(email) == 0:
        logging.info("*******no email***********")
        return True
    else:
        return False
class Mainpage(webapp2.RequestHandler):

    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        self.write_form("","","","")
    def post(self):
        global epass
        global everify
        global euser
        global eemail
        eemail = ""
        euser = ""
        everify = ""
        epass = ""
        user = self.request.get("username")
        email = self.request.get("email")
        password = escape_html(self.request.get("password"))
        verify = escape_html(self.request.get("verify"))
        v_valid_user = valid_user(escape_html(self.request.get("username")))
        v_valid_password = valid_password(password, verify)
        v_valid_email = valid_email(escape_html(self.request.get("email")))
        if not (v_valid_user and v_valid_password and v_valid_email) or (v_valid_user and v_valid_password == 3 and v_valid_email):
            if v_valid_user == None:
                euser = "Please enter a valid Username (a-z,A-Z,0-9,_,-) length (3-20)"
                logging.info(v_valid_user)
            else:
                euser = ""
                logging.info(v_valid_user)
            if not v_valid_password:
                logging.info(v_valid_password)
                epass = "Please enter a valid Passsword (3-20)"
            else:
                if v_valid_password == 3:
                    everify = "Please make sure passwords match"
            if v_valid_email == False:
                eemail = "Please enter a valid email or leave blank"
            else:
                eemail = ""
            self.write_form(euser, epass, everify, eemail,user,email)
        else:
            self.redirect("/success")
    def write_form(self, erroruser="", errorpassword="", errorverify="", erroremail="", user="",email=""):
        self.response.write(form % {"erroruser":erroruser, "errorpassword":errorpassword, "errorverify":errorverify, "erroremail":erroremail, "user":user, "email":email})    
class SuccessHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write(welcome)
application = webapp2.WSGIApplication([
    ('/', Mainpage),
    ('/success', SuccessHandler),  
], debug=True)