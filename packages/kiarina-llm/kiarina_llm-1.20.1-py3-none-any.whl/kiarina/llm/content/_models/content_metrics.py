from typing import Self

from pydantic import BaseModel


class ContentMetrics(BaseModel):
    """
    Content Metrics
    """

    # --------------------------------------------------
    # Properties
    # --------------------------------------------------

    token_count: int = 0
    """Token count"""

    file_size: int = 0
    """Total file size (bytes)"""

    text_file_count: int = 0
    """Number of text files"""

    image_file_count: int = 0
    """Number of image files"""

    audio_duration: float = 0.0
    """Audio duration (seconds)"""

    audio_file_count: int = 0
    """Number of audio files"""

    video_duration: float = 0.0
    """Video duration (seconds)"""

    video_file_count: int = 0
    """Number of video files"""

    pdf_page_count: int = 0
    """Number of PDF pages"""

    pdf_file_count: int = 0
    """Number of PDF files"""

    # --------------------------------------------------
    # Properties for Meta Information
    # --------------------------------------------------

    text_token_count: int = 0
    """Text token count"""

    image_token_count: int = 0
    """Image token count"""

    audio_token_count: int = 0
    """Audio token count"""

    video_token_count: int = 0
    """Video token count"""

    pdf_token_count: int = 0
    """PDF token count"""

    # --------------------------------------------------
    # Methods
    # --------------------------------------------------

    def add_text_token_count(self, count: int) -> None:
        self.text_token_count += count
        self.token_count += count

    def add_image_token_count(self, count: int) -> None:
        self.image_token_count += count
        self.token_count += count

    def add_audio_token_count(self, count: int) -> None:
        self.audio_token_count += count
        self.token_count += count

    def add_video_token_count(self, count: int) -> None:
        self.video_token_count += count
        self.token_count += count

    def add_pdf_token_count(self, count: int) -> None:
        self.pdf_token_count += count
        self.token_count += count

    # --------------------------------------------------
    # Operators
    # --------------------------------------------------

    def __add__(self, other: Self) -> Self:
        """
        Add metrics
        """
        result = self.model_copy()

        result.token_count += other.token_count
        result.file_size += other.file_size
        result.text_file_count += other.text_file_count
        result.image_file_count += other.image_file_count
        result.audio_duration += other.audio_duration
        result.audio_file_count += other.audio_file_count
        result.video_duration += other.video_duration
        result.video_file_count += other.video_file_count
        result.pdf_page_count += other.pdf_page_count
        result.pdf_file_count += other.pdf_file_count

        result.text_token_count += other.text_token_count
        result.image_token_count += other.image_token_count
        result.audio_token_count += other.audio_token_count
        result.video_token_count += other.video_token_count
        result.pdf_token_count += other.pdf_token_count

        return result
