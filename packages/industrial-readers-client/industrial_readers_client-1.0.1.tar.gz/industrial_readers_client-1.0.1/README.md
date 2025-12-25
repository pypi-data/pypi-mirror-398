# Industrial Readers Client

High-performance Python client for the Industrial Readers Server - a blazing-fast document processing service built in Rust.

## Features

- **Multiple Formats**: Excel, Word, PowerPoint, PDF, Images, Text
- **High Performance**: Built for speed with connection pooling
- **Simple API**: Intuitive Python interface
- **Type Hints**: Full typing support
- **Context Manager**: Automatic resource cleanup

## Installation

```bash
pip install industrial-readers-client
```

## Quick Start

```python
from industrial_readers_client import IndustrialReadersClient

# Using context manager (recommended)
with IndustrialReadersClient("http://localhost:9847") as client:
    # Check server health
    health = client.health()
    print(health)  # {"status": "ok", "version": "1.0.0"}
    
    # Auto-detect and read any file
    data = client.read("document.xlsx")
    
    # Read specific formats
    excel_data = client.read_excel("spreadsheet.xlsx", max_rows=1000)
    word_data = client.read_word("document.docx")
    pdf_text = client.read_pdf("document.pdf")
    image_info = client.read_image("photo.jpg")
```

## Server Setup

Run the Industrial Readers Server:

```bash
# Using Docker (recommended)
docker run -p 8080:8080 registry.gitlab.com/soberonlineemail/profilereaders:latest

# Or with docker-compose
curl -O https://gitlab.com/soberonlineemail/profilereaders/-/raw/main/docker-compose.yml
docker-compose up -d
```

## API Reference

### IndustrialReadersClient

#### Constructor
- `base_url` (str): Server URL (default: "http://localhost:8080")
- `timeout` (int): Request timeout in seconds (default: 30)

#### Methods
- `health()` → Dict: Server health status
- `detect(file_path)` → str: Detect file format
- `read(file_path, **params)` → Dict: Auto-detect and read file
- `read_format(file_path, format_type, **params)` → Dict: Read with specific format
- `read_excel(file_path, max_rows=None, max_cells=None)` → Dict: Read Excel files
- `read_word(file_path)` → Dict: Read Word documents
- `read_pdf(file_path)` → Dict: Read PDF files
- `read_image(file_path)` → Dict: Read image metadata

## License

MIT License - see LICENSE file for details.

## Links

- **Source Code**: https://gitlab.com/soberonlineemail/profilereaders
- **Docker Image**: registry.gitlab.com/soberonlineemail/profilereaders:latest
- **Issues**: https://gitlab.com/soberonlineemail/profilereaders/-/issues