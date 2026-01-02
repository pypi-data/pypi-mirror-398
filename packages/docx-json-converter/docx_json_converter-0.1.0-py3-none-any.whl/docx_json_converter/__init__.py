from .parser import convert_docx_to_json
from .builder import convert_json_to_docx

__version__ = "0.1.0"
__all__ = ["convert_docx_to_json", "convert_json_to_docx", "zen"]

def zen():
    print("""The Zen of docx_json_converter

Structured is better than messy
Messy is better than complex
Useful is better than useless
Existence is about serving a master
It could be a master slave relationship
Or maybe a relationship that uplifts you
Or a relationship that puts you down
But it's always gonna be a master slave relationship somewhere
That's for you daddy Hegel (read only 2 pages)
""")
