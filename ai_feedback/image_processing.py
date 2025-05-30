import base64
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv
from ollama import chat, Message, Image
from openai import OpenAI
from PIL import Image as PILImage
from .helpers.arg_options import Models
from .helpers.image_extractor import extract_images
from .helpers.image_reader import *
from .helpers.template_utils import render_prompt_template, gather_image_context, gather_image_size, gather_images


def encode_image(image_path: os.PathLike) -> bytes:
    """Encodes the image found at {image_path} to a base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def openai_call(message: Message, model: str) -> str | None:
    """Sends a request to OpenAI"""
    # Load environment variables from .env file
    load_dotenv()
    client = OpenAI()
    images = [
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{encode_image(image.value)}"},
        }
        for image in message.images
    ]
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": message.content,
                    }
                ]
                + images,
            }
        ],
        temperature=0.33,
    )
    return completion.choices[0].message.content


def anthropic_call(message: Message, model: str) -> str | None:
    """Sends a request to OpenAI"""
    # Load environment variables from .env file
    load_dotenv()
    client = Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))
    images = [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": f"{encode_image(image.value)}",
            },
        }
        for image in message.images
    ]
    message = client.messages.create(
        max_tokens=2048,
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": message.content,
                    }
                ]
                + images,
            }
        ],
        temperature=0.33,
    )
    return message.content[0].text


def process_image(args, prompt: dict) -> tuple[str, str]:
    """Generates feedback for an image submission.
    Returns the LLM prompt delivered and the returned response."""
    OUTPUT_DIRECTORY = "output_images"
    submission_notebook = Path("./", args.assignment, "student_submission.ipynb")
    solution_notebook = Path("./", args.assignment, "solution.ipynb")

    # Extract submission images
    extract_images(submission_notebook, OUTPUT_DIRECTORY, "submission")
    # Optionally extract solution images
    if solution_notebook.is_file():
        extract_images(solution_notebook, OUTPUT_DIRECTORY, "solution")

    if args.question:
        questions = [args.question]
    else:
        questions = os.listdir(OUTPUT_DIRECTORY)

    requests: list[str] = []
    responses: list[str] = []
    for question in questions:
        # Use template rendering system for all prompt building
        content = prompt["prompt_content"]
        
        # Gather template data
        template_data = {}
        
        if "{context}" in content:
            context = gather_image_context(OUTPUT_DIRECTORY, question)
            template_data["context"] = "```\n" + context + "\n```"
            
        if "{image_size}" in content:
            template_data["image_size"] = gather_image_size(OUTPUT_DIRECTORY, question)
        
        # Render template
        if template_data:
            content = render_prompt_template(content, **template_data)
        
        # Gather images for attachment
        include_images = prompt.get("include_images", [])
        message = Message(role="user", content=content, images=gather_images(OUTPUT_DIRECTORY, question, include_images))

        # Gather images based on boolean flags
        images = []
        if prompt.get("include_submission_image", False):
            try:
                submission_image_paths = read_submission_images(OUTPUT_DIRECTORY, question)
                if submission_image_paths:
                    images.append(Image(value=submission_image_paths[0]))
            except Exception as e:
                print(f"Error loading submission image: {e}")
                
        if prompt.get("include_solution_image", False):
            try:
                solution_image_paths = read_solution_images(OUTPUT_DIRECTORY, question)
                if solution_image_paths:
                    images.append(Image(value=solution_image_paths[0]))
            except Exception as e:
                print(f"Error loading solution image: {e}")
        
        message = Message(role="user", content=content, images=images)

        # Prompt the LLM
        requests.append(
            f"{message.content}\n\n{[str(image.value) for image in message.images]}"
        )
        if args.model == Models.OPENAI.value:
            responses.append(openai_call(message, model="gpt-4o"))
        elif args.model == Models.CLAUDE.value:
            responses.append(
                anthropic_call(message, model="claude-3-7-sonnet-20250219")
            )
        else:
            responses.append(
                chat(
                    model=args.model, messages=[message], options={"temperature": 0.33}
                ).message.content
            )

    return "\n\n---\n\n".join(requests), "\n\n---\n\n".join(responses)
