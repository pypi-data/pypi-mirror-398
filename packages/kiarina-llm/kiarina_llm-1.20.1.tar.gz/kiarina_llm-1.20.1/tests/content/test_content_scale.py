from kiarina.llm.content import ContentLimits, ContentMetrics, ContentScale


def test_content_scale_create_no_overflow():
    """Test ContentScale.create with no overflow"""
    limits = ContentLimits(
        token_input_limit=1000,
        file_size_limit=2048,
        text_file_limit=5,
        image_file_limit=3,
        audio_duration_limit=300.0,
        audio_file_limit=2,
        video_duration_limit=600.0,
        video_file_limit=1,
        pdf_page_limit=50,
        pdf_file_limit=2,
    )

    metrics = ContentMetrics(
        token_count=500,
        file_size=1024,
        text_file_count=3,
        image_file_count=2,
        audio_duration=150.0,
        audio_file_count=1,
        video_duration=300.0,
        video_file_count=1,
        pdf_page_count=25,
        pdf_file_count=1,
    )

    scale = ContentScale.create(limits=limits, metrics=metrics)

    assert scale.limits == limits
    assert scale.metrics == metrics
    assert not scale.has_overflow
    assert not scale.is_overflow()
    assert scale.error_message == "Message is valid"


def test_content_scale_create_with_token_overflow():
    """Test ContentScale.create with token overflow"""
    limits = ContentLimits(token_input_limit=100)
    metrics = ContentMetrics(token_count=150)

    scale = ContentScale.create(limits=limits, metrics=metrics)

    assert scale.has_overflow
    assert scale.is_overflow()
    assert scale.overflow.token_count == 50
    assert "Token count exceeds limit: 150 / 100" in scale.error_message


def test_content_scale_create_with_file_size_overflow():
    """Test ContentScale.create with file size overflow"""
    limits = ContentLimits(file_size_limit=1024)
    metrics = ContentMetrics(file_size=2048)

    scale = ContentScale.create(limits=limits, metrics=metrics)

    assert scale.has_overflow
    assert scale.is_overflow()
    assert scale.overflow.file_size == 1024
    assert "Total file size exceeds limit: 2048 / 1024 bytes" in scale.error_message


def test_content_scale_create_with_text_file_overflow():
    """Test ContentScale.create with text file overflow"""
    limits = ContentLimits(text_file_limit=3)
    metrics = ContentMetrics(text_file_count=5)

    scale = ContentScale.create(limits=limits, metrics=metrics)

    assert scale.has_overflow
    assert scale.is_overflow()
    assert scale.overflow.text_file_count == 2
    assert "Number of text files exceeds limit: 5 / 3" in scale.error_message


def test_content_scale_create_with_image_file_overflow():
    """Test ContentScale.create with image file overflow"""
    limits = ContentLimits(image_input_enabled=True, image_file_limit=2)
    metrics = ContentMetrics(image_file_count=4)

    scale = ContentScale.create(limits=limits, metrics=metrics)

    assert scale.has_overflow
    assert scale.is_overflow()
    assert scale.overflow.image_file_count == 2
    assert "Number of image files exceeds limit: 4 / 2" in scale.error_message


def test_content_scale_create_with_audio_duration_overflow():
    """Test ContentScale.create with audio duration overflow"""
    limits = ContentLimits(audio_input_enabled=True, audio_duration_limit=300.0)
    metrics = ContentMetrics(audio_duration=450.0)

    scale = ContentScale.create(limits=limits, metrics=metrics)

    assert scale.has_overflow
    assert scale.is_overflow()
    assert scale.overflow.audio_duration == 150.0
    assert "Audio duration exceeds limit: 450.0s / 300.0s" in scale.error_message


