import os
import sys

from flask import Flask, render_template, request, session, make_response
from pyfladesk import init_gui
from waitress import serve
from youtubesearchpython import VideosSearch, Video, ResultMode, Channel
from flask import request

from backend.main import process_video

base_dir = '.'
query = ""
urls = [""] * 5
if hasattr(sys, '_MEIPASS'):
    base_dir = os.path.join(sys._MEIPASS)

app = Flask(__name__,
            static_folder=os.path.join(base_dir, 'static'),
            template_folder=os.path.join(base_dir, 'templates'))


def get_url(query, idx=0, limit=2):
    videos_search = VideosSearch(query, limit=limit)
    videos_search = videos_search.result()["result"][idx]
    return videos_search["link"].replace('/watch?v=', '/embed/'), videos_search["title"], \
           videos_search["publishedTime"], videos_search["viewCount"]["short"], \
           videos_search["channel"]["name"], videos_search["channel"]["thumbnails"][0]["url"],


def get_urls(query, limit=5):
    videos_search = VideosSearch(query, limit=limit)
    return [(x["link"].replace('/watch?v=', '/embed/'), x["title"]) for x in videos_search.result()["result"]]


app.secret_key = 'dljsaklqk24e21cjn!Ew@@dsa5'


@app.route('/')
def index():
    try:
        return render_template('index.html', url=session["url"], urls=urls)
    except:
        return render_template('welcome.html')


def get_info_by_url(url_):
    if "embed" in url_:
        url_ = url_.replace('/embed/', '/watch?v=')
    results = Video.get(url_, mode=ResultMode.json, get_upload_date=True)
    return results["title"], results["publishDate"], results["viewCount"]["text"], results["channel"]["name"], \
           Channel.get(results["channel"]["link"].split("/")[-1])["thumbnails"][0]["url"]


@app.route('/get_video_url', methods=['POST', 'GET'])
def video2():
    url = request.form.get("video-title")
    print("arg: ", url)
    title, publish_time, view_count, channel_name, pfp_name = get_info_by_url(url)
    session["url"] = url
    urls = get_urls(query)
    if "embed" not in query:
        url = url.replace('/watch?v=', '/embed/')
    return render_template('index.html', url=url,
                           title=title, publish_time=publish_time, view_count=view_count, channel_name=channel_name,
                           pfp_name=pfp_name, urls=urls)
    # return render_template('index.html')


@app.route('/get_video', methods=['POST'])
def video():
    query = request.form.get("query")
    if "youtu.be" in query or "youtube.com" in query:
        if "youtu.be" in query:
            url = query.replace("youtu.be/", "youtube.com/watch?v=")
        else:
            url = query
        print(url)
        title, publish_time, view_count, channel_name, pfp_name = get_info_by_url(url)
    else:
        url, title, publish_time, view_count, channel_name, pfp_name = get_url(query)
    session["url"] = url
    urls = get_urls(title)
    if "embed" not in query:
        url = url.replace('/watch?v=', '/embed/')
    return render_template('index.html', url=url,
                           title=title, publish_time=publish_time, view_count=view_count, channel_name=channel_name,
                           pfp_name=pfp_name, urls=urls)
    # return render_template('index.html')


@app.route('/translate', methods=['POST'])
def translate():
    url = session["url"]
    if "embed" in url:
        url = url.replace('/embed/', '/watch?v=')
    print(f"translate url '{url}'")
    # temp_response = make_response("please wait a minute..", 200)
    # temp_response.mimetype = "text/plain"
    render_template("wait.html")
    process_video(url, limit="third")
    title, publish_time, view_count, channel_name, pfp_name = get_info_by_url(url)
    urls = get_urls(title)
    url = url.replace('/watch?v=', '/embed/')
    return render_template('double_search.html', url=url,
                           title=title, publish_time=publish_time, view_count=view_count, channel_name=channel_name,
                           pfp_name=pfp_name, urls=urls, video_id=url.split("/embed/")[1])


# def run_waitress():
    # app.run()


if __name__ == '__main__':
    serve(app)
    # app.run(debug=False)
    # init_gui(app)
