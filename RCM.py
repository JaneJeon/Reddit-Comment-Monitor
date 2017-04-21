"""
Reddit Comment Monitor - to delete (my) comments when shit goes south
if you happen to go against the reddit circlejerk without knowing, you'd better get out before they eat you alive
Currently, there are two conditions:
1. A comment reaches a score of zero.
2. A reply to my comment is rising, whereas my comment is declining (point = 2 or 3?)
Such deletion of comments prevents the scores from dropping and the comments from feeding the circlejerk
Once it's deleted, it notifies you via email

Setup: have settings.json on the same folder as the script, with reddit's client id (14 char) & secret (the longer one),
user agent name of your choice, username and password for your reddit account, your email address as sender,
receiver as your other email, and e-pw for your sender email.

In addition, you may have to adjust security settings on your sender email to allow 'less secure' apps to access it
"""

import praw
import prawcore
import json as jason
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

with open('settings.json') as params:
	login = jason.load(params)
	
result = False
while not result:
	try:
		reddit = praw.Reddit(client_id=login["client_id"],
							 client_secret=login["client_secret"],
							 user_agent=login["user_agent"],
							 password=login["password"],
							 username=login["username"])

		print(f'Monitoring: {str(reddit.user.me())} with {str(reddit.user.me().comment_karma)} comment karma\n')
		result = True
	except prawcore.exceptions.ResponseException:
		print('Probably a 503 error from Reddit API side')
		time.sleep(60)

def sendemail(body, karma, reason):
	# I'm using gmail for my sender email, but for other email services, look up its smtp address and TLS port number
	s = smtplib.SMTP('smtp.gmail.com', 587)
	s.starttls()
	s.login(login["sender"], login["e-pw"])

	message = f'Your comment has been removed since {reason}.\n Current karma: {karma}\n Comment: {body}'
	print(message)

	msg = MIMEMultipart()
	msg['From'] = login["sender"]
	msg['To'] = login["receiver"]
	msg['Subject'] = 'Reddit Comment Monitor: comment removed'

	msg.attach(MIMEText(message, 'plain'))

	s.send_message(msg)
	del msg

# test mail to make sure your settings are working: again, make sure your sender email is configured properly
# sendemail('test mail', 42, 'this is a test')

history = {}
watch = {}

while True:
	# check comments' status
	for comment in reddit.user.me().comments.new():
		if comment.score < 1:
			sendemail(comment.body, comment.score, 'Comment reached score of zero.')
			comment.delete()
		elif len(comment.replies.list()) > 0:
			for reply in comment.replies:
				# if there is a reply and your comment is vulnerable to being mass downvoted, monitor the score for
				# both the comment and the reply. Delete when your score drops by 2 and theirs increase by 2
				if comment.score > 4 and reply not in history:
					history.update({reply: comment.score})
					watch.update({reply: reply.score})

				if reply in watch and history[reply] < comment.score - 1 and watch[reply] > reply.score + 1:
					sendemail(comment.body + '\nReply: {reply.body}', comment.score,
							  'Reply is likely bringing animosity towards original comment.')
					comment.delete()
	time.sleep(120)

# resource for sending email: https://medium.freecodecamp.com/send-emails-using-code-4fcea9df63f
# reddit comment details: http://praw.readthedocs.io/en/latest/code_overview/models/comment.html