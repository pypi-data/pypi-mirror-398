import json
import os
import re

from ....api import ScoutAPI
from scouttypes.conversations.conversation_message import ConversationMessage
from scouttypes.conversations.message_role import MessageRole


class ContentExtractor:
    def __init__(self) -> None:
        self.api = ScoutAPI()

    def execute_prompt(
        self, system: str, user: str, model: str = "gpt-4.1-mini"
    ) -> str:
        result = self.api.chat.completion(
            messages=[
                ConversationMessage(role=MessageRole.SYSTEM, content=system),
                ConversationMessage(role=MessageRole.USER, content=user),
            ],
            model=model,
            allowed_tools=[],
        )
        return str(result.messages[0].content)

    def extract_text_document(self, file_path: str) -> dict:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        res = self.api.utils.chunk_document(file_path=file_path)
        chunks = res.get("file", {}).get("chunks")
        references = [chunk.get("metadata") for chunk in chunks]
        headers = [
            " -> ".join(reference.get("hierarchy", []))
            for reference in references
            if reference is not None
        ]
        headers = list(dict.fromkeys(headers))
        table_of_content = list(dict.fromkeys(filter(None, headers)))
        return {"table_of_content": json.dumps(table_of_content), "chunks": chunks}

    def cleanup_html(self, html: str) -> str:
        clean_html = re.sub(r"<[^>]+>", " ", html).replace("NaN", "")
        return clean_html

    def summarize_file(self, powerpoint_text_content: str, local_path: str) -> str:
        filename = os.path.basename(local_path)
        filename_lower = filename.lower()
        prompt = ""
        if filename_lower.endswith((".ppt", ".pptx")):
            prompt = self.summarize_powerpoint_prompt
        elif filename_lower.endswith((".xls", ".xlsx", ".csv", ".ods")):
            prompt = self.summarize_spreadsheet_prompt
        else:
            prompt = self.summarize_generic_document_prompt

        return self.execute_prompt(
            user=powerpoint_text_content, system=prompt, model="gpt41"
        )

    def extract_speadsheet_sheet(self, sheet: dict) -> dict:
        sheet_name = sheet.get("sheet_name")
        sheet_content = sheet.get("html_table", "")
        header, rest = sheet_content.split("<thead>")[1].split("</thead>")
        rows = rest.replace("</tbody></table>", "").replace("<tbody>", "").split("<tr>")
        rows = [self.cleanup_html(row) for row in rows if row.strip() not in [None, ""]]
        sheet_first_20_rows = [header] + rows[:19]

        excerpt = json.dumps(sheet_first_20_rows)

        return {
            "sheet_name": sheet_name,
            "excerpt": excerpt,
            "rows": rows,
        }

    def extract_spreadsheet_document(self, file_path: str) -> dict:
        data = self.api.utils.get_document_text(file_path)
        import shutil

        shutil.copy(file_path, "/tmp")
        sheets = json.loads(data.get("file", {}).get("content", {}))
        return {"sheets": [self.extract_speadsheet_sheet(sheet) for sheet in sheets]}

    summarize_spreadsheet_prompt = """
The user will give you a sheet excerpt containing data. Your task is to create a summary of approximately 100 words describing the content and purpose of the data in the sheet. 

Focus only on the named column headers and describe their relevance or the type of information they represent. 

Do not mention unnamed columns, the fact that it is a spreadsheet, or its association with the Bahamut project unless explicitly stated in the sheet. 

For example: The datasheet represents measurements of gains and losses, with additional columns detailing voltage levels and specific gain values. Notably, the sheet includes entries for 'gain en db,' 'perte,' and other specified metrics, suggesting an analysis of the instrument's efficiency and signal integrity at different settings."""

    summarize_powerpoint_prompt = """
The user will give you text content extracted from a PowerPoint presentation. Your task is to create a summary of approximately 100 words describing the content and purpose of the presentation. Focus on the key topics, themes, and main points presented in the slides. Do not mention the fact that it is a PowerPoint presentation, only mention content that are present in the document. For example: The presentation outlines a new product development strategy, covering market analysis, technical specifications, and implementation timeline. Key sections include competitor benchmarking, feature prioritization, and resource allocation plans, suggesting a comprehensive product launch roadmap for stakeholders.
"""

    summarize_generic_document_prompt = """
The user will give you text content extracted from a document. Your task is to create a summary of approximately 100 words describing the content and purpose of the document. Focus on the central topics, main arguments, and key sections present in the text. Do not mention the document type or its association with any project unless explicitly stated in the content. For example: The document provides a detailed overview of a business initiative, describing objectives, methodologies, and expected outcomes. It highlights important findings, recommendations, and action steps, offering stakeholders a clear understanding of the subject matter’s significance and implications.
"""
