# coding: utf-8
from .. import app
from . import main
from ..models import Movie, Article, Photo, Anime, Course, Startup, Notice
# from ..models import W_Movie, W_Article, W_Photo, W_Anime, W_Course, W_Startup
from app import db, r1
from flask import render_template, request, redirect, url_for, send_from_directory, flash, session, jsonify
from geetest import GeetestLib
# from werkzeug import secure_filename
import time
import os
import random
from qiniu import Auth, put_file, etag
import qiniu.config


captcha_id = app.config['CAPTCHA_ID']
private_key = app.config['PRIVATE_KEY']
pic_appendix = app.config['PIC_APPENDIX']
access_key = app.config['ACCESS_KEY']
secret_key = app.config['SECRET_KEY']
url = app.config['URL']
bucket_name = app.config['QINIUNAME']
q = qiniu.Auth(access_key, secret_key)


def qiniu_upload(key, localfile):
    token = q.upload_token(bucket_name, key, 3600)

    ret, info = qiniu.put_file(token, key, localfile)

    if ret:
        return '{0}{1}'.format(url, ret['key'])
    else:
        raise UploadError('上传失败，请重试')

def allowed_file(filename):
    if '.' in filename and \
            filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']:
                return True

@main.route('/')
def index():
    movies = Movie.query.filter_by(is_confirm=True).all()
    courses = Course.query.filter_by(is_confirm=True).all()
    animes = Anime.query.filter_by(is_confirm=True).all()
    photos = Photo.query.filter_by(is_confirm=True).all()
#    for photo in photos:
#        mystr = photo.photo_url.split(';')[0]
#        i = mystr.find('com')
#        tstr = mystr[:i + 3] + '/' + mystr[i + 3:]
#        photo.img_url = tstr 
#        db.session.add(photo)
#        db.session.commit()
    startups = Startup.query.filter_by(is_confirm=True).all()
    for eachPhoto in photos:
        eachPhoto.first_photo = eachPhoto.video_url.split(' ')[0]
    articles = Article.query.filter_by(is_confirm=True).all()
    notices = Notice.query.filter_by(is_confirm=True).all()
    return render_template(
            '/main/index.html',
            movies=movies[:4],
            courses=courses[:4],
            animes=animes[:4],
            photos=photos[:4],
            articles=articles[:4],
            notices=notices[:4],
            startups=startups[:4]
            )

@main.route('/fix/fix/course/', methods=['POST'])
def fix_fix():
    id = request.get_json().get('id')
    img_url = request.get_json().get('img_url')
    try:
        ppclass = Course.query.filter_by(id=id).first()
        ppclass.img_url = img_url
        db.session.add(ppclass)
        db.session.commit()
    except:
        return jsonify({}), 500
    return jsonify({}), 200

@main.route('/fix/fix/movie/', methods=["POST"])
def fix_movie():
    id = request.get_json().get('id')
    img_url = request.get_json().get('img_url')
    try:
        ppclass = Movie.query.filter_by(id=id).first()
        ppclass.img_url = img_url
        db.session.add(ppclass)
        db.session.commit()
    except:
        return jsonify({}), 500
    return jsonify({}), 200

@main.route('/fix/fix/anime/', methods=['POST'])
def fix_anime():
    id = request.get_json().get('id')
    img_url = request.get_json().get('img_url')
    try:
        ppclass = Anime.query.filter_by(id=id).first()
        ppclass.img_url = img_url
        db.session.add(ppclass)
        db.session.commit()
    except:
        return jsonify({}), 500
    return jsonify({}), 200

@main.route('/fix/fix/startup/', methods=['POST'])
def fix_starup():
    id = request.get_json().get('id')
    img_url = request.get_json().get('img_url')
    try:
        ppclass = Startup.query.filter_by(id=id).first()
        ppclass.img_url = img_url
        db.session.add(ppclass)
        db.session.commit()
    except:
        return jsonify({}), 500
    return jsonify({}), 200

