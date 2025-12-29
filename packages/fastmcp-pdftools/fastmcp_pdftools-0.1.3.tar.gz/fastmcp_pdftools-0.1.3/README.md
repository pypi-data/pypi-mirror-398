# PDF Reader

mcp-name: io.github.atarkowska/fastmcp-pdftools

This project is a simple PDF reader server allowing to read  PDF files.

## Configuration

[](https://github.com/atarkowska/fastmcp-pdftools/blob/main/README.md#configuration)

Add the following to your `claude_desktop_config.json`:

```json
{
    "mcpServers": {
        "fastmcp-pdftools": {
            "command": "uvx",
            "args": [
                "fastmcp-pdftools"
            ]
        }
    }
}
```

## License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).
See the LICENSE file for details.
