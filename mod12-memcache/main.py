# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from flask import Flask, render_template, request
from google.appengine.api import memcache
from google.appengine.ext import ndb

app = Flask(__name__)
HOUR = 3600

class Visit(ndb.Model):
    'Visit entity registers visitor IP address & timestamp'
    visitor   = ndb.StringProperty()
    timestamp = ndb.DateTimeProperty(auto_now_add=True)

def store_visit(remote_addr, user_agent):
    'create new Visit entity in Datastore'
    Visit(visitor='{}: {}'.format(remote_addr, user_agent)).put()

def fetch_visits(limit):
    'get most recent visits'
    return (v.to_dict() for v in Visit.query().order(
            -Visit.timestamp).fetch(limit))

@app.route('/')
def root():
    'main application (GET) handler'
    # check for (hour-)cached visits
    ip_addr, usr_agt = request.remote_addr, request.user_agent
    visitor = '{}: {}'.format(ip_addr, usr_agt)
    visits = memcache.get('visits')

    # if cache empty or new visitor, register visit & run DB query
    if not visits or visits[0]['visitor'] != visitor:
        store_visit(ip_addr, usr_agt)
        visits = list(fetch_visits(10))
        memcache.set('visits', visits, HOUR)  # set() not add()

    return render_template('index.html', visits=visits)
