# OutfitAI

- [개요](#개요)
- [설치 방법](#설치-방법)
- [사용 방법](#사용-방법)
- [설정 관리](#설정-관리)
- [참고 사항](#참고-사항)

## 개요

AI 기반의 의류 이미지 분류 도구입니다. 의류 이미지를 분석하여 색상, 카테고리, 드레스 코드, 계절 정보를 JSON 형태로 출력합니다.

### 주요 기능

- 다양한 AI 지원 (OpenAI 및 Gemini)
- 이미지 분류 (색상, 카테고리, 드레스 코드, 계절)
- CLI 및 라이브러리 형태로 사용 가능
- 단일 이미지 및 배치 처리 지원
- 비동기 처리를 통한 성능 최적화
- 유연한 설정 관리
- 로컬 이미지 및 이미지 URL 지원

#### 분류 항목

- **색상**: white, gray, black, red, orange, yellow, green, blue, indigo, purple, other
- **카테고리**: tops, bottoms, outerwear, dresses, shoes, bags, hats, accessories, other
- **드레스 코드**: casual wear, business attire, campus style, date night outfit, travel wear, wedding attire, loungewear, resort wear, other
- **계절**: spring, summer, fall, winter

### 시스템 요구사항

- Python 3.9+

## 설치 방법

### 1. [PyPI](https://pypi.org/project/outfitai/)를 통한 설치 (권장)

```bash
pip install outfitai
```

### 2. 소스코드를 통한 설치

```bash
# 저장소 복제
git clone https://github.com/23tae/outfitai.git
cd outfitai

# 패키지 설치
pip install -e .
```

## 사용 방법

- 사용 전 API 정보 설정이 필요합니다 ([설정 관리](#설정-관리) 참고)
- 지원하는 이미지 파일 형식:
  - OpenAI: PNG(.png), JPEG(.jpeg, .jpg), WEBP(.webp), non-animated GIF(.gif)
  - Gemini: PNG(.png), JPEG(.jpeg, .jpg), WEBP(.webp)

### 1. 라이브러리로 사용

Python 코드에서 다음과 같이 사용할 수 있습니다:

```python
from outfitai import Settings, ClassifierFactory
import asyncio

# 방법 1: 환경 변수나 .env 파일 사용
classifier = ClassifierFactory.create_classifier()

# 방법 2: 직접 설정
settings = Settings(
    OUTFITAI_PROVIDER="openai",
    OPENAI_API_KEY="your-api-key"
)

classifier = ClassifierFactory.create_classifier(settings)

# 단일 이미지 처리
async def process_single():
  # 방법 1: 로컬 이미지 사용
    result = await classifier.classify_single("path/to/image.jpg")
    print(result)

  # 방법 2: 이미지 URL 사용
    result = await classifier.classify_single("https://example.com/image.jpg")
    print(result)

asyncio.run(process_single())

# 다중 이미지 처리
async def process_batch():
    # 디렉토리에서 처리
    results = await classifier.classify_batch("path/to/images/")
    # 또는 파일 목록으로 처리
    results = await classifier.classify_batch(["image1.jpg", "image2.jpg"])
    print(results)

asyncio.run(process_batch())
```

### 2. CLI 사용

단일 이미지 처리 및 결과 표시:
```bash
outfitai path/to/image.jpg
```

결과를 파일로 저장:
```bash
outfitai path/to/image.jpg --output result.json
```

디렉토리 내 모든 이미지 처리:
```bash
outfitai path/to/images/ --batch
```

#### CLI 옵션

```
필수:
  IMAGE_PATH          이미지 파일이나 디렉토리의 경로 또는 이미지 URL

선택:
  --batch, -b         디렉토리 내 모든 이미지 처리
  --output, -o FILE   결과를 JSON 파일로 저장
```

### 출력 예시

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

## 설정 관리

### API 정보 설정

1. 환경 변수 사용 (권장):
    ```bash
    # OpenAI 사용 시
    export OUTFITAI_PROVIDER=openai
    export OPENAI_API_KEY=your-api-key

    # Gemini 사용 시
    export OUTFITAI_PROVIDER=gemini
    export GEMINI_API_KEY=your-api-key
    ```

2. `.bashrc` 또는 `.zshrc` 설정:
    ```bash
    # OpenAI 사용 시
    echo 'export OUTFITAI_PROVIDER=openai' >> ~/.bashrc
    echo 'export OPENAI_API_KEY=your-api-key' >> ~/.bashrc

    # Gemini 사용 시
    echo 'export OUTFITAI_PROVIDER=gemini' >> ~/.bashrc
    echo 'export GEMINI_API_KEY=your-api-key' >> ~/.bashrc
    ```

3. 프로젝트 루트에 `.env` 파일 생성:
    ```
    # OpenAI 사용 시
    OUTFITAI_PROVIDER=openai
    OPENAI_API_KEY=your_api_key

    # Gemini 사용 시
    OUTFITAI_PROVIDER=gemini
    GEMINI_API_KEY=your_api_key
    ```

4. 코드에서 직접 설정:
    ```python
    # OpenAI 사용 시
    settings = Settings(
        OUTFITAI_PROVIDER="openai",
        OPENAI_API_KEY="your-api-key"
    )
    classifier = ClassifierFactory.create_classifier(settings)

    # Gemini 사용 시
    settings = Settings(
        OUTFITAI_PROVIDER="gemini",
        GEMINI_API_KEY="your-api-key"
    )
    classifier = ClassifierFactory.create_classifier(settings)
    ```

### 설정 가능한 옵션

모든 설정은 환경 변수, `.env` 파일, 또는 코드에서 직접 설정할 수 있습니다:

- 필수 사항:
  - `OPENAI_API_KEY`: OpenAI API 키 (OpenAI 사용 시)
  - `GEMINI_API_KEY`: Gemini API 키 (Gemini 사용 시)
- 선택 사항:
  - `OUTFITAI_PROVIDER`: 사용할 API 제공자 ("openai" 또는 "gemini")
  - `OPENAI_MODEL`: 사용할 OpenAI 모델 (기본값: gpt-4o-mini)
  - `GEMINI_MODEL`: 사용할 Gemini 모델 (기본값: gemini-2.5-flash)

커스텀 설정 예시:
```python
settings = Settings(
    OUTFITAI_PROVIDER="gemini",
    GEMINI_API_KEY="your-api-key",
    GEMINI_MODEL="gemini-2.5-flash",
)
classifier = ClassifierFactory.create_classifier(settings)
```

## 참고 사항

- API 제공자와 모델에 따라 비용이 다릅니다.
  - [OpenAI 비용](https://platform.openai.com/docs/pricing)
  - [Gemini 비용](https://ai.google.dev/pricing)
- 라이브러리로 사용 시 메서드가 비동기(async)임을 유의바랍니다.
- 라이브러리가 자동으로 이미지 크기를 최적화합니다.
- GIF 형식은 OpenAI에서만 지원됩니다.
