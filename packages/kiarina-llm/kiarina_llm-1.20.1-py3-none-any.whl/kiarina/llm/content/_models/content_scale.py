from typing import Self

from pydantic import BaseModel, computed_field

from .._operations.calculate_overflow import calculate_overflow
from .content_limits import ContentLimits
from .content_metrics import ContentMetrics


class ContentScale(BaseModel):
    """
    Content Scale
    """

    limits: ContentLimits
    """Limits"""

    metrics: ContentMetrics
    """Metrics (usage)"""

    overflow: ContentMetrics
    """Overflow amount (in metrics format)"""

    # --------------------------------------------------
    # Properties
    # --------------------------------------------------

    @computed_field  # type: ignore
    @property
    def token_ratio(self) -> float:
        """
        Token usage ratio
        """
        if self.limits.token_input_limit == 0:
            return 0.0

        return self.metrics.token_count / self.limits.token_input_limit

    @computed_field  # type: ignore
    @property
    def has_overflow(self) -> bool:
        """
        Whether overflow has occurred
        """
        return self.is_overflow()

    @computed_field  # type: ignore
    @property
    def error_message(self) -> str:
        """
        Error message
        """
        return self.get_error_message()

    # --------------------------------------------------
    # Methods
    # --------------------------------------------------

    def is_overflow(self) -> bool:
        """
        Whether the message has overflowed
        """
        return (
            self.overflow.token_count > 0
            or self.overflow.file_size > 0
            or self.overflow.text_file_count > 0
            or self.overflow.image_file_count > 0
            or self.overflow.audio_duration > 0
            or self.overflow.audio_file_count > 0
            or self.overflow.video_duration > 0
            or self.overflow.video_file_count > 0
            or self.overflow.pdf_page_count > 0
            or self.overflow.pdf_file_count > 0
        )

    def get_error_message(self) -> str:
        """
        Get error message
        """
        if self.overflow.file_size > 0:
            return f"Total file size exceeds limit: {self.metrics.file_size} / {self.limits.file_size_limit} bytes"
        elif self.overflow.pdf_file_count > 0:
            return f"Number of PDF files exceeds limit: {self.metrics.pdf_file_count} / {self.limits.pdf_file_limit}"
        elif self.overflow.pdf_page_count > 0:
            return f"PDF page count exceeds limit: {self.metrics.pdf_page_count} / {self.limits.pdf_page_limit}"
        elif self.overflow.video_file_count > 0:
            return f"Number of video files exceeds limit: {self.metrics.video_file_count} / {self.limits.video_file_limit}"
        elif self.overflow.video_duration > 0:
            return f"Video duration exceeds limit: {self.metrics.video_duration}s / {self.limits.video_duration_limit}s"
        elif self.overflow.audio_file_count > 0:
            return f"Number of audio files exceeds limit: {self.metrics.audio_file_count} / {self.limits.audio_file_limit}"
        elif self.overflow.audio_duration > 0:
            return f"Audio duration exceeds limit: {self.metrics.audio_duration}s / {self.limits.audio_duration_limit}s"
        elif self.overflow.image_file_count > 0:
            return f"Number of image files exceeds limit: {self.metrics.image_file_count} / {self.limits.image_file_limit}"
        elif self.overflow.text_file_count > 0:
            return f"Number of text files exceeds limit: {self.metrics.text_file_count} / {self.limits.text_file_limit}"
        elif self.overflow.token_count > 0:
            return f"Token count exceeds limit: {self.metrics.token_count} / {self.limits.token_input_limit}"
        else:
            return "Message is valid"

    # --------------------------------------------------
    # Class Methods
    # --------------------------------------------------

    @classmethod
    def create(cls, *, limits: ContentLimits, metrics: ContentMetrics) -> Self:
        """
        Create scale information from metrics and limits
        """
        overflow = calculate_overflow(limits=limits, metrics=metrics)
        return cls(limits=limits, metrics=metrics, overflow=overflow)
