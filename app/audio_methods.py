# -*- coding: utf-8 -*-
import logging
import os

import ffmpeg  # noqa
from pydub import AudioSegment
from pydub.utils import make_chunks


logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


def segment_audio(filepath, segment_len, outname):
    """
    Split autio file into segments and delete original audio file.
    """
    logger.debug("segment")
    logger.debug(filepath)

    audio = AudioSegment.from_file(filepath)
    segments = make_chunks(audio, int(segment_len))

    segnames = []

    for i, seg in enumerate(segments):
        segname = filepath[:-4] + "_segment{0}.mp3".format(i)
        seg.export(segname, format="mp3")
        segnames.append(segname)

    # delete whole audio
    os.remove(filepath)

    return segnames


def cut_audio(filepath, start, end, outname):
    """
    Cut segment from and audio file an delete the original audio file.
    """
    logger.debug("cut")
    logger.debug(filepath)

    try:
        audio = AudioSegment.from_file(filepath)
    except Exception as e:
        logger.error(f"Failure segmenting audio: {e}")

    sample = audio[int(start): int(end)]
    sample_path = filepath[:-4] + "_sample.mp3"
    try:
        sample.export(sample_path, format="mp3")
    except Exception as e:
        logger.error(f"Failure exporting mp3: {e}")

    # delete whole audio
    os.remove(filepath)

    return sample_path
