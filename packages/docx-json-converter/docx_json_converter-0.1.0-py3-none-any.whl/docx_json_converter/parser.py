import logging
from typing import Dict, List, Any, Optional
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

logger = logging.getLogger(__name__)

def get_run_formatting(run) -> Dict[str, Any]:
    """
    Extracts formatting information from a single run.
    """
    return {
        "bold": bool(run.bold),
        "italic": bool(run.italic),
        "underline": bool(run.underline),
        "font_size": run.font.size.pt if run.font.size else None
    }

def get_block_type(paragraph, runs_data: List[Dict]) -> str:
    """
    Determines the block type.
    """
    if paragraph.style and paragraph.style.name.startswith('List'):
        return "list_item"
    
    alignment = paragraph.alignment
    if not paragraph.text.strip():
        return "empty"

    is_bold = False
    if runs_data:
        is_bold = runs_data[0].get('formatting', {}).get('bold', False)

    if alignment == WD_ALIGN_PARAGRAPH.CENTER and is_bold:
        return "title"
    
    if (alignment == WD_ALIGN_PARAGRAPH.LEFT or alignment is None) and is_bold:
        return "section_header"
        
    return "paragraph"

def get_document_metadata(doc: Document) -> Dict[str, Any]:
    """
    Extracts document-level metadata like column count from the first section.
    """
    metadata = {}
    try:
        section = doc.sections[0]
        sectPr = section._sectPr
        cols = sectPr.xpath('./w:cols')
        if cols:
            # 'num' attribute defaults to 1 if missing
            num_str = cols[0].get(qn('w:num'))
            metadata['columns'] = int(num_str) if num_str else 1
        else:
            metadata['columns'] = 1
    except Exception as e:
        logger.warning(f"Could not extract metadata: {e}")
        metadata['columns'] = 1
        
    return metadata

def convert_docx_to_json(file_path: str, include_formatting: bool = True) -> Dict[str, Any]:
    """
    Parses a .docx file into a structured JSON format.
    """
    try:
        doc = Document(file_path)
    except Exception as e:
        logger.error(f"Failed to load document: {e}")
        return {"error": str(e)}

    # Extract Metadata
    metadata = get_document_metadata(doc)
    blocks = []

    for paragraph in doc.paragraphs:
        if not paragraph.text.strip():
            continue

        runs_data = []
        if include_formatting:
            for run in paragraph.runs:
                if not run.text:
                    continue
                runs_data.append({
                    "text": run.text,
                    "formatting": get_run_formatting(run)
                })
        else:
            runs_data.append({
                "text": paragraph.text,
                "formatting": {}
            })

        alignment_map = {
            WD_ALIGN_PARAGRAPH.LEFT: "left",
            WD_ALIGN_PARAGRAPH.CENTER: "center",
            WD_ALIGN_PARAGRAPH.RIGHT: "right",
            WD_ALIGN_PARAGRAPH.JUSTIFY: "justify",
            None: "left"
        }
        
        block_alignment = alignment_map.get(paragraph.alignment, "left")
        block_type = get_block_type(paragraph, runs_data if include_formatting else [])

        block = {
            "text": paragraph.text,
            "block_type": block_type,
            "formatting": {
                "alignment": block_alignment,
            } if include_formatting else {},
            "runs": runs_data
        }
        
        blocks.append(block)

    return {
        "metadata": metadata,
        "blocks": blocks
    }
