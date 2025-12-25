# supermaker-ai-video-downloader

Generate branded links and HTML anchors for [https://supermaker.ai/video/](https://supermaker.ai/video/).

## Installation

```bash
pip install supermaker-ai-video-downloader
```

## Usage

### Generate Links

```python
from supermaker_ai_video_downloader import build_link

# Basic link
url = build_link()

# Link with UTM parameters
url = build_link(
    utm_source="github",
    utm_medium="readme",
    utm_campaign="launch"
)

# Link with path
url = build_link(path="features", utm_source="blog")
```

### Generate HTML Anchors

```python
from supermaker_ai_video_downloader import generate_anchor

# Basic anchor
html = generate_anchor("Click here")

# Custom attributes
html = generate_anchor(
    text="Visit website",
    utm_source="twitter",
    utm_medium="social",
    utm_campaign="promotion",
    css_class="btn btn-primary"
)
```

## Official Website

[https://supermaker.ai/video/](https://supermaker.ai/video/)
