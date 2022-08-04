from pymongo import MongoClient
import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'SPARTA'

client = MongoClient('mongodb+srv://sparta:woowa@cluster0.v2xvyfm.mongodb.net/Cluster0?retryWrites=true&w=majority')
db = client.dbsparta_plus_week4

# 토큰 유효 시간
@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

        return render_template('index.html')
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)

@bp.route('/logout/')
def logout():
    session.clear()
    return redirect(url_for('login.html'))

@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})

    if result is not None:
        payload = {
            'id': username_receive,
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,  # 아이디
        "password": password_hash,  # 비밀번호
        "profile_name": username_receive,  # 프로필 이름 기본값은 아이디
        "profile_pic": "",  # 프로필 사진 파일 이름
        "profile_pic_real": "profile_pics/profile_placeholder.png",  # 프로필 사진 기본 이미지
        "profile_info": ""  # 프로필 한 마디
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})


@app.route('/sign_up/check_dup', methods=['POST'])
    #중복확인
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})

#리뷰 등록
@app.route("/sub", methods=["POST"])
def review_post():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    except:
        payload=None
    title_receive = request.form['title_give']
    star_receive = request.form['star_give']
    comment_receive = request.form['comment_give']
    date_receive = request.form["date_give"]
    toon_id = request.form["toonId_give"]

    doc = {
        'id': payload['id'],
        'title':title_receive,
        'star':star_receive,
        'review':comment_receive,
        "date": date_receive,
        "toon_id":toon_id
    }

    db.reviews.insert_one(doc)

    return jsonify({"result": "success","msg":"저장 완료!"})

#리뷰작성 페이지 속 이미지
@app.route('/sub/<title>')
def sub(title):
    webtoon_list = db.toons.find_one({'title':title})
    return render_template('sub.html', WT=webtoon_list)

#웹툰 등록 페이지
@app.route('/title')
def title():
   return render_template('title.html')

#웹툰 등록 페이지 url 중복확인
@app.route('/Webtoon/check_dup', methods=['POST'])
def web_check_dup():
    url_receive = request.form['url_give']
    exists = bool(db.toons.find_one({"url": url_receive}))
    return jsonify({'result': 'success', 'exists': exists})

#웹툰 등록
@app.route("/Webtoon/title", methods=["POST"])
def webtoon_post():
    url_receive = request.form['url_give']
    title_receive = request.form['title_give']
    serialization_receive = request.form['serialization_give']
    date_receive = request.form["date_give"]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
    data = requests.get(url_receive, headers=headers)

    soup = BeautifulSoup(data.text, 'html.parser')

    og_image = soup.select_one('meta[property="og:image"]')

    image = og_image['content']


    doc = {
        "url":url_receive,
        "img": image,
        "title": title_receive,
        "ser": serialization_receive,
        "date": date_receive
    }

    db.toons.insert_one(doc)

    return jsonify({'result': 'success','msg':'저장 완료'})


#웹툰 리뷰 상세페이지 열기
@app.route("/detail/<review_id>")
def move_detail(review_id):
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])['id']
    except:
        payload=""
    review = db.reviews.find_one({'_id': ObjectId(review_id)})
    toon = db.toons.find_one({'title': review['toon_id']})
    return render_template('detail.html', post=review, toon=toon, user_id=payload)

#웹툰 리뷰 삭제하기
@app.route("/delete/<review_id>")
def delete(review_id):
    toon_id = db.reviews.find_one({'_id': ObjectId(review_id)})['toon_id']
    db.reviews.delete_one({'_id': ObjectId(review_id)})
    return redirect(url_for( 'review',title = toon_id))





if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
    
    
