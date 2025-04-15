# -*- coding: utf-8 -*-
import io
import os

from flask import (
    Blueprint,
    send_file,
    current_app,
    redirect,
    url_for,
    make_response,
    request,
    render_template
)
import yt_dlp

from .tasks import ytsampler
from .ydl_options import ydl_opts
from .audio_methods import lgt


bp = Blueprint("core", __name__)


@bp.route("/")
def interface_index():
    """
    Serve simple interface to interact with the API endpoints.
    """
    current_app.logger.info("index info")
    current_app.logger.debug("index debug")
    current_app.logger.error("index error")
    return render_template("index.html")


@bp.route("/logtest")
def log_test():

    beef = lgt("playaa")
    return "<h1>"+beef+"</h1>"


@bp.route("/extract", methods=["GET", "POST"])
def extract():
    """
    Start a celery task to extract a clip based on the start and end parameters. # noqa: E501
    """

    if request.method == "GET":
        current_app.logger.debug("Extract GET")
        url = request.args.get("url", None)
        start = request.args.get("start", None)
        end = request.args.get("end", None)
        current_app.logger.debug(f"{url} {start} {end}")

        if None in (url, start, end):
            return make_response(
                {"error": "Missing parameter. Provide url, start and end."}
            )
        current_app.logger.debug("extractor")
        yt_extractor = yt_dlp.extractor.get_info_extractor("Youtube")
        is_valid_link = yt_extractor.suitable(url)
        current_app.logger.debug("extracted")

        if not is_valid_link:
            current_app.logger.debug("Invalid url: {}".format(url))
            return make_response({"error": "Invalid url."}, 400)

        current_app.logger.debug("sampler")
        try:
            audio = ytsampler.apply_async(
                args=[url, ydl_opts, start, end])
        except Exception as e:
            current_app.logger.debug("Something went wrong tasking celery.")
            current_app.logger.debug(repr(e))

        current_app.logger.debug("postsampler")

        check_url = url_for("core.taskstatus", task_id=audio.id)

        return redirect(check_url)

    if request.method == "POST":
        current_app.logger.debug("Extract POST")
        url = request.form.get("url", None)
        start = request.form.get("start", None)
        end = request.form.get("end", None)
        current_app.logger.debug(f"{url} {start} {end}")

        if None in (url, start, end):
            return render_template(
                "failure.html", message="Missing parameter. Provide url, start and end."  # noqa: E501
            )

        try:
            yt_extractor = yt_dlp.extractor.get_info_extractor("Youtube")
            is_valid_link = yt_extractor.suitable(url)
        except Exception as e:
            current_app.logger.debug("Error calling ty_dlp.")
            current_app.logger.debug(repr(e))

        if not is_valid_link:
            current_app.logger.debug("Invalid url: {}".format(url))
            return render_template("failure.html", message="Invalid url.")

        current_app.logger.debug("pre task")

        try:
            audio = ytsampler.apply_async(
                args=[url, ydl_opts, start, end])
            current_app.logger.debug(audio)
        except Exception as e:
            current_app.logger.debug("Something went wrong tasking celery.")
            current_app.logger.debug(repr(e))

        return render_template("check_status.html", task_id=audio.id, html=True)  # noqa: E501


@bp.route("/segment")
def segment():
    """
    Start the celery task to segment an audio file into ... segments.
    """

    url = request.args.get("url")
    segment_len = request.args.get("segment_len")

    audio = ytsampler.apply_async(
        args=[url, ydl_opts, None, None],
        kwargs={"segment_len": segment_len, "segment": True},
    )

    return redirect(url_for("core.taskstatus", task_id=audio.id))


@bp.route("/status", methods=["GET"])
def taskstatus():
    """
    Check celery task status.
    """
    task_id = request.args.get("task_id")
    html = request.args.get("html", False)

    response = {"state": None, "message": None, "download_urls": None}

    if not task_id:
        response["message"] = "Missing request argument `task_id`."
        return make_response(response, 400)

    task = ytsampler.AsyncResult(task_id)

    if html:
        if task.state == "PENDING":
            return render_template("check_status.html", task_id=task_id)
        elif task.state == "FAILURE":
            current_app.logger.error(task.result)
            return render_template("failure.html")
        elif task.state == "SUCCESS":
            dl_url = url_for("core.download", path=task.result)
            return render_template("result.html", dl_url=dl_url)
    else:
        response["state"] = task.state

        if task.state == "PENDING":
            response["message"] = "Task still in progress."
            return make_response(response, 200)

        elif task.state == "SUCCESS":
            if isinstance(task.result, list):
                result = [url_for("core.download", path=n)
                          for n in task.result]
            else:
                result = url_for("core.download", path=task.result)

            response["download_urls"] = result
            return make_response(response, 200)

        elif task.state == "FAILURE":
            current_app.logger.error(task.result)
            response["message"] = "Something went wrong."
            return make_response(response)


@bp.route("/download/<path:path>")
def download(path):
    """
    Download a file.
    """
    spl = path.rsplit("/", 1)
    fname = spl[-1]
    folder = spl[0]

    return_data = io.BytesIO()
    with open(path, "rb") as fo:
        return_data.write(fo.read())

    return_data.seek(0)

    os.remove(path)

    try:
        os.rmdir(folder)
    except Exception as e:
        current_app.logger.error(f"Error removing temp folder: {repr(e)}")

    return send_file(
        return_data,
        mimetype="audio/mpeg",
        download_name=fname,
        as_attachment=True,
    )
