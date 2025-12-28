from pydantic import BaseModel


class ContentLimits(BaseModel):
    """
    Content Limits
    """

    token_input_limit: int = -1
    """Maximum token count input limit (-1 indicates unlimited)"""

    file_size_limit: int = -1
    """Maximum total file size limit (in bytes; -1 indicates unlimited)"""

    # --------------------------------------------------
    # Text Files
    # --------------------------------------------------

    text_file_limit: int = -1
    """Maximum number of text files (-1 indicates unlimited)"""

    # --------------------------------------------------
    # Image Files
    # --------------------------------------------------

    image_input_enabled: bool = True
    """Whether image input is enabled"""

    image_file_limit: int = -1
    """Maximum number of image files (-1 indicates unlimited)"""

    # --------------------------------------------------
    # Audio Files
    # --------------------------------------------------

    audio_input_enabled: bool = True
    """Whether audio input is enabled"""

    audio_duration_limit: float = 60 * 60 * 9.5
    """Maximum audio duration limit (in seconds; Gemini's limit is 9.5h)"""

    audio_file_limit: int = -1
    """Maximum number of audio files (-1 indicates unlimited)"""

    # --------------------------------------------------
    # Video Files
    # --------------------------------------------------

    video_input_enabled: bool = True
    """Whether video input is enabled"""

    video_duration_limit: float = 60 * 60 * 1.0
    """Maximum video duration limit (in seconds; Gemini's limit is 1h)"""

    video_file_limit: int = -1
    """Maximum number of video files (-1 indicates unlimited)"""

    # --------------------------------------------------
    # PDF Files
    # --------------------------------------------------

    pdf_input_enabled: bool = True
    """Whether PDF input is enabled"""

    pdf_page_limit: int = 100
    """Maximum number of PDF pages (default is 100)"""

    pdf_file_limit: int = -1
    """Maximum number of PDF files (-1 indicates unlimited)"""
