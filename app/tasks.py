# -*- coding: utf-8 -*-
import logging

from celery import shared_task
import yt_dlp
from .audio_methods import segment_audio, cut_audio

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@shared_task(bind=True)
def ytsampler(self, url, ydl_opts, start, end, segment_len=0, segment=False):  # noqa: E501
    """
    Download the youtube video/audio and call the postporcessing functions
    (to convert and segment or cut the audio).
    """

    task_id = self.request.id
    temppath = "app/files/" + task_id + "/"
    ydl_opts["paths"] = {"home": temppath}

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info_dict = ydl.extract_info(url, download=True)
            logger.debug("runnin")
            saved_mp3_path = info_dict["requested_downloads"][0]["filepath"].replace(  # noqa: E501
                "/home/youtube_sampler/", ""
            )
            logger.debug(saved_mp3_path)
        except Exception as e:
            logger.error(
                "yt_dlp failure with the following url: {}".format(url))
            logger.error(repr(e))
            return False

        title = info_dict.get("title", "johnaudidoe")

    if segment:
        sample_path = segment_audio(saved_mp3_path, segment_len, outname=title)
    else:
        sample_path = cut_audio(saved_mp3_path, start, end, outname=title)

    return sample_path