def test_content_scale_create_with_audio_file_overflow():
    """Test ContentScale.create with audio file overflow"""
    limits = ContentLimits(audio_input_enabled=True, audio_file_limit=1)
    metrics = ContentMetrics(audio_file_count=3)

    scale = ContentScale.create(limits=limits, metrics=metrics)

    assert scale.has_overflow
    assert scale.is_overflow()
    assert scale.overflow.audio_file_count == 2
    assert "Number of audio files exceeds limit: 3 / 1" in scale.error_message


def test_content_scale_create_with_video_duration_overflow():
    """Test ContentScale.create with video duration overflow"""
    limits = ContentLimits(video_input_enabled=True, video_duration_limit=600.0)
    metrics = ContentMetrics(video_duration=900.0)

    scale = ContentScale.create(limits=limits, metrics=metrics)

    assert scale.has_overflow
    assert scale.is_overflow()
    assert scale.overflow.video_duration == 300.0
    assert "Video duration exceeds limit: 900.0s / 600.0s" in scale.error_message


def test_content_scale_create_with_video_file_overflow():
    """Test ContentScale.create with video file overflow"""
    limits = ContentLimits(video_input_enabled=True, video_file_limit=1)
    metrics = ContentMetrics(video_file_count=2)

    scale = ContentScale.create(limits=limits, metrics=metrics)

    assert scale.has_overflow
    assert scale.is_overflow()
    assert scale.overflow.video_file_count == 1
    assert "Number of video files exceeds limit: 2 / 1" in scale.error_message


def test_content_scale_create_with_pdf_page_overflow():
    """Test ContentScale.create with PDF page overflow"""
    limits = ContentLimits(pdf_input_enabled=True, pdf_page_limit=50)
    metrics = ContentMetrics(pdf_page_count=75)

    scale = ContentScale.create(limits=limits, metrics=metrics)

    assert scale.has_overflow
    assert scale.is_overflow()
    assert scale.overflow.pdf_page_count == 25
    assert "PDF page count exceeds limit: 75 / 50" in scale.error_message


def test_content_scale_create_with_pdf_file_overflow():
    """Test ContentScale.create with PDF file overflow"""
    limits = ContentLimits(pdf_input_enabled=True, pdf_file_limit=2)
    metrics = ContentMetrics(pdf_file_count=4)

    scale = ContentScale.create(limits=limits, metrics=metrics)

    assert scale.has_overflow
    assert scale.is_overflow()
    assert scale.overflow.pdf_file_count == 2
    assert "Number of PDF files exceeds limit: 4 / 2" in scale.error_message


def test_content_scale_create_with_disabled_inputs():
    """Test ContentScale.create with disabled inputs (no overflow)"""
    limits = ContentLimits(
        image_input_enabled=False,
        audio_input_enabled=False,
        video_input_enabled=False,
        pdf_input_enabled=False,
    )

    metrics = ContentMetrics(
        image_file_count=10,
        audio_duration=1000.0,
        audio_file_count=5,
        video_duration=2000.0,
        video_file_count=3,
        pdf_page_count=200,
        pdf_file_count=5,
    )

    scale = ContentScale.create(limits=limits, metrics=metrics)

    assert not scale.has_overflow
    assert not scale.is_overflow()
    assert scale.overflow.image_file_count == 0
    assert scale.overflow.audio_duration == 0.0
    assert scale.overflow.audio_file_count == 0
    assert scale.overflow.video_duration == 0.0
    assert scale.overflow.video_file_count == 0
    assert scale.overflow.pdf_page_count == 0
    assert scale.overflow.pdf_file_count == 0


def test_content_scale_create_with_unlimited_limits():
    """Test ContentScale.create with unlimited limits (-1)"""
    limits = ContentLimits(
        token_input_limit=-1,
        file_size_limit=-1,
        text_file_limit=-1,
        image_file_limit=-1,
        audio_file_limit=-1,
        video_file_limit=-1,
        pdf_file_limit=-1,
    )

    metrics = ContentMetrics(
        token_count=10000,
        file_size=1024 * 1024,
        text_file_count=100,
        image_file_count=50,
        audio_file_count=20,
        video_file_count=10,
        pdf_file_count=30,
    )

    scale = ContentScale.create(limits=limits, metrics=metrics)

    assert not scale.has_overflow
    assert not scale.is_overflow()
    assert scale.overflow.token_count == 0
    assert scale.overflow.file_size == 0
    assert scale.overflow.text_file_count == 0
    assert scale.overflow.image_file_count == 0
    assert scale.overflow.audio_file_count == 0
    assert scale.overflow.video_file_count == 0
    assert scale.overflow.pdf_file_count == 0


