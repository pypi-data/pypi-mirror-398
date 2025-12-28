from kiarina.llm.content import ContentLimits, ContentMetrics, calculate_overflow


def test_calculate_overflow_no_overflow():
    """Test calculate_overflow with no overflow"""
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

    overflow = calculate_overflow(limits=limits, metrics=metrics)

    assert overflow.token_count == 0
    assert overflow.file_size == 0
    assert overflow.text_file_count == 0
    assert overflow.image_file_count == 0
    assert overflow.audio_duration == 0.0
    assert overflow.audio_file_count == 0
    assert overflow.video_duration == 0.0
    assert overflow.video_file_count == 0
    assert overflow.pdf_page_count == 0
    assert overflow.pdf_file_count == 0


def test_calculate_overflow_token_overflow():
    """Test calculate_overflow with token overflow"""
    limits = ContentLimits(token_input_limit=100)
    metrics = ContentMetrics(token_count=150)

    overflow = calculate_overflow(limits=limits, metrics=metrics)

    assert overflow.token_count == 50
    assert overflow.file_size == 0  # No overflow for other fields


def test_calculate_overflow_file_size_overflow():
    """Test calculate_overflow with file size overflow"""
    limits = ContentLimits(file_size_limit=1024)
    metrics = ContentMetrics(file_size=2048)

    overflow = calculate_overflow(limits=limits, metrics=metrics)

    assert overflow.file_size == 1024
    assert overflow.token_count == 0  # No overflow for other fields


def test_calculate_overflow_text_file_overflow():
    """Test calculate_overflow with text file overflow"""
    limits = ContentLimits(text_file_limit=3)
    metrics = ContentMetrics(text_file_count=7)

    overflow = calculate_overflow(limits=limits, metrics=metrics)

    assert overflow.text_file_count == 4
    assert overflow.token_count == 0  # No overflow for other fields


def test_calculate_overflow_image_file_overflow():
    """Test calculate_overflow with image file overflow"""
    limits = ContentLimits(image_input_enabled=True, image_file_limit=2)
    metrics = ContentMetrics(image_file_count=5)

    overflow = calculate_overflow(limits=limits, metrics=metrics)

    assert overflow.image_file_count == 3
    assert overflow.token_count == 0  # No overflow for other fields


def test_calculate_overflow_audio_duration_overflow():
    """Test calculate_overflow with audio duration overflow"""
    limits = ContentLimits(audio_input_enabled=True, audio_duration_limit=300.0)
    metrics = ContentMetrics(audio_duration=450.0)

    overflow = calculate_overflow(limits=limits, metrics=metrics)

    assert overflow.audio_duration == 150.0
    assert overflow.token_count == 0  # No overflow for other fields


def test_calculate_overflow_audio_file_overflow():
    """Test calculate_overflow with audio file overflow"""
    limits = ContentLimits(audio_input_enabled=True, audio_file_limit=1)
    metrics = ContentMetrics(audio_file_count=4)

    overflow = calculate_overflow(limits=limits, metrics=metrics)

    assert overflow.audio_file_count == 3
    assert overflow.token_count == 0  # No overflow for other fields


def test_calculate_overflow_video_duration_overflow():
    """Test calculate_overflow with video duration overflow"""
    limits = ContentLimits(video_input_enabled=True, video_duration_limit=600.0)
    metrics = ContentMetrics(video_duration=900.0)

    overflow = calculate_overflow(limits=limits, metrics=metrics)

    assert overflow.video_duration == 300.0
    assert overflow.token_count == 0  # No overflow for other fields


def test_calculate_overflow_video_file_overflow():
    """Test calculate_overflow with video file overflow"""
    limits = ContentLimits(video_input_enabled=True, video_file_limit=1)
    metrics = ContentMetrics(video_file_count=3)

    overflow = calculate_overflow(limits=limits, metrics=metrics)

    assert overflow.video_file_count == 2
    assert overflow.token_count == 0  # No overflow for other fields


