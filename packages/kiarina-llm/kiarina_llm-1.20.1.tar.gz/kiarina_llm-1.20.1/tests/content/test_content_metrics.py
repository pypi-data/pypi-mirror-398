from kiarina.llm.content import ContentMetrics


def test_content_metrics_default_values():
    """Test ContentMetrics with default values"""
    metrics = ContentMetrics()

    # Basic properties
    assert metrics.token_count == 0
    assert metrics.file_size == 0
    assert metrics.text_file_count == 0
    assert metrics.image_file_count == 0
    assert metrics.audio_duration == 0.0
    assert metrics.audio_file_count == 0
    assert metrics.video_duration == 0.0
    assert metrics.video_file_count == 0
    assert metrics.pdf_page_count == 0
    assert metrics.pdf_file_count == 0

    # Meta information
    assert metrics.text_token_count == 0
    assert metrics.image_token_count == 0
    assert metrics.audio_token_count == 0
    assert metrics.video_token_count == 0
    assert metrics.pdf_token_count == 0


def test_add_text_token_count():
    """Test add_text_token_count method"""
    metrics = ContentMetrics()

    metrics.add_text_token_count(100)
    assert metrics.text_token_count == 100
    assert metrics.token_count == 100

    metrics.add_text_token_count(50)
    assert metrics.text_token_count == 150
    assert metrics.token_count == 150


def test_add_image_token_count():
    """Test add_image_token_count method"""
    metrics = ContentMetrics()

    metrics.add_image_token_count(200)
    assert metrics.image_token_count == 200
    assert metrics.token_count == 200

    metrics.add_image_token_count(100)
    assert metrics.image_token_count == 300
    assert metrics.token_count == 300


def test_add_audio_token_count():
    """Test add_audio_token_count method"""
    metrics = ContentMetrics()

    metrics.add_audio_token_count(150)
    assert metrics.audio_token_count == 150
    assert metrics.token_count == 150

    metrics.add_audio_token_count(75)
    assert metrics.audio_token_count == 225
    assert metrics.token_count == 225


def test_add_video_token_count():
    """Test add_video_token_count method"""
    metrics = ContentMetrics()

    metrics.add_video_token_count(300)
    assert metrics.video_token_count == 300
    assert metrics.token_count == 300

    metrics.add_video_token_count(200)
    assert metrics.video_token_count == 500
    assert metrics.token_count == 500


def test_add_pdf_token_count():
    """Test add_pdf_token_count method"""
    metrics = ContentMetrics()

    metrics.add_pdf_token_count(80)
    assert metrics.pdf_token_count == 80
    assert metrics.token_count == 80

    metrics.add_pdf_token_count(20)
    assert metrics.pdf_token_count == 100
    assert metrics.token_count == 100


def test_content_metrics_addition():
    """Test ContentMetrics addition operator"""
    metrics1 = ContentMetrics(
        token_count=100,
        file_size=1024,
        text_file_count=2,
        image_file_count=1,
        audio_duration=60.0,
        audio_file_count=1,
        video_duration=120.0,
        video_file_count=1,
        pdf_page_count=5,
        pdf_file_count=1,
        text_token_count=50,
        image_token_count=30,
        audio_token_count=10,
        video_token_count=8,
        pdf_token_count=2,
    )

    metrics2 = ContentMetrics(
        token_count=200,
        file_size=2048,
        text_file_count=3,
        image_file_count=2,
        audio_duration=90.0,
        audio_file_count=2,
        video_duration=180.0,
        video_file_count=2,
        pdf_page_count=10,
        pdf_file_count=2,
        text_token_count=100,
        image_token_count=60,
        audio_token_count=20,
        video_token_count=16,
        pdf_token_count=4,
    )

    result = metrics1 + metrics2

    assert result.token_count == 300
    assert result.file_size == 3072
    assert result.text_file_count == 5
    assert result.image_file_count == 3
    assert result.audio_duration == 150.0
    assert result.audio_file_count == 3
    assert result.video_duration == 300.0
    assert result.video_file_count == 3
    assert result.pdf_page_count == 15
    assert result.pdf_file_count == 3
    assert result.text_token_count == 150
    assert result.image_token_count == 90
    assert result.audio_token_count == 30
    assert result.video_token_count == 24
    assert result.pdf_token_count == 6
