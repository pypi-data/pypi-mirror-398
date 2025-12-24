import sys
from typing import cast

from arcade_mcp_server import MCPApp
from arcade_mcp_server.mcp_app import TransportType

import arcade_google_sheets

app = MCPApp(
    name="GoogleSheets",
    instructions=(
        "Use this server when you need to interact with Google Sheets to enable users to "
        "efficiently manage and access their spreadsheets."
    ),
)

app.add_tools_from_module(arcade_google_sheets)


def main() -> None:
    transport = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    host = sys.argv[2] if len(sys.argv) > 2 else "127.0.0.1"
    port = int(sys.argv[3]) if len(sys.argv) > 3 else 8000

    app.run(transport=cast(TransportType, transport), host=host, port=port)


if __name__ == "__main__":
    main()
