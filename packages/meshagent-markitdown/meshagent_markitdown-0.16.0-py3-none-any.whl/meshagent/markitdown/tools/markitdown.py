import aiohttp
import mimetypes
import os
from meshagent.api import EmptyResponse, FileResponse
from meshagent.tools import (
    Tool,
    ToolContext,
    TextResponse,
    get_bytes_from_url,
    RemoteToolkit,
)
import logging
import asyncio
import aiofiles
import markitdown

logger = logging.getLogger("markitdown")


supported_extensions = {
    ".pdf",
    ".docx",
    ".pptx",
    ".docx",
    ".heic",
    ".xlsx",
    # TODO: actually supports more formats, do we want others?
}


class FileMarkItDownTool(Tool):
    def __init__(self):
        super().__init__(
            name="markitdown_from_file",
            title="MarkItDown File Adapter",
            description="Read the contents of a PDF or Office document from a file path",
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["path"],
                "properties": {"path": {"type": "string"}},
            },
        )

    async def execute(self, *, context: ToolContext, path: str):
        filename, ext = os.path.splitext(path)
        if ext in supported_extensions:
            file: FileResponse = await context.room.storage.download(path=path)
            logger.info("adding office metadata for file: {path}".format(path=path))
            async with aiofiles.tempfile.NamedTemporaryFile("wb", suffix=ext) as f:
                await f.write(file.data)
                logger.info("tmp: {path}".format(path=f.name))
                converter = markitdown.MarkItDown()

                def convert():
                    return converter.convert(f.name)

                result = await asyncio.get_event_loop().run_in_executor(None, convert)

                return TextResponse(text=result.text_content)
        else:
            return EmptyResponse()


class UrlMarkItDownTool(Tool):
    def __init__(self):
        super().__init__(
            name="markitdown_from_url",
            title="MarkItDown URL Adapter",
            description="Read the contents of a PDF or Office document from a URL",
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["url"],
                "properties": {"url": {"type": "string"}},
            },
        )

        self._session = aiohttp.ClientSession()

    async def execute(self, *, context: ToolContext, url: str):
        blob = await get_bytes_from_url(url=url)

        ext = mimetypes.guess_extension(blob.mime_type)
        if ext in supported_extensions:
            async with aiofiles.tempfile.NamedTemporaryFile("wb", suffix=ext) as f:
                # TODO: should protect against too large files with maximum file length?
                await f.write(blob.data)

                converter = markitdown.MarkItDown()

                def convert():
                    return converter.convert(f.name)

                result = await asyncio.get_event_loop().run_in_executor(None, convert)

                return TextResponse(text=result.text_content)
        else:
            raise Exception(
                "Unsupported file type, you cannot use this tool to retreive its content"
            )


class MarkItDownToolkit(RemoteToolkit):
    def __init__(self, name="meshagent.markitdown"):
        super().__init__(
            name=name,
            title="markitdown",
            description="MarkItDown is a utility for converting various files to Markdown",
            tools=[
                FileMarkItDownTool(),
                UrlMarkItDownTool(),
            ],
        )
