import os
import sys
import re
from typing import List, Optional, Tuple
from dotenv import load_dotenv
import openai
import PyPDF2
from .Model import Model
from ..helpers.constants import SYSTEM_INSTRUCTIONS

load_dotenv()


class OpenAIModel(Model):
    def __init__(self) -> None:
        """
        Initialize an OpenAIModel instance.

        Loads the OpenAI API key from environment variables and prepares the client.
        """
        super().__init__()
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def generate_response(
        self,
        prompt: str,
        assignment_files: List[str],
        scope: Optional[str] = None,
        question_num: Optional[int] = None,
    ) -> Tuple[str, str]:
        """
        Generate a response based on the given prompt and assignment context.

        Args:
            prompt (str): The user's prompt to feed into the model.
            assignment_files (List[str]): Paths to files to include in the prompt.
            scope (Optional[str]): The content scope.
            question_num (Optional[int]): Specific question number to focus on.

        Returns:
            Tuple[str, str]: The full prompt and the generated response from OpenAI.
        """
        if question_num:
            prompt += f" Identify and generate a response for the mistakes **only** in task {question_num}. "
            file_contents = self._get_question_contents(assignment_files, question_num)
        elif scope == "text":
            file_contents = self._get_pdf_contents(assignment_files)
        else:
            file_contents = self._get_file_contents(assignment_files)

        request = f"{SYSTEM_INSTRUCTIONS}\n\nPrompt: {prompt}\nFiles to Reference:\n{file_contents}"
        response = self._call_openai(request)
        return request, response

    def _get_file_contents(self, assignment_files: List[str]) -> str:
        """
        Retrieve contents from all provided files.

        Args:
            assignment_files (List[str]): List of file paths.

        Returns:
            str: Combined content of all files, formatted with line numbers.
        """
        file_contents = ""

        for file_path in assignment_files:
            file_name = os.path.basename(file_path)
            try:
                with open(file_path, "r") as file:
                    lines = file.readlines()
            except Exception as e:
                print(f"Error reading file {file_name}: {e}")
                continue

            file_contents += f"=== {file_name} ===\n"
            for i, line in enumerate(lines, start=1):
                stripped_line = line.rstrip("\n")
                if stripped_line.strip():
                    file_contents += f"(Line {i}) {stripped_line}\n"
                else:
                    file_contents += f"(Line {i}) {line}"
            file_contents += "\n"

        return file_contents

    def _get_pdf_contents(self, assignment_files: List[str]) -> str:
        """
        Retrieve and combine text extracted from PDF files.

        Args:
            assignment_files (List[str]): List of PDF file paths.

        Returns:
            str: Combined extracted text from all PDF files.
        """
        combined_content = ""
        for file_path in assignment_files:
            file_name = os.path.basename(file_path)
            pdf_content = self._extract_text_from_pdf(file_path)
            combined_content += f"{file_name}:\n{pdf_content}\n\n"

        return combined_content

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract and clean text content from a single PDF file.

        Args:
            pdf_path (str): Path to the PDF file.

        Returns:
            str: Extracted text organized by page.
        """
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page_num, page in enumerate(reader.pages):
                raw_text = page.extract_text()
                if not raw_text:
                    continue
                cleaned_text = raw_text.strip()
                text += f"Page {page_num}:\n{cleaned_text}\n\n"
        return text

    def _get_question_contents(
        self, assignment_files: List[str], question_num: int
    ) -> str:
        """
        Retrieve contents of files specifically for a targeted question number.

        Assumes files follow a specific markdown-like structure with sections titled
        '## Introduction' and '## Task {question_num}'.

        Args:
            assignment_files (List[str]): List of assignment file paths.
            question_num (int): The question number to extract.

        Returns:
            str: Extracted content relevant to the specific question.

        Raises:
            SystemExit: If the question number is not found in any file.
        """
        file_contents = ""
        task_found = False

        for file_path in assignment_files:
            if (
                not file_path.endswith(".txt")
                or "error_output" in file_path
                or file_path.endswith(".DS_Store")
            ):
                continue

            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()

            intro_match = re.search(
                r"(## Introduction\b.*?)(?=\n##|\Z)", content, re.DOTALL
            )
            intro_content = intro_match.group(1).strip() if intro_match else ""

            task_pattern = rf"(## Task {question_num}\b.*?)(?=\n##|\Z)"
            task_match = re.search(task_pattern, content, re.DOTALL)

            if task_match:
                task_content = task_match.group(1).strip()
                task_found = True

            file_contents += f"\n\n---\n### {file_path}\n\n"
            file_contents += intro_content + "\n\n" if intro_content else ""
            file_contents += task_content + "\n\n"

        if not task_found:
            print(f"Task {question_num} not found in any assignment file.")
            sys.exit(1)

        return file_contents.strip()

    def _call_openai(self, prompt: str) -> str:
        """
        Send a prompt to OpenAI's chat completion API and retrieve the generated response.

        Args:
            prompt (str): The fully constructed input prompt including file content.

        Returns:
            str: The model's response text.
        """
        response = self.client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTIONS},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1000,
            temperature=0.5,
        )
        return response.choices[0].message.content
