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
NYT_KEY = os.getenv('NYT_KEY')
BING_KEY = os.getenv('BING_KEY')
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
    source = db.Column(db.String(1024))

    def __init__(self, topic, body, url, source):
        self.topic = topic
        self.body = body
        self.url = url
        self.source = source

    def __repr__(self):
        return self.topic + ' ' + self.url


@public_ns.route('/articles/<string:topic>')
class ArticleRoute(Resource):

    def get(self, topic):
        filtered = Article.query.filter_by(topic=topic).all()
        return [{'article': article.body, 'url': article.url, 'source': article.source} for article in filtered]

@public_ns.route('/refresh')
class Refresh(Resource):

    def post(self):
        ''' refresh db '''
        #return self.getGuardianArticles("wind power")
        return self.topNArticles('wind power', 20)
        #return self.pullBodyOfURL("http://www.nytimes.com/2016/11/08/science/bats-wind-power-turbines.html");
         


    
    def topNArticles(self, topic, n): 
        NYT_urls = self.getNYTArticles(topic)
        GUAR_urls = self.getGuardianArticles(topic)

        NYT_bodies = self.pullBodyFromURLSet(NYT_urls, "new york times")
        GUAR_bodies = self.pullBodyFromURLSet(GUAR_urls, "guardian")
        
        urls = NYT_urls + GUAR_urls
        bodies = NYT_bodies + GUAR_bodies
        sources = self.createSourceArray(len(NYT_urls), "New York Times") + self.createSourceArray(len(GUAR_urls), "The Guardian")

        print(sources)

        for (article_url, body, source) in zip(urls, bodies, sources):
            new_article = Article(topic, body, article_url, source)
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

    def pullBodyOfURL(self, url, source):
        page = requests.get(url)
        html_content = page.text
        soup = BeautifulSoup(html_content, 'lxml')
        tags = [tag for tag in soup.find_all('p', self.classTagFromSource(source))]
        strings = []
        for tag in tags:
            self.get_contents(tag, strings)
        storyText = " ".join(strings)
        return storyText

    def classTagFromSource(self, source):
        if source == "new york times":
            return 'story-body-text story-content'
        elif source == "guardian":
            return 'content__article-body from-content-api js-article__body'

    def getGuardianArticles(self, topic):
        header = {
                "q": topic,
                "type": "article"
            }
        content_articles = theguardian_content.Content(GUAR_KEY, **header)
        content_articles_data = content_articles.get_content_response()
        results = content_articles.get_results(content_articles_data)

        webUrls = [result["webUrl"] for result in results]
        return webUrls

    def getNYTArticles(self, topic):
        urlString = "https://api.nytimes.com/svc/search/v2/articlesearch.json"
        urlString = urlString + "?q=" + topic.replace(' ', '+') + "&api-key=" + NYT_KEY + "&response-format=jsonp" + "&callback=svc_search_v2_articlesearch"
        
        response = requests.get(urlString)
        docs = response.json()['response']['docs']
        webUrls = [doc["web_url"] for doc in docs]
        return webUrls

    def pullBodyFromURLSet(self, urlSet, source):
        bodyList = [self.pullBodyOfURL(url, source) for url in urlSet]
        return bodyList
        
        
    def getBingArticles(self, topic):
        headers = {
                # Request headers
                'Ocp-Apim-Subscription-Key': BING_KEY,
        }

        params = urllib.parse.urlencode({
                # Request parameters
                'q': topic,
                'count': '10',
                'offset': '0',
                'mkt': 'en-us',
        })

        requests.get("https://api.cognitive.microsoft.com/bing/v5.0/news/search", headers=headers, params=params)

    def createSourceArray(self, size, source):
        sourceArr = []

        for i in range(0, size):
            sourceArr.append(source)
            
        return sourceArr