@main.route('/upgrade/photo/', methods=['GET'])
def upgrade_photo():
    photos = Photo.query.filter_by(is_confirm=True).all()
    try:
        for eachPhoto in photos:
            Pos = '/upload/photo/' + eachPhoto.upload_name.split('.')[0]
            #print(Pos)
            for (dirpath, dirnames, files) in os.walk(Pos):
                for filename in files:
                    localfile = os.path.join(dirpath, filename)
                    qiniukey = str(time.time()).split('.')[0]+ '.' + filename.split('.')[1]
                    if filename.split('.')[1] in ['jpg', 'jpeg', 'png', 'gif']:
                        print(localfile)
                        res = qiniu_upload(qiniukey, localfile)
                        eachPhoto.photo_url = eachPhoto.photo_url + res + ';'
                    else:
                        continue
            db.session.add(eachPhoto)
            db.session.commit()
        return jsonify({}), 200
    except:
        return jsonify({}), 500

@main.route('/upgrade/article/', methods=['GET'])
def upgrade_article():
    articles = Article.query.filter_by(is_confirm=True).all()
    try:
        for eachArticle in  articles:
            Pos = '/upload/article/' + eachArticle.upload_name.split('.')[0]
            for (dirpath, dirnames, files) in os.walk(Pos):
                for filename in files:
                    localfiles = os.path.join(dirpath, filename)
                    qiniukey = str(ime.time()).split('.')[0] + '.'+filename.split('.')[1]
                    if filename.split('.')[1] == 'pdf':
                        res = qiniu_upload(qiniukey, localfiles)
                        i = res.find('com')
                        arurl = res[:i + 3] + '/' + res[i + 3:]
                        eachArticle.article_url = arurl
#                        print(eachArticle.article_url)
                        time.sleep(1)
                    else:
                        continue
            db.session.add(eachArticle)
            db.session.commit()
        return jsonify({}), 200
    except:
        return jsonify({}), 500

