from flask import Flask, request, jsonify, Response
from flask_cors import *
from ipdb import set_trace as debug


class Application(object):

    def __init__(self, Pyro, url_prefix=''):

        self.prefix = url_prefix
        self.app = app = Flask(__name__)
        valid_headers = ['Content-Type', 'Access-Control-Allow-Origin', '*']
        CORS(self.app)

        for DataClass in Pyro:
            available_routes = DataClass._routes()
            for route_name, data in available_routes.items():
                app.add_url_rule(data['route'], route_name, data['callback'],\
                        methods=data['methods'])

    def run(self):
        '''Launch the server.'''
        self.app.run()
