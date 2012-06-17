#!/usr/bin/python

# Author: Jon McCune <jonmccune@gmail.com>
# License: BSD-style
# Significant help from the example at:
# https://sourceforge.net/p/forge/documentation/API%20-%20Beta/
# Thanks also to the #sourceforge IRC channel

# This script will process a .CSV file containing issues exported from
# Redmine 1.0.3 (have not tried with other versions; likely to work
# with little or no modification), and use the SourceForge API v2.0
# Beta to import the issues into a SourceForge project's issue
# tracker.

import os
import oauth2 as oauth
import certifi
import urlparse
import webbrowser
import urllib
import csv
import string

# Replace this with the name of your SourceForge project
SF_PROJECT_NAME = "test"

# You must go to https://sourceforge.net/auth/oauth/ in your web
# browser and register a new "Oauth Application".  The name and
# description can be arbotrary strings, and need not correspond to
# your sourceforge project name in any way.
CONSUMER_KEY = "<consumer KEY from registration>"
CONSUMER_SECRET = "<consumer SECRET from registration>"

# Should not need to change
REQUEST_TOKEN_URL = 'https://sourceforge.net/rest/oauth/request_token'
AUTHORIZE_URL = 'https://sourceforge.net/rest/oauth/authorize'
ACCESS_TOKEN_URL = 'https://sourceforge.net/rest/oauth/access_token'

consumer = oauth.Consumer(CONSUMER_KEY, CONSUMER_SECRET)
client = oauth.Client(consumer)
client.ca_certs = certifi.where()

# Step 1: Get a request token. This is a temporary token that is used for 
# having the user authorize an access token and to sign the request to obtain 
# said access token.

resp, content = client.request(REQUEST_TOKEN_URL, 'GET')
if resp['status'] != '200':
    raise Exception("Invalid response %s." % resp['status'])

request_token = dict(urlparse.parse_qsl(content))

print "Request Token:"
print "    - oauth_token        = %s" % request_token['oauth_token']
print "    - oauth_token_secret = %s" % request_token['oauth_token_secret']
print 

# Step 2: Redirect to the provider. Since this is a CLI script we do not 
# redirect. In a web application you would redirect the user to the URL
# below, specifying the additional parameter oauth_callback=<your callback URL>.

webbrowser.open("%s?oauth_token=%s" % (
        AUTHORIZE_URL, request_token['oauth_token']))

# Since we didn't specify a callback, the user must now enter the PIN displayed in 
# their browser.  If you had specified a callback URL, it would have been called with 
# oauth_token and oauth_verifier parameters, used below in obtaining an access token.
oauth_verifier = raw_input('What is the PIN? ')

# Step 3: Once the consumer has redirected the user back to the oauth_callback
# URL you can request the access token the user has approved. You use the 
# request token to sign this request. After this is done you throw away the
# request token and use the access token returned. You should store this 
# access token somewhere safe, like a database, for future use.
token = oauth.Token(request_token['oauth_token'],
    request_token['oauth_token_secret'])
token.set_verifier(oauth_verifier)
client = oauth.Client(consumer, token)
client.ca_certs = certifi.where()

resp, content = client.request(ACCESS_TOKEN_URL, "GET")
access_token = dict(urlparse.parse_qsl(content))

print "resp from client.request() to ACCESS_TOKEN_URL"
print resp
print "Access Token:"
print "    - oauth_token        = %s" % access_token['oauth_token']
print "    - oauth_token_secret = %s" % access_token['oauth_token_secret']
print
print "You may now access protected resources using the access tokens above." 
print

## From the original request (i.e., these worked in authorize.py)
#CONSUMER_KEY = ''
#CONSUMER_SECRET = ''

ACCESS_KEY=access_token['oauth_token']
ACCESS_SECRET=access_token['oauth_token_secret']

URL_BASE='http://sourceforge.net/rest/'

consumer = oauth.Consumer(CONSUMER_KEY, CONSUMER_SECRET)
access_token = oauth.Token(ACCESS_KEY, ACCESS_SECRET)
client = oauth.Client(consumer, access_token)
client.ca_certs = certifi.where()

# Format in Redmine-exported CSV (# denotes Issue Number):
# #, Status, Project, Tracker, Priority, Subject, Assigned to, Category, Target version, Author, Start Date, Due date, % Done, Estimated time, Parent task, Created, Updated, Description
Reader = csv.DictReader(open('export.csv', 'rb'))
#print Reader.fieldnames

# # Redmine fields we're going to drop: 
# # Due date, Estimated time, Parent task, Target version

for row in Reader:
  # The purpose of this is to catch any malformatted rows BEFORE we
  # start actually hitting the Sourceforge server, so as to avoid
  # partial import (e.g., non-UTF-8 characters can cause problems).
  for key, val in row.iteritems():
    print "Checking UTF-8 compatibility of field: " + key
    throw_away = val.decode('utf-8')

# NOTE: This second for loop will iterate zero times (i.e., nothing
# will happen) because the above for loop already iterated through the
# Reader object.  You want to comment-out the above for loop to send
# your issues "for real".  This is by design, to detect encoding
# failures early (i.e., before things become permanent on
# sourceforge).

# Map fields from Redmine schema to SourceForge schema
for row in Reader:
  #print row
  d = {} # dict adhering to SourceForge schema
  d['ticket_form.summary'] = row['Subject']

  if row['Assigned to'] == "Jon McCune":
    d['ticket_form.assigned_to'] = 'jonmccune'
  elif row['Assigned to'] == "Another Dev":
    d['ticket_form.assigned_to'] = 'anotherdev'
  else:
    d['ticket_form.assigned_to'] = ''

  if row['Category'] == "security":
    d['ticket_form.labels'] = 'security'
  # Add more translation here if needed for your project
  print "Labels prepared: " + d['ticket_form.labels']

  if row['Status'] == "Resolved":
    d['ticket_form.status'] = 'closed'
  else:
    d['ticket_form.status'] = 'open'

  d['ticket_form.description'] = string.join(["ISSUE IMPORTED FROM REDMINE",
                 "\r\nRedmine Issue Number: ",   row['#'],
                 "\r\nRedmine Project Name: ",   row['Project'],
                 "\r\nRedmine Tracker Name: ",   row['Tracker'],
                 "\r\nRedmine Priority: ",       row['Priority'],
                 "\r\nRedmine Author: ",         row['Author'],
                 "\r\nRedmine Start Date: ",     row['Start Date'],
                 "\r\nRedmine % Done: ",         row['% Done'],
                 "\r\nRedmine Created Date: ",   row['Created'],
                 "\r\nRedmine Updated Date: ",   row['Updated'],
                 "\r\nRedmine Description:\r\n", row['Description']], '')
  #print d['ticket_form.description']
  print "Attempting import with Redmine issue: " + row['#']

  resp, content = client.request(URL_BASE + 'p/' + SF_PROJECT_NAME + '/tickets/new', 'POST', body=urllib.urlencode(d))

  if resp['status'] == '302':
      print "Ignoring redirect to new ticket: " + resp['location']
      print "Assuming Success"
  elif resp['status'] != '200':
      print "ERRONEOUS RESPONSE: "
      print resp
      raise Exception("Invalid response %s." % resp['status'])
  else:
      print "Success"


