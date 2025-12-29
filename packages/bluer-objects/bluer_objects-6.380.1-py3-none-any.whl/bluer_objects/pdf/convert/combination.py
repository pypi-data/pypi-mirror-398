from typing import List
from PyPDF2 import PdfMerger

from bluer_options.logger import crash_report

from bluer_objects import objects
from bluer_objects.logger import logger


def combine_pdfs(
    list_of_pdfs: List[str],
    object_name: str,
) -> bool:
    logger.info(f"combining {len(list_of_pdfs)} pdf(s)...")
    combined_filename = objects.path_of(
        filename="release.pdf",
        object_name=object_name,
    )

    try:
        merger = PdfMerger()
        for filename in list_of_pdfs:
            merger.append(filename)

        merger.write(combined_filename)
        merger.close()
    except Exception as e:
        crash_report(e)
        return False

    logger.info(f"-> {combined_filename}")
    return True
