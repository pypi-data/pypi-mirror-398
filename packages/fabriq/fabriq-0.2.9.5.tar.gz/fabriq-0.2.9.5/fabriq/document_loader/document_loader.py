import re
from markitdown import MarkItDown
import os
from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import EasyOcrOptions, PdfPipelineOptions
from docling.document_converter import (
    DocumentConverter,
    PdfFormatOption,
    PowerpointFormatOption,
    ExcelFormatOption,
    ImageFormatOption,
    HTMLFormatOption,
    CsvFormatOption,
    PatentUsptoFormatOption,
)
from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline
from fabriq.document_loader.doc_utils import (
    convert_to_pdf,
    replace_image,
    transcribe_audio,
)
from langchain_core.documents import Document
from typing import Dict, List, Any, Optional
from docling.utils import model_downloader


class DocumentLoader:
    def __init__(self, config):
        self.config = config
        self._md = MarkItDown(enable_plugins=False, keep_data_uris=True)
        self.multimodal_option = (
            self.config.get("document_loader")
            .get("params")
            .get("multimodal", True)
        )
        self.loader_type = self.config.get("document_loader").get("type", "default")
        self.artifacts_path = (
            self.config.get("document_loader")
            .get("params")
            .get("artifacts_path", "./assets/models")
        )

    def load_document(
        self, file_path: str, mode="single", llm: Optional[Any] = None, metadata: Dict = {}
    ) -> List[Document]:
        """Load the document in Markdown format."""
        self.file_path = file_path

        doc_extension = os.path.basename(self.file_path)

        if mode not in {"single", "pages", "tables"}:
            raise ValueError(
                f"mode parameter should be one of the following: 'single' or 'pages' or 'tables'. Found: {mode}."
            )

        self.download_models()

        if doc_extension.endswith(".xls"):
            markdown_results = self._md.convert(self.file_path, keep_data_uris=True)

        elif doc_extension.endswith((".mp3", ".wav", ".mp4", ".m4a", ".mov", ".avi")):
            markdown_results, metadata = transcribe_audio(self.file_path)

        else:

            if doc_extension.endswith((".doc", ".docx")):
                pdf_path = re.sub(
                    r"\.docx?$", ".pdf", self.file_path, flags=re.IGNORECASE
                )
                if convert_to_pdf(self.file_path, pdf_path) is True:
                    self.file_path = pdf_path

            pipeline_options = PdfPipelineOptions(
                artifacts_path=self.artifacts_path,
                generate_page_images=True,
                generate_picture_images=True,
                images_scale=2,
            )
            if self.loader_type == "ocr":
                pipeline_options.do_ocr = True
                ocr_options = EasyOcrOptions(
                    force_full_page_ocr=True,
                    model_storage_directory=self.artifacts_path,
                    download_enabled=False,
                )
                pipeline_options.generate_page_images = True
                pipeline_options.ocr_options = ocr_options
            else:
                pipeline_options.do_ocr = False

            pipeline_options.do_table_structure = True
            pipeline_options.table_structure_options.do_cell_matching = True

            doc_converter = DocumentConverter(
                allowed_formats=[
                    InputFormat.PDF,
                    InputFormat.IMAGE,
                    InputFormat.HTML,
                    InputFormat.PPTX,
                    InputFormat.CSV,
                    InputFormat.XML_USPTO,
                    InputFormat.XLSX,
                ],
                format_options={
                    InputFormat.PDF: PdfFormatOption(
                        pipeline_cls=StandardPdfPipeline,
                        pipeline_options=pipeline_options,
                    ),
                    InputFormat.IMAGE: ImageFormatOption(
                        pipeline_options=pipeline_options
                    ),
                    InputFormat.PPTX: PowerpointFormatOption(
                        pipeline_options=pipeline_options
                    ),
                    InputFormat.XLSX: ExcelFormatOption(
                        pipeline_options=pipeline_options
                    ),
                    InputFormat.CSV: CsvFormatOption(pipeline_options=pipeline_options),
                    InputFormat.HTML: HTMLFormatOption(
                        pipeline_options=pipeline_options
                    ),
                    InputFormat.XML_USPTO: PatentUsptoFormatOption(
                        pipeline_options=pipeline_options
                    ),
                },
            )

            conv_results = doc_converter.convert(self.file_path)

            if mode == "tables":
                tables = []
                for table in conv_results.document.tables:
                    exported_table = table.export_to_dataframe()
                    tables.append(exported_table)
            else:
                markdown_results = ""
                # for res in conv_results:
                markdown_results += conv_results.document.export_to_markdown(
                    image_placeholder="\n<!-- image -->\n",
                    image_mode="embedded",
                    page_break_placeholder="\n\n-----\n\n",
                )

                if llm is not None:
                    markdown_results = replace_image(markdown_results, llm)

        if mode == "pages":
            result = [
                Document(
                    page_content=doc,
                    metadata={
                        "source": self.file_path,
                        "file_name": os.path.basename(self.file_path),
                        "page_num": page_num + 1**metadata,
                    },
                )
                for page_num, doc in markdown_results.split("\n\n-----\n\n")
            ]
        elif mode == "tables":
            result = tables
        else:
            return [
                Document(
                    page_content=markdown_results,
                    metadata={
                        "source": self.file_path,
                        "file_name": os.path.basename(self.file_path),
                        "page_num": None,
                        **metadata,
                    },
                )
            ]
        return result

    def download_models(self):
        os.makedirs(self.artifacts_path, exist_ok=True)

        if not os.listdir(self.artifacts_path):
            if self.multimodal_option is True:
                model_downloader.download_models(
                    output_dir=Path(self.artifacts_path),
                    with_layout=True,
                    with_tableformer=True,
                    with_easyocr=False,
                    with_code_formula=False,
                    with_picture_classifier=False,
                )
            else:
                model_downloader.download_models(
                    output_dir=Path(self.artifacts_path),
                    with_layout=True,
                    with_tableformer=True,
                    with_easyocr=True,
                    with_code_formula=False,
                    with_picture_classifier=False,
                )
