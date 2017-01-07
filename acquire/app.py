#!/usr/bin/env python3
import os, logging
from flask import Flask, request, render_template, jsonify
from flask_restplus import Api, Resource
from flask_sqlalchemy import SQLAlchemy
import requests
import lxml
from lxml import html
from bs4 import BeautifulSoup
from theguardian import theguardian_tag
from theguardian import theguardian_content
import sys

app = Flask(__name__)

ROOT_URL = os.getenv('ROOT_URL', 'localhost')
VERSION_NO = os.getenv('VERSION_NO', '1.0')
APP_NAME = os.getenv('APP_NAME', "Devil's Advocate")
GUAR_KEY = os.getenv('GUAR_KEY')
DEBUG = os.getenv('DEBUG', False)
api = Api(app, version=VERSION_NO, title=APP_NAME)
public_ns = api.namespace('Public', description='Public methods')

DATABASE = os.getenv("DATABASE_URL", 'postgres://localhost')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE
db = SQLAlchemy(app)

class Article(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(256))
    topic = db.Column(db.String(1024))
    body = db.Column(db.String(65536))

    def __init__(self, topic, body, url):
        self.topic = topic
        self.body = body
        self.url = url

    def __repr__(self):
        return self.topic + ' ' + self.url


@public_ns.route('/articles/<string:topic>')
class ArticleRoute(Resource):

    def get(self, topic):
        filtered = Article.query.filter_by(topic=topic).all()
        return [article.body for article in filtered]

@public_ns.route('/refresh')
class Refresh(Resource):

    def post(self):
        ''' refresh db '''
        return self.getGuardianArticles("wind power")
        # return self.topNArticles('wind power', 10)
        # return self.pullBodyOfURL("http://www.nytimes.com/2016/11/08/science/bats-wind-power-turbines.html");
         
    
    def topNArticles(self, topic, n): 
        urlString = "https://api.nytimes.com/svc/search/v2/articlesearch.json"
        urlString = urlString + "?q=" + topic.replace(' ', '+') + "&api-key=61f3909960f048909642771cedab3b76" + "&response-format=jsonp" + "&callback=svc_search_v2_articlesearch"
        # data = '{"query":{"bool":{"must":[{"text":{"record.document":"SOME_JOURNAL"}},{"text":{"record.articleTitle":"farmers"}}],"must_not":[],"should":[]}},"from":0,"size":50,"sort":[],"facets":{}}'
        response = requests.get(urlString)
        docs = response.json()['response']['docs']
        articles = []
        for doc in docs:
            article_url = doc["web_url"]
            text = self.pullBodyOfURL(article_url)
            new_article = Article(topic, text, article_url)
            if not Article.query.filter_by(url=article_url).first():
                db.session.add(new_article)
        db.session.commit()
        return [article.url for article in Article.query.filter_by(topic=topic).limit(n)]
    
    def get_contents(self, tag, arr):
        if len(tag.contents):
            for subtag in tag.contents:
                if subtag.string:
                    arr.append(subtag.string)
                elif len(subtag.contents):
                    self.get_contents(subtag, arr)
        else:
            arr.append(tag.string)

    def pullBodyOfURL(self, url):
        page = requests.get(url)
        html_content = page.text
        soup = BeautifulSoup(html_content, 'lxml')
        tags = [tag for tag in soup.find_all('p', 'story-body-text story-content')]
        strings = []
        for tag in tags:
            self.get_contents(tag, strings)
        storyText = " ".join(strings)
        return storyText

    def getGuardianArticles(self, topic):
        header = {
                "q": topic,
                "type": "article"
            }
        content_articles = theguardian_content.Content(GUAR_KEY, **header)
        content_articles_data = content_articles.get_content_response()
        results = content_articles.get_results(content_articles_data)

        webTitles = [result["webUrl"] for result in results]
        return ("{title}" .format(title=webTitles))