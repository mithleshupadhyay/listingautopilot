"""Image upgrade pipeline."""

from listingautopilot.exceptions import ProviderExecutionError
from listingautopilot.image.providers.demo import upgrade_image_demo
from listingautopilot.image.providers.gemini import upgrade_image_gemini
from listingautopilot.image.providers.openai import upgrade_image_openai
from listingautopilot.llm.schemas import ProviderType
from listingautopilot.logging import get_logger
from listingautopilot.schemas.response import ImageBundle


logger = get_logger(__name__)


def upgrade_image(
    image_bytes: bytes,
    image_filename: str,
    image_content_type: str = "image/png",
    provider_type: str = "demo",
    context: dict[str, str | None] | None = None,
    use_demo_mode: bool = False,
) -> ImageBundle:
    if use_demo_mode or provider_type == ProviderType.DEMO.value:
        return upgrade_image_demo(image_bytes=image_bytes, image_filename=image_filename)

    if provider_type == ProviderType.OPENAI.value:
        return upgrade_image_openai(
            image_bytes=image_bytes,
            image_filename=image_filename,
            image_content_type=image_content_type,
            context=context,
    )

    if provider_type == ProviderType.GEMINI.value:
        try:
            return upgrade_image_gemini(
                image_bytes=image_bytes,
                image_filename=image_filename,
                image_content_type=image_content_type,
                context=context,
            )
        except ProviderExecutionError as exc:
            logger.warning(
                "Gemini image provider failed; falling back to demo provider code=%s error=%s",
                exc.code,
                exc.message,
            )
            bundle = upgrade_image_demo(image_bytes=image_bytes, image_filename=image_filename)
            bundle.metadata.update(
                {
                    "fallback_from": ProviderType.GEMINI.value,
                    "fallback_code": exc.code,
                    "fallback_reason": exc.message,
                }
            )
            return bundle

    logger.warning(
        "Image provider %s does not support image editing; using demo provider",
        provider_type,
    )
    bundle = upgrade_image_demo(image_bytes=image_bytes, image_filename=image_filename)
    bundle.metadata.update(
        {
            "fallback_from": provider_type,
            "fallback_code": "IMAGE_PROVIDER_NOT_SUPPORTED",
            "fallback_reason": f"{provider_type} does not support live image editing in this version.",
        }
    )
    return bundle
