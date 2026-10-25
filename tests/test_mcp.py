import pytest
pytest.importorskip('mcp')
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio
import os
import sys
from oncosignal.config import Settings
from oncosignal.pipeline import ResearchWorkspace

def test_actual_mcp_stdio(tmp_path):
    ResearchWorkspace(Settings(tmp_path)).demo()
    async def check():
        env={**os.environ,'ONCO_WORKSPACE':str(tmp_path)}
        params=StdioServerParameters(command=sys.executable,args=['-m','oncosignal.mcp_server'],env=env)
        async with stdio_client(params) as (read,write):
            async with ClientSession(read,write) as session:
                await session.initialize()
                tools=await session.list_tools()
                assert {t.name for t in tools.tools}=={'search_evidence','get_record','quality_report','trial_publication_links'}
                result=await session.call_tool('search_evidence',{'query':'melanoma','limit':2})
                assert not result.isError
                assert 'melanoma' in str(result.content).lower()
    asyncio.run(check())
