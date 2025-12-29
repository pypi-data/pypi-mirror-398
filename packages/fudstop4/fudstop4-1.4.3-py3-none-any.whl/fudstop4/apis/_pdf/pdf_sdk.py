import pandas as pd
import asyncio


import os
from PyPDF2 import PdfReader


class PDFSDK:
    def __init__(self):
        pass



    def pdf_folder_to_single_text(self, folder_path: str):
        """
        Combines all PDFs in a folder into one text file in the same folder.
        """

        if not os.path.isdir(folder_path):
            raise ValueError("Provided path is not a valid directory")

        output_path = os.path.join(
            folder_path,
            os.path.basename(os.path.normpath(folder_path)) + "_ALL_TEXT.txt"
        )

        pdf_files = sorted(
            f for f in os.listdir(folder_path)
            if f.lower().endswith(".pdf")
        )

        if not pdf_files:
            raise ValueError("No PDF files found in the folder")

        with open(output_path, "w", encoding="utf-8") as out:
            for pdf in pdf_files:
                pdf_path = os.path.join(folder_path, pdf)

                out.write("\n" + "=" * 80 + "\n")
                out.write(f"FILE: {pdf}\n")
                out.write("=" * 80 + "\n\n")

                try:
                    reader = PdfReader(pdf_path)
                    for page_num, page in enumerate(reader.pages, start=1):
                        text = page.extract_text()
                        if text:
                            out.write(f"\n--- Page {page_num} ---\n")
                            out.write(text + "\n")

                except Exception as e:
                    out.write(f"\n[ERROR reading {pdf}: {e}]\n")

        return output_path