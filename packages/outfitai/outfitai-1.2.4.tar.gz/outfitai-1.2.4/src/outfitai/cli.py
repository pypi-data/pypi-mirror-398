import click
import json
from pathlib import Path
import asyncio
from typing import Optional
from urllib.parse import urlparse
from .classifier.factory import ClassifierFactory
from .config.settings import Settings
from .error.exceptions import ClothingClassifierError


def validate_image_path(ctx, param, value):
    try:
        # Check URL
        result = urlparse(value)
        if all([result.scheme, result.netloc]):
            return value

        # Check local file/directory
        path = Path(value)
        if not path.exists():
            raise click.BadParameter(f"File or directory not found: {value}")
        return str(path)

    except Exception as e:
        raise click.BadParameter(f"Invalid image path or URL: {value}")


async def process_images(
    classifier_factory: ClassifierFactory,
    settings: Settings,
    image_path: str,
    batch: bool
) -> list:
    try:
        classifier = classifier_factory.create_classifier(settings)

        if batch:
            if not Path(image_path).is_dir():
                raise click.UsageError("Batch mode requires a directory path")
            return await classifier.classify_batch(image_path)
        else:
            return [await classifier.classify_single(image_path)]

    except Exception as e:
        raise ClothingClassifierError(f"Error processing images: {str(e)}")


def save_results(results: list, output_path: Optional[str]) -> None:
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        click.echo(f"Results saved to {output_path}")
    else:
        click.echo(json.dumps(results, indent=2, ensure_ascii=False))


@click.group()
def cli():
    """OutfitAI: AI-powered clothing image classification tool."""
    pass


@cli.command()
@click.argument('image_path', callback=validate_image_path)
@click.option('--batch', '-b', is_flag=True, help='Process multiple images from directory')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
def classify(
    image_path: str,
    batch: bool,
    output: Optional[str],
):
    """Classify clothing items in images"""
    try:
        settings = Settings()

        # 이미지 처리
        results = asyncio.run(
            process_images(ClassifierFactory, settings, image_path, batch)
        )

        # 결과 저장/출력
        save_results(results, output)

    except ClothingClassifierError as e:
        click.echo(f"Classification error: {str(e)}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"Unexpected error: {str(e)}", err=True)
        raise click.Abort()
