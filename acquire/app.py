import os, logging
from flask import Flask, request, render_template, jsonify
from flask_restplus import Api, Resource
from flask_sqlalchemy import SQLAlchemy
import requests

app = Flask(__name__)

ROOT_URL = os.getenv('ROOT_URL', 'localhost')
VERSION_NO = os.getenv('VERSION_NO', '1.0')
APP_NAME = os.getenv('APP_NAME', "Devil's Advocate")
DEBUG = os.getenv('DEBUG', False)
api = Api(app, version=VERSION_NO, title=APP_NAME)
public_ns = api.namespace('Public', description='Public methods')

DATABASE = os.getenv("DATABASE_URL", 'postgres://localhost')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE
db = SQLAlchemy(app)

class Article(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(1024))
    body = db.Column(db.String(65536))

    def __init__(self, topic, body):
        self.topic = topic
        self.body = body

    def __repr__(self):
        return self.topic + ' ' + str(len(self.body))


@public_ns.route('/articles')
class ArticleRoute(Resource):

    @public_ns.param('topic', 'the topic to look for')
    def get(topic):
        return [article.body for article in Article.query.filter_by(topic=topic)]

    def post(self):
        ''' refresh db '''
