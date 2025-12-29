import pypandoc
import subprocess
import os

from bluer_options.logger import crash_report

from bluer_objects import file, objects, path
from bluer_objects.env import abcli_path_git
from bluer_objects.logger import logger

css = """
    <style>
        body { font-family: sans-serif; margin: 2cm; }
        img { max-width: 100%; height: auto; }
        table { width: 100%; border-collapse: collapse; word-break: break-word; }
        th, td { border: 1px solid #ccc; padding: 4px; vertical-align: top; }
        code, pre { white-space: pre-wrap; }
    </style>
    """


def convert_md(
    source_filename: str,
    suffix: str,
    object_name: str,
    list_of_pdfs: list[str],
) -> bool:
    filename_html = file.add_extension(
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
        "html",
    )
    filename_pdf = file.add_extension(
        filename_html,
        "pdf",
    )

    if filename_pdf not in list_of_pdfs:
        list_of_pdfs.append(filename_pdf)

    if file.exists(filename_pdf):
        logger.info(f"✅ {filename_pdf}")
        return True

    logger.info(f"{source_filename} -> {filename_pdf}")

    try:
        with open(source_filename, "r", encoding="utf-8") as f:
            markdown_text = f.read()

        html_text = pypandoc.convert_text(
            markdown_text,
            "html",
            format="md",
        )

        html_text = (
            f"<!DOCTYPE html><html><head>{css}</head><body>{html_text}</body></html>"
        )

        if not path.create(
            file.path(filename_html),
            log=True,
        ):
            return (False,)

        with open(
            filename_html,
            "w",
            encoding="utf-8",
        ) as f:
            f.write(html_text)

        subprocess.run(
            [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "--headless",
                "--disable-gpu",
                "--no-margins",
                f"--print-to-pdf={filename_pdf}",
                os.path.abspath(filename_html),
            ],
            check=True,
        )
    except Exception as e:
        crash_report(e)
        return False

    return True
