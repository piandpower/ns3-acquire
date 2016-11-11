import os, logging
from flask import Flask, request, render_template, jsonify
from flask_restplus import Api, Resource
from flask_sqlalchemy import SQLAlchemy
import requests
import lxml
from lxml import html
import BeautifulSoup
from BeautifulSoup import BeautifulSoup

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


@public_ns.route('/articles/<string:topic>')
class ArticleRoute(Resource):

    def get(self, topic):
        filtered = Article.query.filter_by(topic=topic).all()
        return [article.body for article in filtered]

@public_ns.route('/refresh')
class Refresh(Resource):

    def post(self):
        ''' refresh db '''
        return self.pullBodyOfURL("http://www.nytimes.com/2016/11/08/science/bats-wind-power-turbines.html");
         
    
    def topNArticles(self, topic, n): 
        urlString = "https://api.nytimes.com/svc/search/v2/articlesearch.json"
        #to do: add custom topic
        urlString = urlString + "?q=wind+power" + "&api-key=61f3909960f048909642771cedab3b76" + "&response-format=jsonp" + "&callback=svc_search_v2_articlesearch"
        data = '{"query":{"bool":{"must":[{"text":{"record.document":"SOME_JOURNAL"}},{"text":{"record.articleTitle":"farmers"}}],"must_not":[],"should":[]}},"from":0,"size":50,"sort":[],"facets":{}}'
        response = requests.get(urlString, data = data)
        docs = response.json()["docs"]
        
        for i in range(0, len(docs)):
            doc = docs[i];
            article_url = doc["web_url"]

    
    def pullBodyOfURL(self, url):
        page = requests.get(url)
        html_content = page.text
        soup = BeautifulSoup(html_content, 'lxml')
        storyList = soup.find_all('p', 'story-body-text story-content')
        storyText = " ".join(storyList) #join by space
        return storyText



        #tree = html.fromstring(page.content)
        #storyList = tree.xpath('//p[@class="story-body-text story-content"]/text()')
        #storyText = " ".join(storyList) #join by space
        #return storyText


