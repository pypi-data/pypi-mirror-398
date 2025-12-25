import argparse
import asyncio
import base64
import json
import logging
import sys
from typing import Any
from typing import cast

from amsdal.manager import AmsdalManager
from amsdal.manager import AsyncAmsdalManager
from amsdal_utils.config.data_models.amsdal_config import AmsdalConfig
from amsdal_utils.config.manager import AmsdalConfigManager
from mcp.server.fastmcp import FastMCP

from amsdal_ml.agents.retriever_tool import retriever_search

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler('server.log'), logging.StreamHandler(sys.stdout)],
)

parser = argparse.ArgumentParser()
parser.add_argument('--amsdal-config', required=False, help='Base64-encoded config string')
args = parser.parse_args()

logging.info(f'Starting server with args: {args}')

if args.amsdal_config:
    decoded = base64.b64decode(args.amsdal_config).decode('utf-8')
    amsdal_config = AmsdalConfig(**json.loads(decoded))
    logging.info(f'Loaded Amsdal config: {amsdal_config}')
    AmsdalConfigManager().set_config(amsdal_config)

    manager: Any
    if amsdal_config.async_mode:
        manager = AsyncAmsdalManager()
        logging.info('pre-setup')
        asyncio.run(cast(Any, manager).setup())
        logging.info('post-setup')
        asyncio.run(cast(Any, manager).post_setup())
        logging.info('manager inited')
    else:
        manager = AmsdalManager()
        cast(Any, manager).setup()
        cast(Any, manager).post_setup()

server = FastMCP('retriever-stdio')
server.tool(
    name='search',
    description='Semantic search in knowledge base (OpenAI embeddings)',
    structured_output=True,
)(retriever_search)

server.run(transport='stdio')
