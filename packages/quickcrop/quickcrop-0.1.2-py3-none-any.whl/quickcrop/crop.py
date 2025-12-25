from typing import Optional
from PIL.Image import Image as PILImage
from PIL.Image import new as new_pil_image


def crop(
    original: PILImage, left: int = 0, right: int = 0, top: int = 0, bottom: int = 0
) -> PILImage:
    """
    Crop the specified amount of pixels from the outside of the image
    """
    width, height = original.size
    crop_region = (left, top, width - right, height - bottom)
    return original.crop(crop_region)


def crop_center(
    original: PILImage,
    horizontal: Optional[tuple[int, int]] = None,
    vertical: Optional[tuple[int, int]] = None,
) -> PILImage:
    """
    In vertical and/or horizontal direction:
    When (x, y) is specified, start at pixel x and remove a stripe y pixels wide
    """
    image = original
    if horizontal:
        start, remove = horizontal
        if start + remove > image.width:
            raise ValueError(
                "Image is not wide enough for selected horizontal center crop"
            )
        slice1 = image.crop((0, 0, start - 1, image.height))
        slice2 = image.crop((start + remove, 0, image.width, image.height))
        result_size = (image.width - remove, image.height)
        image = new_pil_image(image.mode, result_size)
        image.paste(slice1, (0, 0))
        image.paste(slice2, (start, 0))
    if vertical:
        start, remove = vertical
        if start + remove > image.height:
            raise ValueError(
                "Image is not wide enough for selected vertical center crop"
            )
        slice1 = image.crop((0, 0, image.width, start - 1))
        slice2 = image.crop((0, start + remove, image.width, image.height))
        result_size = (image.width, image.height - remove)
        image = new_pil_image(image.mode, result_size)
        image.paste(slice1, (0, 0))
        image.paste(slice2, (0, start))
    return image
