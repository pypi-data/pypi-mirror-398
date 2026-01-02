# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['fast_sentence_segment',
 'fast_sentence_segment.bp',
 'fast_sentence_segment.core',
 'fast_sentence_segment.dmo',
 'fast_sentence_segment.svc']

package_data = \
{'': ['*']}

install_requires = \
['spacy>=3.8.0,<4.0.0']

setup_kwargs = {
    'name': 'fast-sentence-segment',
    'version': '1.1.8',
    'description': 'Fast and Efficient Sentence Segmentation',
    'long_description': '# Fast Sentence Segmentation\n\n[![PyPI version](https://img.shields.io/pypi/v/fast-sentence-segment.svg)](https://pypi.org/project/fast-sentence-segment/)\n[![Python versions](https://img.shields.io/pypi/pyversions/fast-sentence-segment.svg)](https://pypi.org/project/fast-sentence-segment/)\n[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)\n[![spaCy](https://img.shields.io/badge/spaCy-3.5-blue.svg)](https://spacy.io/)\n\nFast and efficient sentence segmentation using spaCy. Handles complex edge cases like abbreviations (Dr., Mr., etc.), quoted text, and multi-paragraph documents.\n\n## Features\n\n- **Paragraph-aware segmentation**: Returns sentences grouped by paragraph\n- **Abbreviation handling**: Correctly handles "Dr.", "Mr.", "etc." without false splits\n- **Cached processing**: LRU cache for repeated text processing\n- **Flexible output**: Nested lists (by paragraph) or flattened list of sentences\n- **Bullet point & numbered list normalization**: Cleans common list formats\n\n## Installation\n\n```bash\npip install fast-sentence-segment\n```\n\nAfter installation, download the spaCy model:\n\n```bash\npython -m spacy download en_core_web_sm\n```\n\n## Quick Start\n\n```python\nfrom fast_sentence_segment import segment_text\n\ntext = "Here is a Dr. who says something. And then again, what else? I don\'t know. Do you?"\n\nresults = segment_text(text)\n# Returns: [[\'Here is a Dr. who says something.\', \'And then again, what else?\', "I don\'t know.", \'Do you?\']]\n```\n\n## Usage\n\n### Basic Segmentation\n\nThe `segment_text` function returns a list of lists, where each inner list represents a paragraph containing its sentences:\n\n```python\nfrom fast_sentence_segment import segment_text\n\ntext = """First paragraph here. It has two sentences.\n\nSecond paragraph starts here. This one also has multiple sentences. And a third."""\n\nresults = segment_text(text)\n# Returns:\n# [\n#     [\'First paragraph here.\', \'It has two sentences.\'],\n#     [\'Second paragraph starts here.\', \'This one also has multiple sentences.\', \'And a third.\']\n# ]\n```\n\n### Flattened Output\n\nIf you don\'t need paragraph boundaries, use the `flatten` parameter:\n\n```python\nresults = segment_text(text, flatten=True)\n# Returns: [\'First paragraph here.\', \'It has two sentences.\', \'Second paragraph starts here.\', ...]\n```\n\n### Direct Segmenter Access\n\nFor more control, use the `Segmenter` class directly:\n\n```python\nfrom fast_sentence_segment import Segmenter\n\nsegmenter = Segmenter()\nresults = segmenter.input_text("Your text here.")\n```\n\n## API Reference\n\n| Function | Parameters | Returns | Description |\n|----------|------------|---------|-------------|\n| `segment_text()` | `input_text: str`, `flatten: bool = False` | `list` | Main entry point for segmentation |\n| `Segmenter.input_text()` | `input_text: str` | `list[list[str]]` | Cached paragraph-aware segmentation |\n\n## Why Nested Lists?\n\nThe segmentation process preserves document structure by segmenting into both paragraphs and sentences. Each outer list represents a paragraph, and each inner list contains that paragraph\'s sentences. This is useful for:\n\n- Document structure analysis\n- Paragraph-level processing\n- Maintaining original text organization\n\nUse `flatten=True` when you only need sentences without paragraph context.\n\n## Requirements\n\n- Python 3.8.5+\n- spaCy 3.5.3\n- en_core_web_sm spaCy model\n\n## License\n\nMIT License - see [LICENSE](LICENSE) for details.\n\n## Contributing\n\nContributions are welcome! Please feel free to submit a Pull Request.\n\n1. Fork the repository\n2. Create your feature branch (`git checkout -b feature/amazing-feature`)\n3. Run tests (`make test`)\n4. Commit your changes\n5. Push to the branch\n6. Open a Pull Request\n',
    'author': 'Craig Trim',
    'author_email': 'craigtrim@gmail.com',
    'maintainer': 'Craig Trim',
    'maintainer_email': 'craigtrim@gmail.com',
    'url': 'https://github.com/craigtrim/fast-sentence-segment',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.9,<4.0',
}


setup(**setup_kwargs)
