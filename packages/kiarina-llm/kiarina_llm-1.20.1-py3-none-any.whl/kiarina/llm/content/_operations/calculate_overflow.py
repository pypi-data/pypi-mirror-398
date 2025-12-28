from .._models.content_limits import ContentLimits
from .._models.content_metrics import ContentMetrics


def calculate_overflow(
    *, limits: ContentLimits, metrics: ContentMetrics
) -> ContentMetrics:
    """
    Calculate overflow amount from metrics and limits
    """
    return ContentMetrics(
        token_count=(
            max(0, metrics.token_count - limits.token_input_limit)
            if limits.token_input_limit != -1
            else 0
        ),
        file_size=(
            max(0, metrics.file_size - limits.file_size_limit)
            if limits.file_size_limit != -1
            else 0
        ),
        text_file_count=(
            max(0, metrics.text_file_count - limits.text_file_limit)
            if limits.text_file_limit != -1
            else 0
        ),
        image_file_count=(
            max(0, metrics.image_file_count - limits.image_file_limit)
            if (limits.image_input_enabled and limits.image_file_limit != -1)
            else 0
        ),
        audio_duration=(
            max(0.0, metrics.audio_duration - limits.audio_duration_limit)
            if limits.audio_input_enabled
            else 0.0
        ),
        audio_file_count=(
            max(0, metrics.audio_file_count - limits.audio_file_limit)
            if (limits.audio_input_enabled and limits.audio_file_limit != -1)
            else 0
        ),
        video_duration=(
            max(0.0, metrics.video_duration - limits.video_duration_limit)
            if limits.video_input_enabled
            else 0.0
        ),
        video_file_count=(
            max(0, metrics.video_file_count - limits.video_file_limit)
            if (limits.video_input_enabled and limits.video_file_limit != -1)
            else 0
        ),
        pdf_page_count=(
            max(0, metrics.pdf_page_count - limits.pdf_page_limit)
            if limits.pdf_input_enabled
            else 0
        ),
        pdf_file_count=(
            max(0, metrics.pdf_file_count - limits.pdf_file_limit)
            if (limits.pdf_input_enabled and limits.pdf_file_limit != -1)
            else 0
        ),
    )
