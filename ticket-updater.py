#!/usr/bin/python

# Author: Jon McCune <jonmccune@gmail.com>
# License: BSD-style
# Significant help from the example at:
# https://sourceforge.net/p/forge/documentation/API%20-%20Beta/
# Thanks also to the #sourceforge IRC channel

# This script will update the labels attached to existing issues in
# the SourceForge v2.0 API Beta.  This is mildly tricky because the API
# clobbers existing labels.  Our basic operation is thus to fetch the
# existing labels, extend the list with new ones of interest, and then
# assign the new labels.

import os
import oauth2 as oauth
import certifi
import urlparse
import webbrowser
import urllib
import string
import json

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

ACCESS_KEY=access_token['oauth_token']
ACCESS_SECRET=access_token['oauth_token_secret']

URL_BASE='http://sourceforge.net/rest/'

consumer = oauth.Consumer(CONSUMER_KEY, CONSUMER_SECRET)
access_token = oauth.Token(ACCESS_KEY, ACCESS_SECRET)
client = oauth.Client(consumer, access_token)
client.ca_certs = certifi.where()

# These are set manually right now.  The "smart" thing to do would
# probably be to iterate through all issues and decide what changes to
# make using a regexp or similar.  For example, in ticket-importer.py,
# we included "Redmine Project Name" in the "description" of a Ticket.
# One common scenario is that these are subprojects that should get
# labeled as such.
test_issues = [1,2,3]

for issue in test_issues:
  print "Processing issue " + str(issue)

  d = {}

  resp, content = client.request(URL_BASE + 'p/' + SF_PROJECT_NAME + '/tickets/' + str(issue), 'GET')
  if resp['status'] != '200':
    print "ERRONEOUS RESPONSE: "
    print resp
    raise Exception("Invalid response %s." % resp['status'])

  content_dict = json.loads(content)
  for label in content_dict['ticket']['labels']:
    print "Preserving existing label: " + label
    d['ticket_form.labels'] += ',' + label
  print d

  resp, content = client.request(URL_BASE + 'p/' + SF_PROJECT_NAME + '/tickets/' + str(issue) + '/save', 'POST', body=urllib.urlencode(d))

  if resp['status'] == '302':
    print "Ignoring redirect to the ticket: " + resp['location']
    print "Assuming Success"
  elif resp['status'] != '200':
    print "ERRONEOUS RESPONSE: "
    print resp
    raise Exception("Invalid response %s." % resp['status'])
  else:
    print "Success"


