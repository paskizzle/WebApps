import webapp2
import random

form = """
<form method="post" action= "/" >
<input name= "q" >
<input type= "submit" >
</form>
Previous Guess:</br>
"""
replay = """
</br> <button type="button" method="get" action="/"> Replay? </button>
"""
global randNum
randNum = random.randrange(1,100)

global guesses
guesses = 0
class GuessHandler(webapp2.RequestHandler):
    def get(self):
    	global guesses
    	#global randNum
    	#randNum = random.randrange(1,100)
        self.response.headers['Content-Type']='text/html'
        self.response.write(form)
        guesses = 0
    def post(self):
    	global guesses
    	global randNum
        self.response.headers['Content-Type']='text/html'
        q = self.request.get("q")
        try:
        	q = int(q)
        	self.response.write(form)
        except:
        	self.response.write("Please enter number")
        	self.response.write(form)
       	if q==randNum:
       		guesses = str(guesses)
        	self.response.write("You Won in " + guesses + " guesses")
        	#self.response.write(guesses)
        	randNum = random.randrange(1,100)
        	self.response.write(replay)
        	guesses = int(guesses)
        	guesses = 1
        elif q<randNum:
        	self.response.write(q)
        	self.response.write("</br> Guess Higher! Current Guesses: ")
        	guesses = guesses + 1
        	self.response.write(guesses)
        elif q>randNum:
        	self.response.write(q)
        	self.response.write("</br> Guess Lower! Current Guesses: ")
        	guesses = guesses + 1
        	self.response.write(guesses)

application = webapp2.WSGIApplication([
    ('/', GuessHandler),  
], debug=True)
