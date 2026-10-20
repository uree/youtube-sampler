import logging

import yt_dlp
from celery import shared_task

from .audio_methods import cut_audio, segment_audio

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@shared_task(bind=True)
def ytsampler(self, url, ydl_opts, start=None, end=None, segment_len=0):
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
            saved_mp3_path = info_dict["requested_downloads"][0]["filepath"].replace(
                "/home/youtube_sampler/", ""
            )
            logger.debug(saved_mp3_path)
        except Exception as e:  # noqa: BLE001
            logger.error(
                f"yt_dlp failure with the following url: {url}")
            logger.error(repr(e))
            return False

        title = info_dict.get("title", "johnaudidoe")

    if segment_len:
        sample_path = segment_audio(saved_mp3_path, segment_len, outname=title)
    elif start and end:
        sample_path = cut_audio(saved_mp3_path, start, end, outname=title)
    else:
        sample_path = saved_mp3_path

    return sample_path
