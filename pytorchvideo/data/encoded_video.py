# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved.

import io
import logging
import pathlib
import cv2
from typing import Any, Dict

from iopath.common.file_io import g_pathmgr
from pytorchvideo.data.decoder import DecoderType

from .video import Video


logger = logging.getLogger(__name__)


def select_video_class(decoder: str) -> Video:
    """
    Select the class for accessing clips based on provided decoder string

    Args:
        decoder (str): Defines what type of decoder used to decode a video.
    """
    if DecoderType(decoder) == DecoderType.PYAV:
        from .encoded_video_pyav import EncodedVideoPyAV

        video_cls = EncodedVideoPyAV
    elif DecoderType(decoder) == DecoderType.TORCHVISION:
        from .encoded_video_torchvision import EncodedVideoTorchVision

        video_cls = EncodedVideoTorchVision
    elif DecoderType(decoder) == DecoderType.DECORD:
        from .encoded_video_decord import EncodedVideoDecord

        video_cls = EncodedVideoDecord
    else:
        raise NotImplementedError(f"Unknown decoder type {decoder}")

    return video_cls


class EncodedVideo(Video):
    """
    EncodedVideo is an abstraction for accessing clips from an encoded video.
    It supports selective decoding when header information is available.
    """

    @classmethod
    def from_path(
        cls,
        file_path: str,
        decode_video: bool = True,
        decode_audio: bool = True,
        decoder: str = "pyav",
        **other_args: Dict[str, Any],
    ):
        """
        Fetches the given video path using PathManager (allowing remote uris to be
        fetched) and constructs the EncodedVideo object.

        Args:
            file_path (str): a PathManager file-path.
        """
        # We read the file with PathManager so that we can read from remote uris.
        with g_pathmgr.open(file_path, "rb") as fh:
            video_file = io.BytesIO(fh.read())

        short_side_scale = other_args.pop("short_side_scale", None)
        if short_side_scale:
            video_capture = cv2.VideoCapture(file_path)
            width = video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)

            if width == 0 or height == 0:
                raise ValueError(f'Invalid video object at "{file_path}"')

            if width < height:
                height = short_side_scale * height / width
                width = short_side_scale
            else:
                width = short_side_scale * width / height
                height = short_side_scale
            other_args["width"] = int(width)
            other_args["height"] = int(height)

        video_cls = select_video_class(decoder)
        return video_cls(
            file=video_file,
            video_name=pathlib.Path(file_path).name,
            decode_video=decode_video,
            decode_audio=decode_audio,
            **other_args,
        )
