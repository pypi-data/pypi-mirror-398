from PIL import Image

from bluer_options.logger import crash_report

from bluer_objects import file, objects, path
from bluer_objects.env import abcli_path_git
from bluer_objects.logger import logger


def convert_image(
    source_filename: str,
    suffix: str,
    object_name: str,
    list_of_pdfs: list[str],
) -> bool:
    logger.info("🌠 image found!")
    filename_pdf = file.add_extension(
        objects.path_of(
            filename="docs/{}".format(
                (
                    suffix.split(abcli_path_git, 1)[1]
                    if abcli_path_git in suffix
                    else suffix
                ),
            ),
            object_name=object_name,
        ),
        "pdf",
    )

    if filename_pdf not in list_of_pdfs:
        list_of_pdfs.append(filename_pdf)

    if file.exists(filename_pdf):
        logger.info(f"✅ {filename_pdf}")
        return True

    if not path.create(
        file.path(filename_pdf),
        log=True,
    ):
        return False

    try:
        image = Image.open(source_filename)
        image = image.convert("RGB")
        image.save(filename_pdf)
    except Exception as e:
        crash_report(e)
        return False

    logger.info(f"-> {filename_pdf}")
    return True