def test_content_scale_token_ratio():
    """Test ContentScale token_ratio computed field"""
    # Test normal ratio
    limits = ContentLimits(token_input_limit=1000)
    metrics = ContentMetrics(token_count=250)
    scale = ContentScale.create(limits=limits, metrics=metrics)
    assert scale.token_ratio == 0.25

    # Test ratio with zero limit
    limits = ContentLimits(token_input_limit=0)
    metrics = ContentMetrics(token_count=100)
    scale = ContentScale.create(limits=limits, metrics=metrics)
    assert scale.token_ratio == 0.0

    # Test ratio over 1.0
    limits = ContentLimits(token_input_limit=100)
    metrics = ContentMetrics(token_count=150)
    scale = ContentScale.create(limits=limits, metrics=metrics)
    assert scale.token_ratio == 1.5


def test_content_scale_error_message_priority():
    """Test ContentScale error message priority (file_size has highest priority)"""
    limits = ContentLimits(
        token_input_limit=100,
        file_size_limit=1024,
        text_file_limit=2,
    )

    metrics = ContentMetrics(
        token_count=150,  # Overflow
        file_size=2048,  # Overflow (higher priority)
        text_file_count=5,  # Overflow
    )

    scale = ContentScale.create(limits=limits, metrics=metrics)

    assert scale.has_overflow
    # File size error should be shown first (highest priority)
    assert "Total file size exceeds limit" in scale.error_message
    assert "Token count exceeds limit" not in scale.error_message


def test_content_scale_direct_construction():
    """Test ContentScale direct construction (not using create method)"""
    limits = ContentLimits(token_input_limit=1000)
    metrics = ContentMetrics(token_count=500)
    overflow = ContentMetrics(token_count=0)  # No overflow

    scale = ContentScale(limits=limits, metrics=metrics, overflow=overflow)

    assert scale.limits == limits
    assert scale.metrics == metrics
    assert scale.overflow == overflow
    assert not scale.has_overflow
    assert scale.token_ratio == 0.5
    assert scale.error_message == "Message is valid"


def test_content_scale_model_validation():
    """Test ContentScale model validation"""
    data = {
        "limits": {
            "token_input_limit": 1000,
            "pdf_page_limit": 50,
        },
        "metrics": {
            "token_count": 500,
            "pdf_page_count": 25,
        },
        "overflow": {
            "token_count": 0,
            "pdf_page_count": 0,
        },
    }

    scale = ContentScale.model_validate(data)
    assert scale.limits.token_input_limit == 1000
    assert scale.limits.pdf_page_limit == 50
    assert scale.metrics.token_count == 500
    assert scale.metrics.pdf_page_count == 25
    assert scale.overflow.token_count == 0
    assert scale.overflow.pdf_page_count == 0


def test_content_scale_model_dump():
    """Test ContentScale model dump"""
    limits = ContentLimits(token_input_limit=1000)
    metrics = ContentMetrics(token_count=500)
    scale = ContentScale.create(limits=limits, metrics=metrics)

    data = scale.model_dump()
    assert isinstance(data, dict)
    assert "limits" in data
    assert "metrics" in data
    assert "overflow" in data
    assert "token_ratio" in data
    assert "has_overflow" in data
    assert "error_message" in data

    assert data["limits"]["token_input_limit"] == 1000
    assert data["metrics"]["token_count"] == 500
    assert data["token_ratio"] == 0.5
    assert data["has_overflow"] is False
    assert data["error_message"] == "Message is valid"
