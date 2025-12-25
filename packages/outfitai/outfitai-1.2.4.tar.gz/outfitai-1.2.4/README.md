# OutfitAI

- [Description](#description)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Notes](#notes)

## Description

AI-powered clothing image classification tool. The tool analyzes clothing images and outputs color, category, dress code, and seasonal information in JSON format.

### Features

- Multiple AI provider support (OpenAI and Gemini)
- Image classification (color, category, dress code, season)
- Both CLI and library usage support
- Single image and batch processing support
- Performance optimization through async processing
- Flexible configuration management
- Support for both local file and image URL

#### Classification Criteria

- **Color**: white, gray, black, red, orange, yellow, green, blue, indigo, purple, other
- **Category**: tops, bottoms, outerwear, dresses, shoes, bags, hats, accessories, other
- **Dress code**: casual wear, business attire, campus style, date night outfit, travel wear, wedding attire, loungewear, resort wear, other
- **Season**: spring, summer, fall, winter

### Requirements

- Python 3.9+

## Installation

### 1. Install from [PyPI](https://pypi.org/project/outfitai/) (Recommended)

```bash
pip install outfitai
```

### 2. Install from source

```bash
# Clone repository
git clone https://github.com/23tae/outfitai.git
cd outfitai

# Install package
pip install -e .
```

## Usage

- Set up API credentials before use (see [Configuration](#configuration))
- Supported image file formats: 
  - OpenAI: PNG(.png), JPEG(.jpeg, .jpg), WEBP(.webp) and non-animated GIF(.gif)
  - Gemini: PNG(.png), JPEG(.jpeg, .jpg), WEBP(.webp)

### 1. As a Library

You can use it in your Python code:

```python
from outfitai import Settings, ClassifierFactory
import asyncio

# Method 1: Use environment variables or .env file
classifier = ClassifierFactory.create_classifier()

# Method 2: Direct settings
settings = Settings(
    OUTFITAI_PROVIDER="openai",
    OPENAI_API_KEY="your-api-key"
)

classifier = ClassifierFactory.create_classifier(settings)

# Process single image
async def process_single():
    # Method 1: From local file
    result = await classifier.classify_single("path/to/image.jpg")
    print(result)
    
    # Method 2: From URL
    result = await classifier.classify_single("https://example.com/image.jpg")
    print(result)

asyncio.run(process_single())

# Process multiple images
async def process_batch():
    # From directory
    results = await classifier.classify_batch("path/to/images/")
    # Or from list of files
    results = await classifier.classify_batch(["image1.jpg", "image2.jpg"])
    print(results)

asyncio.run(process_batch())
```

### 2. Command Line Interface

Process a single image and display results:
```bash
outfitai path/to/image.jpg
```

Save results to file:
```bash
outfitai path/to/image.jpg --output result.json
```

Process all images in a directory:
```bash
outfitai path/to/images/ --batch
```

#### CLI Options

```
Required:
  IMAGE_PATH          Path to image file/directory or image URL

Optional:
  --batch, -b         Process all images in directory
  --output, -o FILE   Save results to JSON file
```

### Example Output

```json
[
  {
    "image_path": "path/to/image.jpg",
    "color": "indigo",
    "category": "outerwear",
    "dress_code": "casual wear",
    "season": ["spring", "fall"]
  }
]
```

## Configuration

### Setting API Credentials

1. Environment variables (Recommended):
    ```bash
    # For OpenAI
    export OUTFITAI_PROVIDER=openai
    export OPENAI_API_KEY=your-api-key

    # For Gemini
    export OUTFITAI_PROVIDER=gemini
    export GEMINI_API_KEY=your-api-key
    ```

2. In `.bashrc` or `.zshrc`:
    ```bash
    # For OpenAI
    echo 'export OUTFITAI_PROVIDER=openai' >> ~/.bashrc
    echo 'export OPENAI_API_KEY=your-api-key' >> ~/.bashrc

    # For Gemini
    echo 'export OUTFITAI_PROVIDER=gemini' >> ~/.bashrc
    echo 'export GEMINI_API_KEY=your-api-key' >> ~/.bashrc
    ```

3. `.env` file in project root:
    ```
    # For OpenAI
    OUTFITAI_PROVIDER=openai
    OPENAI_API_KEY=your_api_key

    # For Gemini
    OUTFITAI_PROVIDER=gemini
    GEMINI_API_KEY=your_api_key
    ```

4. Direct in code:
    ```python
    # For OpenAI
    settings = Settings(
        OUTFITAI_PROVIDER="openai",
        OPENAI_API_KEY="your-api-key"
    )
    classifier = ClassifierFactory.create_classifier(settings)

    # For Gemini
    settings = Settings(
        OUTFITAI_PROVIDER="gemini",
        GEMINI_API_KEY="your-api-key"
    )
    classifier = ClassifierFactory.create_classifier(settings)
    ```

### Available Settings

All settings can be configured through environment variables, `.env` file, or in code:

- Required:
  - `OPENAI_API_KEY`: OpenAI API key (required when using OpenAI)
  - `GEMINI_API_KEY`: Gemini API key (required when using Gemini)
- Optional:
  - `OUTFITAI_PROVIDER`: API provider to use ("openai" or "gemini") (default: openai)
  - `OPENAI_MODEL`: OpenAI model to use (default: gpt-4o-mini)
  - `GEMINI_MODEL`: Gemini model to use (default: gemini-2.5-flash)

Example of using custom settings:
```python
settings = Settings(
    OUTFITAI_PROVIDER="gemini",
    GEMINI_API_KEY="your-api-key",
    GEMINI_MODEL="gemini-2.5-flash",
)
classifier = ClassifierFactory.create_classifier(settings)
```

## Notes

- API costs vary by provider and model.
  - [OpenAI pricing](https://platform.openai.com/docs/pricing)
  - [Google Gemini pricing](https://ai.google.dev/pricing)
- When using as a library, remember that the classifier methods are asynchronous.
- The library automatically handles image size optimization.
- GIF support is only available with the OpenAI provider.
