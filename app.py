from bson import ObjectId
from pymongo import MongoClient
import certifi

ca = certifi.where()

client = MongoClient('mongodb://13.209.88.187', 27017, username="test", password="test")
db = client.dbsparta_mini

SECRET_KEY = 'SPARTA'

import jwt
import datetime
import hashlib

from flask import Flask, render_template, request, jsonify, redirect, url_for
app = Flask(__name__)


@app.route('/')
def move_reviews():
    return render_template('test3.html')

@app.route("/detail/<review_id>")
def move_detail(review_id):
    review = db.reviews.find_one({'_id': ObjectId(review_id)})
    toon = db.toons.find_one({'toon_id': review['toon_id']})
    return render_template('detail.html', post=review, toon=toon)


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)