@main.route('/upload/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        tag = request.form.get('upload-class-choice')
        uptime = str(time.time())
        file_name = uptime.rsplit('.', 1)[0] + uptime.rsplit('.', 1)[1]
        description = request.form.get('description') or ''

        if not tag:
            flash("请选择类型!")
            return redirect(url_for('main.upload_file'))

        if not file_name:
            flash("请填写文件名!")
            return redirect(url_for('main.upload_file'))

        author_name = request.form.get('author_name')
        if not author_name:
            flash("请填写文件名!")
            return redirect(url_for('main.upload_file'))

        img_url = request.form.get('img_url')
        if not img_url and tag is not 'article':
            imgs = ["http://p688ihx0v.bkt.clouddn.com/c.png", "http://p688ihx0v.bkt.clouddn.com/n.png", "http://p688ihx0v.bkt.clouddn.com/u.png"]
            import random
            img_url = imgs[random.randint(0, len(imgs)-1)]

        upload_url = request.form.get('upload_url')

        if not upload_url:
            file = request.files.getlist("file")
#            print (type(file))
#            print(file[0].filename)
            if allowed_file(file[0].filename):
                filename = file_name + '.' + file[0].filename.rsplit('.', 1)[1]
            else:
                flash("请添加文件或链接!")
                return redirect(url_for('main.upload_file'))
        else:
            filename = time.strftime("%a %b %d %H:%M:%S %Y",time.localtime()) + ' ' + file_name

        if tag == 'movie':
            UPLOAD_FOLDER = os.path.join(app.config['BUPLOAD_FOLDER'], 'movie/')
            if not upload_url:
                file[0].save(os.path.join(UPLOAD_FOLDER, filename).encode('utf-8').strip())
            else:
                UPLOAD_FOLDER = 'no'
            item = Movie(
                    upload_name=filename,
                    present_name=request.form.get('file_name'),
                    author_name=author_name,
                    description=description,
                    upload_url=UPLOAD_FOLDER + filename,
                    video_url=upload_url,
                    img_url = img_url,
                    a_time=(time.strftime("%a %b %d %H:%M:%S %Y",time.localtime()))[:10]
                    )

        elif tag == 'article':
            if not upload_url:
                UPLOAD_FOLDER = os.path.join(app.config['BUPLOAD_FOLDER'], 'article/')
                file[0].save(os.path.join(UPLOAD_FOLDER, filename).encode('utf-8').strip())
                localfile = '/upload/article/'+filename
                qiniukey = filename
                mystr = qiniu_upload(qiniukey, localfile)
                i = mystr.find('com')
                mystr = mystr[:i+ 3] + '/' + mystr[i+3:]
                article_url = mystr
            else:
                UPLOAD_FOLDER = 'no'
            item = Article(
                    upload_name=filename,
                    present_name=request.form.get('file_name'),
                    author_name=author_name,
                    description=description,
                    upload_url=UPLOAD_FOLDER + filename,
                    video_url=upload_url,
                    img_url = img_url,
                    article_url=article_url,
                    a_time=(time.strftime("%a %b %d %H:%M:%S %Y",time.localtime()))[:10]
                    )

        elif tag == 'photo':
            if not upload_url:
                UPLOAD_FOLDER = os.path.join(app.config['BUPLOAD_FOLDER'], 'photo/')
                # file.save(os.path.join(UPLOAD_FOLDER, filename))
                i = 0
                photo_url = ''
                for eachfile in file:
#                    qiniukey = str(time.time()).split('.')[0] + str(i) + '.'+filename.split('.')[1]
                    thisfilename = str(time.time()).split('.')[0] + str(i) +'.'+ filename.split('.')[1]
                    qiniukey = thisfilename
                    eachfile.save(os.path.join(UPLOAD_FOLDER, thisfilename).encode('utf-8').strip())
                    localfile = '/upload/photo/'+thisfilename
                    photo_url += (qiniu_upload(qiniukey, localfile) + ';')
                    i += 1
 #                   print(photo_url)
            else:
                UPLOAD_FOLDER = 'no'
            item = Photo(
                    upload_name=filename,
                    present_name=request.form.get('file_name'),
                    author_name=author_name,
                    description=description,
                    upload_url=UPLOAD_FOLDER + filename,
                    video_url=upload_url,
                    img_url = img_url,
                    photo_url = photo_url,
                    a_time=(time.strftime("%a %b %d %H:%M:%S %Y",time.localtime()))[:10]
                    )
        elif tag == 'anime':
            if not upload_url:
                UPLOAD_FOLDER = os.path.join(app.config['BUPLOAD_FOLDER'], 'anime/')
                file[0].save(os.path.join(UPLOAD_FOLDER, filename).encode('utf-8').strip())
            else:
                UPLOAD_FOLDER = 'no'
            item = Anime(
                    upload_name=filename,
                    present_name=request.form.get('file_name'),
                    author_name=author_name,
                    description=description,
                    upload_url=UPLOAD_FOLDER + filename,
                    video_url=upload_url,
                    img_url = img_url,
                    a_time=(time.strftime("%a %b %d %H:%M:%S %Y",time.localtime()))[:10]
                    )

        elif tag == 'course':
            if not upload_url:
                UPLOAD_FOLDER = os.path.join(app.config['BUPLOAD_FOLDER'], 'course/')
                file[0].save(os.path.join(UPLOAD_FOLDER, filename).encode('utf-8').strip())
            else:
                UPLOAD_FOLDER = 'no'
            item = Course(
                    upload_name=filename,
                    present_name=request.form.get('file_name'),
                    author_name=author_name,
                    description=description,
                    upload_url=UPLOAD_FOLDER + filename,
                    video_url=upload_url,
                    img_url = img_url,
                    a_time=(time.strftime("%a %b %d %H:%M:%S %Y",time.localtime()))[:10]
                    )

        elif tag == 'startup':
            if not upload_url:
                UPLOAD_FOLDER = os.path.join(app.config['BUPLOAD_FOLDER'], 'startup/')
                file[0].save(os.path.join(UPLOAD_FOLDER, filename).encode('utf-8').strip())
            else:
                UPLOAD_FOLDER = 'no'
            item = Startup(
                    upload_name=filename,
                    present_name=request.form.get('file_name'),
                    author_name=author_name,
                    description=description,
                    upload_url=UPLOAD_FOLDER + filename,
                    video_url=upload_url,
                    img_url = img_url,
                    a_time=(time.strftime("%a %b %d %H:%M:%S %Y",time.localtime()))[:10]
                    )

        db.session.add(item)
        db.session.commit()
        flash("文件已上传!正在审核中···")
        return redirect(url_for('main.upload_file'))
        print(filename)
    return render_template('/main/upload.html')


@main.route('/notices/')
def notices():
    notices = Notice.query.filter_by(is_confirm=True).all()
    return render_template('/main/notices.html', notices=notices)


@main.route('/movies/')
def movies():
    movies = Movie.query.filter_by(is_confirm=True).all()
    return render_template('main/movies.html', movies=movies)


@main.route('/animes/')
def animes():
    animes = Anime.query.filter_by(is_confirm=True).all()
    return render_template('main/animes.html', animes=animes)


@main.route('/courses/')
def courses():
    courses = Course.query.filter_by(is_confirm=True).all()
    return render_template('main/courses.html', courses=courses)


@main.route('/photos/')
def photos():
    photos = Photo.query.filter_by(is_confirm=True).all()
    for eachPhoto in photos:
        eachPhoto.first_photo = eachPhoto.upload_url.split(' ')[0]
    return render_template('main/photos.html', photos=photos)


@main.route('/articles/')
def articles():
    articles = Article.query.filter_by(is_confirm=True).all()
    return render_template('main/articles.html', articles=articles)


@main.route('/startups/')
def startups():
    startups = Startup.query.filter_by(is_confirm=True).all()
    return render_template('main/startups.html', startups=startups)


@main.route('/rank/')
def rank():
    movies = Movie.query.filter_by(is_confirm=True).all()
    articles = Article.query.filter_by(is_confirm=True).all()
    animes = Anime.query.filter_by(is_confirm=True).all()
    photos = Photo.query.filter_by(is_confirm=True).all()
    courses = Course.query.filter_by(is_confirm=True).all()
    startups = Startup.query.filter_by(is_confirm=True).all()
    sorted_movies = sorted(movies, key=lambda movie: movie.liked_count, reverse=True)
    sorted_animes = sorted(animes, key=lambda anime: anime.liked_count, reverse=True)
    sorted_articles = sorted(articles, key=lambda article: article.liked_count, reverse=True)
    sorted_photos = sorted(photos, key=lambda photo: photo.liked_count, reverse=True)
    sorted_courses = sorted(courses, key=lambda course: course.liked_count, reverse=True)
    sorted_startups = sorted(startups, key=lambda startup: startup.liked_count, reverse=True)
    return render_template(
            'main/rank.html',
            movies=sorted_movies[:20],
            animes=sorted_animes[:20],
            photos=sorted_photos[:20],
            articles=sorted_articles[:20],
            courses=sorted_courses[:20],
            startups=sorted_startups[:20]
            )


@main.route('/movie/<int:id>/', methods=["GET", "POST"])
def get_movie(id):
    movie = Movie.query.get_or_404(id)
    if 'vote' in session.keys():
        if session['vote'] == 1:
            ip = request.remote_addr
            if r1.get(ip):
                flash("每天只能投一次票!")
            else:
                movie.liked_count += 1
                db.session.add(movie)
                db.session.commit()
                flash("投票成功")
                r1.set(ip, ip)
            session['vote'] = 0
            return redirect(url_for('main.get_movie', id=movie.id))
    else:
        session['vote'] = 0
    return render_template('main/movie.html', movie=movie)


@main.route('/article/<int:id>/', methods=["GET", "POST"])
def get_article(id):
    article = Article.query.get_or_404(id)
    if 'vote' in session.keys():
        if session['vote'] == 1:
            ip = request.remote_addr
            if r2.get(ip):
                flash("每天只能投一次票!")
            else:
                article.liked_count += 1
                db.session.add(article)
                db.session.commit()
                flash("投票成功")
                r2.set(ip, ip)
            session['vote'] = 0
            return redirect(url_for('main.get_article', id=article.id))
    else:
        session['vote'] = 0
    return render_template('main/article.html', article=article)


@main.route('/anime/<int:id>/', methods=["GET", "POST"])
def get_anime(id):
    anime = Anime.query.filter_by(is_confirm=True,id=id).first_or_404()
    anime_urls = anime.video_url.split(' ')

    # 根据文件后缀判断是图片还是视频
    if anime_urls[0].split('.')[-1] in pic_appendix or len(anime_urls[0].split('.')[-1]) > 5:
        flag = 'anime'
    else:
        flag = 'video'

    if 'vote' in session.keys():
        if session['vote'] == 1:
            ip = request.remote_addr
            if r3.get(ip):
                flash("每天只能投一次票!")
            else:
                anime.liked_count += 1
                db.session.add(anime)
                db.session.commit()
                flash("投票成功")
                r3.set(ip, ip)
            session['vote'] = 0
            return redirect(url_for('main.get_anime', id=anime.id))
    else:
        session['vote'] = 0
    return render_template('main/anime.html', anime=anime, flag=flag, anime_urls=anime_urls)


@main.route('/course/<int:id>/', methods=["GET", "POST"])
def get_course(id):
    course = Course.query.get_or_404(id)
    if 'vote' in session.keys():
        if session['vote'] == 1:
            ip = request.remote_addr
            if r4.get(ip):
                flash("每天只能投一次票!")
            else:
                course.liked_count += 1
                db.session.add(course)
                db.session.commit()
                flash("投票成功")
                r4.set(ip, ip)
            session['vote'] = 0
            return redirect(url_for('main.get_course', id=course.id))
    else:
        session['vote'] = 0
    return render_template('main/course.html', course=course)


@main.route('/photo/<int:id>/', methods=["GET", "POST"])
def get_photo(id):
    photo = Photo.query.get_or_404(id)
    photo_urls = photo.video_url.split(' ')
#    print(photo.photo_url, "+++++++++++++++++++++++++++")
    if photo.photo_url == None:
        photo.photo_url = 'http://p688ihx0v.bkt.clouddn.com/c.png;http://p688ihx0v.bkt.clouddn.com/c.png;'
    tphoto_url = photo.photo_url.split(';')
    tphoto_url.pop()
    photo_url = []
    for mystr in tphoto_url:
        i = mystr.find('com')
        tstr = mystr[:i+ 3] + '/' + mystr[i+3:]
        photo_url.append(tstr)
    if 'vote' in session.keys():
        if session['vote'] == 1:
            ip = request.remote_addr
            if r5.get(ip):
                flash("每天只能投一次票!")
            else:
                photo.liked_count += 1
                db.session.add(photo)
                db.session.commit()
                flash("投票成功")
                r5.set(ip, ip)
            session['vote'] = 0
            return redirect(url_for('main.get_photo', id=photo.id))
    else:
        session['vote'] = 0
    return render_template('main/photo.html', photo=photo, photo_urls=photo_urls, photo_url=photo_url)


@main.route('/startup/<int:id>/', methods=["GET", "POST"])
def get_startup(id):
    startup = Startup.query.filter_by(is_confirm=True,id=id).first_or_404()
    if 'vote' in session.keys():
        if session['vote'] == 1:
            ip = request.remote_addr
            if r6.get(ip):
                flash("每天只能投一次票!")
            else:
                startup.liked_count += 1
                db.session.add(startup)
                db.session.commit()
                flash("投票成功")
                r6.set(ip, ip)
            session['vote'] = 0
            return redirect(url_for('main.get_startup', id=startup.id))
    else:
        session['vote'] = 0
    return render_template('main/startup.html', startup=startup)


@main.route('/notice/<int:id>/')
def get_notice(id):
    notice = Notice.query.filter_by(is_confirm=True,id=id).first_or_404()
    return render_template('main/notice.html', notice=notice)


@main.route('/captcha/')
def captcha():
    return render_template('/main/captcha.html')


@main.route('/getcaptcha/', methods=["GET"])
def get_captcha():
    user_id = random.randint(1,100)
    gt =  GeetestLib(captcha_id, private_key)
    status = gt.pre_process(user_id)
    session[gt.GT_STATUS_SESSION_KEY] = status
    session["user_id"] = user_id
    response_str = gt.get_response_str()
    print(response_str)
    return response_str


@main.route('/validate', methods=["POST"])
def validate_capthca():
    session['vote'] = 0
    gt = GeetestLib(captcha_id, private_key)
    challenge = request.form[gt.FN_CHALLENGE]
    validate = request.form[gt.FN_VALIDATE]
    seccode = request.form[gt.FN_SECCODE]
    status = session[gt.GT_STATUS_SESSION_KEY]
    user_id = session["user_id"]
    session['refer'] = request.referrer
    if status:
        result = gt.success_validate(challenge, validate, seccode, user_id)
    else:
        result = gt.failback_validate(challenge, validate, seccode)
    result = "success" if result else "fail"
    if result == "success":
        session['vote'] = 1
        return redirect(session['refer'])
    else:
        flash("验证码错误!")
        return redirect(session['refer'])

@main.route('/movie/<int:id>/vote/', methods = ["GET"])
def vote_movie(id):
    movie = Movie.query.filter_by(is_confirm=True,id=id).first_or_404()
    ip = "movie" + request.remote_addr
    if r1.get(ip):
        return jsonify({}),403
    else:
        movie.liked_count += 1
        db.session.add(movie)
        db.session.commit()
        r1.set(ip, ip)
        return jsonify({}),200

@main.route('/article/<int:id>/vote/', methods = ["GET"])
def vote_article(id):
    article = Article.query.filter_by(is_confirm=True,id=id).first_or_404()
    ip = "article" + request.remote_addr
    if r1.get(ip):
        return jsonify({}),403
    else:
        article.liked_count += 1
        db.session.add(article)
        db.session.commit()
        r1.set(ip, ip)
        return jsonify({}),200

@main.route('/anime/<int:id>/vote/', methods = ["GET"])
def vote_anime(id):
    anime = Anime.query.filter_by(is_confirm=True,id=id).first_or_404()
    ip = "anime" + request.remote_addr
    if r1.get(ip):
        return jsonify({}),403
    else:
        anime.liked_count += 1
        db.session.add(anime)
        db.session.commit()
        r1.set(ip, ip)
        return jsonify({}),200

@main.route('/course/<int:id>/vote/', methods = ["GET"])
def vote_course(id):
    course = Course.query.filter_by(is_confirm=True,id=id).first_or_404()
    ip = "course" + request.remote_addr
    if r1.get(ip):
        return jsonify({}),403
    else:
        course.liked_count += 1
        db.session.add(course)
        db.session.commit()
        r1.set(ip, ip)
        return jsonify({}),200
        

@main.route('/photo/<int:id>/vote/', methods = ["GET"])
def vote_photo(id):
    photo = Photo.query.filter_by(is_confirm=True,id=id).first_or_404()
    ip = "photo" + request.remote_addr
    if r1.get(ip):
        return jsonify({}), 403
    else:
        photo.liked_count += 1
        db.session.add(photo)
        db.session.commit()
        r1.set(ip, ip)
        return jsonify({}), 200

@main.route('/startup/<int:id>/vote/', methods = ["GET"])
def vote_startup(id):
    startup = Startup.query.filter_by(is_confirm=True,id=id).first_or_404()
    ip = "startup" + request.remote_addr
    if r1.get(ip):
        return jsonify({}), 403
    else:
        startup.liked_count += 1
        db.session.add(startup)
        db.session.commit()
        r1.set(ip, ip)
        return jsonify({}), 200
