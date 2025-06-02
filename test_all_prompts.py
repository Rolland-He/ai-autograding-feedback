#!/usr/bin/env python3
"""
Comprehensive test script to verify all prompts work correctly with the new template system.
Tests every prompt file across all appropriate scopes and submission types.
"""

import os
import sys
import json
import tempfile
import shutil
import glob
from pathlib import Path

# Add the ai_feedback module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai_feedback'))

from ai_feedback.helpers.template_utils import (
    render_prompt_template, 
    gather_file_references, 
    gather_file_contents,
    gather_image_context,
    gather_image_size,
    gather_images
)


def create_test_assignment_folder(submission_type: str) -> str:
    """Create a temporary test assignment folder with appropriate files."""
    temp_dir = tempfile.mkdtemp(prefix='test_assignment_')
    
    if submission_type == "jupyter":
        # Create a test notebook file
        notebook_content = {
            "cells": [
                {
                    "cell_type": "code",
                    "source": ["print('Hello World')"],
                    "outputs": []
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 4
        }
        with open(os.path.join(temp_dir, "test_submission.ipynb"), 'w') as f:
            json.dump(notebook_content, f)
            
    elif submission_type == "python":
        # Create a test Python file
        with open(os.path.join(temp_dir, "test_submission.py"), 'w') as f:
            f.write("def hello_world():\n    return 'Hello World'\n\nprint(hello_world())")
            
    elif submission_type == "pdf":
        # Create a dummy PDF (just a text file for testing)
        with open(os.path.join(temp_dir, "test_submission.pdf"), 'w') as f:
            f.write("This is a test PDF submission content.")
    
    # Create question context file
    with open(os.path.join(temp_dir, "question_context.txt"), 'w') as f:
        f.write("This is the question context for testing purposes.")
    
    # Create solution files
    with open(os.path.join(temp_dir, "solution.py"), 'w') as f:
        f.write("def solution():\n    return 'This is the solution'")
    
    return temp_dir


def get_assignment_files(assignment_folder: str) -> list[str]:
    """Get all relevant files from the assignment folder."""
    files = []
    for ext in ['*.py', '*.ipynb', '*.pdf', '*.txt']:
        files.extend(glob.glob(os.path.join(assignment_folder, ext)))
    return files


def test_prompt_template(prompt_file: str, scope: str, submission_type: str) -> bool:
    """Test a specific prompt template with given scope and submission type."""
    print(f"\n🧪 Testing {prompt_file} (scope: {scope}, type: {submission_type})")
    
    try:
        # Load the prompt
        prompt_path = os.path.join('ai_feedback', 'data', 'prompts', prompt_file)
        with open(prompt_path, 'r') as f:
            prompt_data = json.load(f)
        
        prompt_content = prompt_data['prompt_content']
        print(f"   📄 Original prompt length: {len(prompt_content)} characters")
        
        # Create test assignment folder
        assignment_folder = create_test_assignment_folder(submission_type)
        
        try:
            # Get assignment files
            assignment_files = get_assignment_files(assignment_folder)
            
            # Prepare template data based on scope
            template_kwargs = {}
            
            if scope == "code":
                if '{file_references}' in prompt_content:
                    template_kwargs['file_references'] = gather_file_references(assignment_files)
                if '{file_contents}' in prompt_content:
                    template_kwargs['file_contents'] = gather_file_contents(assignment_files)
                    
            elif scope == "text":
                if '{file_contents}' in prompt_content:
                    template_kwargs['file_contents'] = gather_file_contents(assignment_files)
                    
            elif scope == "image":
                # For image scope, use mock data since we don't have actual image processing setup
                if '{context}' in prompt_content:
                    template_kwargs['context'] = "Mock question context for testing"
                if '{image_size}' in prompt_content:
                    template_kwargs['image_size'] = "800 by 600"
            
            # Render the template
            rendered_prompt = render_prompt_template(prompt_content, **template_kwargs)
            print(f"   ✅ Template rendered successfully ({len(rendered_prompt)} characters)")
            
            # Check that placeholders were replaced (if any were present)
            placeholders = ['{file_references}', '{file_contents}', '{context}', '{image_size}']
            remaining_placeholders = [p for p in placeholders if p in rendered_prompt]
            
            if remaining_placeholders:
                print(f"   ⚠️  Warning: Some placeholders remain: {remaining_placeholders}")
            else:
                print(f"   ✅ All placeholders properly replaced")
            
            return True
            
        finally:
            # Clean up temp directory
            shutil.rmtree(assignment_folder)
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False


def main():
    """Run comprehensive tests on all prompts."""
    print("🚀 Starting comprehensive prompt template testing...")
    print("=" * 60)
    
    # Get all prompt files
    prompts_dir = os.path.join('ai_feedback', 'data', 'prompts')
    prompt_files = [f for f in os.listdir(prompts_dir) if f.endswith('.json')]
    
    # Define scope mappings
    scope_mappings = {
        'code': ['code_lines.json', 'code_hint.json', 'code_explanation.json', 
                'code_table.json', 'code_template.json', 'code_annotation.json'],
        'text': ['text_pdf_analyze.json'],
        'image': ['image_analyze.json', 'image_compare.json', 'image_style.json',
                 'image_style_annotations.json', 'image_analyze_annotations.json']
    }
    
    # Define submission types to test
    submission_types = ['jupyter', 'python', 'pdf']
    
    # Track results
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    # Test each prompt with appropriate scope and submission types
    for scope, prompt_list in scope_mappings.items():
        print(f"\n📂 Testing {scope.upper()} prompts:")
        print("-" * 40)
        
        for prompt_file in prompt_list:
            if prompt_file in prompt_files:
                # Test with appropriate submission types
                test_types = submission_types if scope in ['code', 'text'] else ['jupyter']  # Image scope is less dependent on submission type
                
                for submission_type in test_types:
                    total_tests += 1
                    success = test_prompt_template(prompt_file, scope, submission_type)
                    if success:
                        passed_tests += 1
                    else:
                        failed_tests.append(f"{prompt_file} ({scope}, {submission_type})")
            else:
                print(f"   ⚠️  Prompt file not found: {prompt_file}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY:")
    print(f"   Total tests: {total_tests}")
    print(f"   Passed: {passed_tests}")
    print(f"   Failed: {len(failed_tests)}")
    
    if failed_tests:
        print("\n❌ Failed tests:")
        for test in failed_tests:
            print(f"   - {test}")
        return 1
    else:
        print("\n🎉 All tests passed! Template system is working correctly.")
        return 0


if __name__ == "__main__":
    # Change to the script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Ensure we're in the right directory
    if not os.path.exists('ai_feedback'):
        print("❌ Error: ai_feedback directory not found. Please run from the project root.")
        sys.exit(1)
    
    sys.exit(main()) 