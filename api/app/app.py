# -*- coding: utf-8 -*-
# python 3.6.9

from flask import Flask, url_for, redirect, request, send_file, after_this_request, make_response
from celery import Celery
import youtube_dl
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
    print("--- segment audio init ---")
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
    print("--- cut audio init ---")

    audio = AudioSegment.from_file(temppath+fname)
    sample = audio[int(start):int(end)]
    sample_path = temppath+outname+'_sample.mp3'
    sample.export(sample_path, format="mp3")

    # delete whole audio
    print("removing ", temppath+fname)
    os.remove(temppath+fname)

    return sample_path


def ytsampler_raw(url, ydl_opts, start=None, end=None,  segment_len=0, segment=False):
    print("--- ytsampler_raw init ---")

    task_id = "somesome"
    temppath = 'files/'+task_id+'/'
    filename = 'download.mp3'
    ydl_opts['outtmpl'] = temppath+filename

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        title = info_dict.get('title', 'johnaudidoe')


    if segment:
        sample_path = segment_audio(temppath, filename, segment_len, outname=title)
    else:
        sample_path = cut_audio(temppath, filename, start, end, outname=title)

    return sample_path


@celery.task(name="app.app.ytsampler", bind=True)
def ytsampler(self, url, ydl_opts, start, end, segment_len=0, segment=False):
    print("--- ytsampler init ---")

    task_id = self.request.id
    print("task id", task_id)
    temppath = 'files/'+task_id+'/'
    filename = 'download.mp3'
    ydl_opts['outtmpl'] = temppath+filename

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        title = info_dict.get('title', 'johnaudidoe')

    if segment:
        print("segment")
        sample_path = segment_audio(temppath, filename, segment_len, outname=title)
    else:
        print("extract/cut")
        sample_path = cut_audio(temppath, filename, start, end, outname=title)

    return sample_path

#http://localhost:420/extract?url=https://www.youtube.com/watch?v=ThvESdCX8QM&start=1000&end=5000
@app.route('/extract')
def extract():
    print("--- init extract ---")
    url = request.args.get('url')
    start = request.args.get('start')
    end = request.args.get('end')

    #audio = ytsampler_raw(url, ydl_opts, start=start, end=end)
    audio = ytsampler.apply_async(args=[url, ydl_opts, start, end])

    return redirect(url_for('taskstatus', task_id=audio.id))

#http://localhost:420/segment?url=https://www.youtube.com/watch?v=ThvESdCX8QM&segment_len=60000
@app.route('/segment')
def segment():
    print("--- init segment ---")
    url = request.args.get('url')
    segment_len = request.args.get('segment_len')
    print(segment_len)

    # audio = ytsampler_raw(url, ydl_opts, segment_len=segment_len, segment=True)
    audio = ytsampler.apply_async(args=[url, ydl_opts, None, None], kwargs={'segment_len': segment_len, 'segment': True})

    # data = {'message': 'Task started successfully. To check status/get results go to url in status.', 'code': 'SUCCESS', 'status': url_for('status', task_id=audio.id)}
    # return make_response(data, 200)
    return redirect(url_for('taskstatus', task_id=audio.id))


@app.route('/result/<task_id>')
def get_results(task_id=None):
    print("--- result init ---")
    task = ytsampler.AsyncResult(task_id)
    # add download/
    if isinstance(task.result, list):
        result = [url_for('download', path=n) for n in task.result]
    else:
        result = url_for('download', path=n)

    data = {'message': 'Task completed successfully. To download files use the links provided', 'code': 'SUCCESS', 'download': result}

    return make_response(data, 200)

@app.route('/status/<task_id>')
def taskstatus(task_id=None):
    print("--- taskstatus init ---")
    task = ytsampler.AsyncResult(task_id)
    print(task.state)

    if task.state != "SUCCESS":
        response = {
            'state': task.state,
        }
        return make_response(response, 500)
    else:
        return redirect(url_for('get_results', task_id=task_id))



@app.route('/download/<path:path>')
def download(path):
    print("--- init download ---")
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
