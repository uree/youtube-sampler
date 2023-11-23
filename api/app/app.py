# -*- coding: utf-8 -*-
# python 3.6.9

from flask import Flask, url_for, redirect, request, send_file, after_this_request, make_response, render_template
from celery import Celery
import yt_dlp
import ffmpeg
from pydub import AudioSegment
from pydub.utils import make_chunks
import logging
import time
import os
import io
from pathlib import Path


app = Flask(__name__)

app.config['CELERY_BROKER_URL'] = 'redis://redis:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://redis:6379/0'
app.config['CELERY_IGNORE_RESULT'] = False

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

ydl_opts = {
    'format': '140',
    'outtmpl': 'files/default/',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }]
}


def segment_audio(temppath, fname, segment_len, outname):
    """
    Split autio file into segments and delete original audio file.
    """

    audio = AudioSegment.from_file(temppath+fname)
    segments = make_chunks(audio, int(segment_len))

    segnames = []

    for i, seg in enumerate(segments):
        segname = temppath+outname+"_segment{0}.mp3".format(i)
        seg.export(segname, format="mp3")
        segnames.append(segname)

    # delete whole audio
    os.remove(temppath+fname)

    return segnames

def cut_audio(temppath, fname, start, end, outname):
    """
    Cut segment from and audio file an delete the original audio file.
    """

    audio = AudioSegment.from_file(temppath+fname)
    sample = audio[int(start):int(end)]
    sample_path = temppath+outname+'_sample.mp3'
    sample.export(sample_path, format="mp3")

    # delete whole audio
    os.remove(temppath+fname)

    return sample_path


@celery.task(name="app.app.ytsampler", bind=True)
def ytsampler(self, url, ydl_opts, start, end, segment_len=0, segment=False):
    """
    Download the youtube video/audio and call the postporcessing functions (to convert and segment or cut the audio).
    """

    task_id = self.request.id
    temppath = 'files/'+task_id+'/'
    filename = 'download.mp3'
    ydl_opts['outtmpl'] = temppath+'download'

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        title = info_dict.get('title', 'johnaudidoe')

    if segment:
        sample_path = segment_audio(temppath, filename, segment_len, outname=title)
    else:
        sample_path = cut_audio(temppath, filename, start, end, outname=title)

    return sample_path

@app.route('/interface')
def interface_index():
    """
    Serve simple interface to interact with the API endpoints.
    """
    return render_template("index.html")


@app.route('/extract', methods=["GET", "POST"])
def extract():
    """
    Start a celery task to extract a clip based on the start and end parameters.
    """
    if request.method == "GET":
        url = request.args.get('url')
        start = request.args.get('start')
        end = request.args.get('end')

        audio = ytsampler.apply_async(args=[url, ydl_opts, start, end])

        check_url = url_for('taskstatus', task_id=audio.id)

        return redirect(check_url)

    if request.method == "POST":
        if request.form:
            url = request.form.get('url')
            start = request.form.get('start')
            end = request.form.get('end')

            audio = ytsampler.apply_async(args=[url, ydl_opts, start, end])

            return render_template("check_status.html", task_id=audio.id, html=True)

        if request.headers['content type'] == "application/json":
            data = request.get_json()
            url = data['url']
            start = data['start']
            end = data['end']

            audio = ytsampler.apply_async(args=[url, ydl_opts, start, end])

            return {"status_url": url_for('taskstatus', task_id=audio.id)}


@app.route('/segment')
def segment():
    """
    Start the celery task to segment an audio file into ... segments.
    """

    url = request.args.get('url')
    segment_len = request.args.get('segment_len')

    audio = ytsampler.apply_async(args=[url, ydl_opts, None, None], kwargs={'segment_len': segment_len, 'segment': True})

    return redirect(url_for('taskstatus', task_id=audio.id))


@app.route('/result')
def get_results():
    """
    Get results of a completed task.
    """
    task_id = request.args.get("task_id")

    task = ytsampler.AsyncResult(task_id)
    # add download/
    if isinstance(task.result, list):
        result = [url_for('download', path=n) for n in task.result]
    else:
        result = url_for('download', path=task.result)

    data = {'message': 'Task completed successfully. To download files use the links provided', 'code': 'SUCCESS', 'download': result}

    return make_response(data, 200)


@app.route('/status')
def taskstatus():
    """
    Check celery task status.
    """
    task_id = request.args.get("task_id")
    html = request.args.get("html", False)

    task = ytsampler.AsyncResult(task_id)

    if html:
        if task.state == "PENDING":
            return render_template("check_status.html", task_id=task_id)
        elif task.state == "FAILURE":
            return "FAILURE"
        elif task.state == "SUCCESS":
            dl_url = url_for('download', path=task.result)
            return render_template("result.html", dl_url=dl_url)
    else:
        if task.state != "SUCCESS":
            response = {
                'state': task.state,
            }
            return make_response(response, 500)
        else:
            return redirect(url_for('get_results', task_id=task_id))


@app.route('/download/<path:path>')
def download(path):
    """
    Download a file.
    """
    spl = path.rsplit("/", 1)
    fname = spl[-1]
    folder = spl[0]

    return_data = io.BytesIO()
    with open(path, 'rb') as fo:
        return_data.write(fo.read())

    return_data.seek(0)

    os.remove(path)

    try:
        os.rmdir(folder)
    except:
        pass

    return send_file(return_data, mimetype='audio/mpeg',
                     attachment_filename=fname, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=420, debug=True)
