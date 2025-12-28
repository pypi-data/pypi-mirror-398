from kiarina.llm.content import ContentLimits


def test_content_limits_default_values():
    limits = ContentLimits()

    # Token and file size limits
    assert limits.token_input_limit == -1
    assert limits.file_size_limit == -1

    # Text files
    assert limits.text_file_limit == -1

    # Image files
    assert limits.image_input_enabled is True
    assert limits.image_file_limit == -1

    # Audio files
    assert limits.audio_input_enabled is True
    assert limits.audio_duration_limit == 60 * 60 * 9.5  # 9.5 hours
    assert limits.audio_file_limit == -1

    # Video files
    assert limits.video_input_enabled is True
    assert limits.video_duration_limit == 60 * 60 * 1.0  # 1 hour
    assert limits.video_file_limit == -1

    # PDF files
    assert limits.pdf_input_enabled is True
    assert limits.pdf_page_limit == 100
    assert limits.pdf_file_limit == -1
