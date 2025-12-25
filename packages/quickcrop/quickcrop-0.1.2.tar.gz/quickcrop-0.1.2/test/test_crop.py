from pathlib import Path

from PIL.Image import Image as PILImage
from PIL.Image import open as pil_open
from PIL.ImageChops import difference

from quickcrop import crop


_IMAGE_DIR = (Path(__file__).parent / "test_images").resolve()


def have_same_format(image1: PILImage, image2: PILImage) -> bool:
    return image1.size == image2.size


def are_identical(image1: PILImage, image2: PILImage) -> bool:
    try:
        diff = difference(
            image1=image1.convert("RGBA"),
            image2=image2.convert("RGBA"),
        )
    except ValueError:
        return False
    return diff.getbbox() is None


def test_crop_all_sides():
    base_image = pil_open(_IMAGE_DIR / "base_image_crop.png")
    all_cropped = crop.crop(base_image, 10, 10, 10, 10)
    target_image = pil_open(_IMAGE_DIR / "crop_10px_all_sides.png")
    assert have_same_format(all_cropped, target_image)
    assert are_identical(all_cropped, target_image)


def test_crop_left():
    base_image = pil_open(_IMAGE_DIR / "base_image_crop.png")
    cropped = crop.crop(base_image, left=10)
    target_image = pil_open(_IMAGE_DIR / "crop_10px_left.png")
    assert have_same_format(cropped, target_image)
    assert are_identical(cropped, target_image)


def test_crop_top():
    base_image = pil_open(_IMAGE_DIR / "base_image_crop.png")
    cropped = crop.crop(base_image, top=10)
    target_image = pil_open(_IMAGE_DIR / "crop_10px_top.png")
    assert have_same_format(cropped, target_image)
    assert are_identical(cropped, target_image)


def test_crop_right():
    base_image = pil_open(_IMAGE_DIR / "base_image_crop.png")
    cropped = crop.crop(base_image, right=10)
    target_image = pil_open(_IMAGE_DIR / "crop_10px_right.png")
    assert have_same_format(cropped, target_image)
    assert are_identical(cropped, target_image)


def test_crop_bottom():
    base_image = pil_open(_IMAGE_DIR / "base_image_crop.png")
    cropped = crop.crop(base_image, bottom=10)
    target_image = pil_open(_IMAGE_DIR / "crop_10px_bottom.png")
    assert have_same_format(cropped, target_image)
    assert are_identical(cropped, target_image)


def test_crop_center_horizontal():
    base_image = pil_open(_IMAGE_DIR / "base_image_crop.png")
    cropped = crop.crop_center(base_image, horizontal=(49, 2))
    target_image = pil_open(_IMAGE_DIR / "crop_2px_center_horizontal.png")
    assert have_same_format(cropped, target_image)
    assert are_identical(cropped, target_image)


def test_crop_center_vertical():
    base_image = pil_open(_IMAGE_DIR / "base_image_crop.png")
    cropped = crop.crop_center(base_image, vertical=(49, 2))
    target_image = pil_open(_IMAGE_DIR / "crop_2px_center_vertical.png")
    assert have_same_format(cropped, target_image)
    assert are_identical(cropped, target_image)


def test_crop_center_both():
    base_image = pil_open(_IMAGE_DIR / "base_image_crop.png")
    cropped = crop.crop_center(base_image, horizontal=(49, 2), vertical=(49, 2))
    target_image = pil_open(_IMAGE_DIR / "crop_2px_center_both.png")
    assert have_same_format(cropped, target_image)
    assert are_identical(cropped, target_image)