def test_calculate_overflow_pdf_page_overflow():
    """Test calculate_overflow with PDF page overflow"""
    limits = ContentLimits(pdf_input_enabled=True, pdf_page_limit=50)
    metrics = ContentMetrics(pdf_page_count=80)

    overflow = calculate_overflow(limits=limits, metrics=metrics)

    assert overflow.pdf_page_count == 30
    assert overflow.token_count == 0  # No overflow for other fields


def test_calculate_overflow_pdf_file_overflow():
    """Test calculate_overflow with PDF file overflow"""
    limits = ContentLimits(pdf_input_enabled=True, pdf_file_limit=2)
    metrics = ContentMetrics(pdf_file_count=5)

    overflow = calculate_overflow(limits=limits, metrics=metrics)

    assert overflow.pdf_file_count == 3
    assert overflow.token_count == 0  # No overflow for other fields


def test_calculate_overflow_unlimited_limits():
    """Test calculate_overflow with unlimited limits (-1)"""
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

    overflow = calculate_overflow(limits=limits, metrics=metrics)

    assert overflow.token_count == 0
    assert overflow.file_size == 0
    assert overflow.text_file_count == 0
    assert overflow.image_file_count == 0
    assert overflow.audio_file_count == 0
    assert overflow.video_file_count == 0
    assert overflow.pdf_file_count == 0


def test_calculate_overflow_disabled_inputs():
    """Test calculate_overflow with disabled inputs"""
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

    overflow = calculate_overflow(limits=limits, metrics=metrics)

    # When inputs are disabled, no overflow should occur
    assert overflow.image_file_count == 0
    assert overflow.audio_duration == 0.0
    assert overflow.audio_file_count == 0
    assert overflow.video_duration == 0.0
    assert overflow.video_file_count == 0
    assert overflow.pdf_page_count == 0
    assert overflow.pdf_file_count == 0


def test_calculate_overflow_mixed_overflow():
    """Test calculate_overflow with multiple overflows"""
    limits = ContentLimits(
        token_input_limit=100,
        file_size_limit=1024,
        text_file_limit=2,
        image_file_limit=1,
        audio_duration_limit=300.0,
        audio_file_limit=1,
        video_duration_limit=600.0,
        video_file_limit=1,
        pdf_page_limit=50,
        pdf_file_limit=1,
    )

    metrics = ContentMetrics(
        token_count=200,  # Overflow: 100
        file_size=2048,  # Overflow: 1024
        text_file_count=5,  # Overflow: 3
        image_file_count=3,  # Overflow: 2
        audio_duration=450.0,  # Overflow: 150.0
        audio_file_count=3,  # Overflow: 2
        video_duration=900.0,  # Overflow: 300.0
        video_file_count=3,  # Overflow: 2
        pdf_page_count=80,  # Overflow: 30
        pdf_file_count=4,  # Overflow: 3
    )

    overflow = calculate_overflow(limits=limits, metrics=metrics)

    assert overflow.token_count == 100
    assert overflow.file_size == 1024
    assert overflow.text_file_count == 3
    assert overflow.image_file_count == 2
    assert overflow.audio_duration == 150.0
    assert overflow.audio_file_count == 2
    assert overflow.video_duration == 300.0
    assert overflow.video_file_count == 2
    assert overflow.pdf_page_count == 30
    assert overflow.pdf_file_count == 3


def test_calculate_overflow_edge_cases():
    """Test calculate_overflow edge cases"""
    # Test with zero limits
    limits = ContentLimits(
        token_input_limit=0,
        file_size_limit=0,
        text_file_limit=0,
    )

    metrics = ContentMetrics(
        token_count=1,
        file_size=1,
        text_file_count=1,
    )

    overflow = calculate_overflow(limits=limits, metrics=metrics)

    assert overflow.token_count == 1
    assert overflow.file_size == 1
    assert overflow.text_file_count == 1

    # Test with exact limits (no overflow)
    limits = ContentLimits(
        token_input_limit=100,
        file_size_limit=1024,
    )

    metrics = ContentMetrics(
        token_count=100,  # Exactly at limit
        file_size=1024,  # Exactly at limit
    )

    overflow = calculate_overflow(limits=limits, metrics=metrics)

    assert overflow.token_count == 0
    assert overflow.file_size == 0
