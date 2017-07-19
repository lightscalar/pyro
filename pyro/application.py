from flask import Flask, request, jsonify, Response
from flask_cors import *
from ipdb import set_trace as debug
from pyro.utils import name_to_class, singular


class Application(object):

    def __init__(self, Model, url_prefix=''):

        self.prefix = url_prefix
        self.app = Flask(__name__)
        valid_headers = ['Content-Type', 'Access-Control-Allow-Origin', '*']
        CORS(self.app)

        self.resources = Model.__subclasses__()
        for resource in self.resources:
            collection_name = resource._collection_name()
            resource_name = resource._name()

            # DEFINE LEVEL-1 ROUTES.
            # -----------------------

            # Define index: GET /users/
            route_name = '{:s}.index'.format(collection_name)
            url = '{:s}/{:s}'.format(self.prefix, collection_name)
            self.app.add_url_rule(url, route_name, resource.index_controller,
                    methods=['GET'])

            # Define show: GET /users/:id
            route_name = '{:s}.show'.format(collection_name)
            url = '{:s}/{:s}/<resource_id>'.format(self.prefix, resource_name)
            self.app.add_url_rule(url, route_name, resource.show_controller,\
                    methods=['GET'])

            # Define create: POST /users/
            route_name = '{:s}.create'.format(collection_name)
            url = '{:s}/{:s}'.format(self.prefix, collection_name)
            self.app.add_url_rule(url, route_name, resource.create_controller,
                    methods=['POST'])

            # Define delete: DELETE /user/<user_id>
            route_name = '{:s}.delete'.format(collection_name)
            url = '{:s}/{:s}/<resource_id>'.format(self.prefix, resource_name)
            self.app.add_url_rule(url, route_name, resource.delete_controller,\
                    methods=['DELETE'])

            # DEFINE LEVEL-2 ROUTES.
            # -----------------------
            if resource_name in Model.has_many_registry:
                children = Model.has_many_registry[resource_name]
                for subresource_collection in children:
                    subresource = name_to_class(singular(subresource_collection),\
                            self.resources)

                    # Define index: GET /user/:id/articles
                    route_name = '{:s}.{:s}.index'
                    url = '{:s}/{:s}/<resource_id>/{:s}'.format(self.prefix,\
                            resource_name, subresource_collection)
                    self.app.add_url_rule(url, route_name,\
                            subresource.index_controller, methods=['GET'])

    def run(self):
        '''Launch the server.'''
        self.app.run()
