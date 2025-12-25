"""
Prompt templates for AI Code Labeler documentation generation.
"""

# Prompt template for file documentation (using .ai.json metadata)
FILE_DOC_FROM_JSON_TEMPLATE = """You are a technical documentation expert. Create comprehensive, narrative documentation for this code file.

FILE METADATA:
File: {file_name}
Language: {language}
Description: {description}

CLASSES:
{classes_info}

FUNCTIONS:
{functions_info}

NAMESPACES:
{namespaces_info}

DOCUMENTATION REQUIREMENTS:
1. Start with a high-level overview of the file's purpose and role
2. Explain the main classes, their responsibilities, and relationships
3. Detail key functions, their logic flow, and how they interact
4. Use natural prose - avoid rigid section headers
5. Write as if explaining to a fellow developer who is reading the code
6. Focus on WHAT the code does and HOW it works internally
7. Include important implementation details (algorithms, patterns, edge cases)
8. Explain why certain design decisions were made (if apparent from the metadata)
9. Highlight any dependencies or external interactions

OUTPUT FORMAT:
- Write in markdown format
- Use inline code references like `ClassName` and `function_name()`
- Use code blocks sparingly for important patterns
- Keep it narrative and conversational
- Length: 500-2000 words depending on complexity

Generate the documentation now:
"""

# Prompt template for file documentation (using source code directly)
FILE_DOC_FROM_SOURCE_TEMPLATE = """You are a technical documentation expert. Create comprehensive, narrative documentation for this code file.

SOURCE CODE:
```{language}
{source_code}
```

FILE: {file_name}
LANGUAGE: {language}

DOCUMENTATION REQUIREMENTS:
1. Read through the code carefully
2. Start with a high-level overview of the file's purpose
3. Explain classes, functions, and their interactions in detail
4. Use natural prose - write as a walkthrough for someone reading the code
5. Avoid rigid section headers - make it flow naturally
6. Focus on WHAT the code does, HOW it works, and WHY (design rationale)
7. Highlight important patterns, algorithms, and implementation details
8. Explain edge cases and error handling
9. Note dependencies and external interactions

OUTPUT FORMAT:
- Markdown format
- Use inline code like `ClassName` and `function_name()`
- Use code blocks sparingly for important snippets
- Natural, conversational tone
- Length: 500-2000 words depending on complexity

Generate the documentation now:
"""

# Prompt template for directory documentation
DIRECTORY_DOC_TEMPLATE = """You are a technical documentation expert. Create a human-readable overview of this directory.

DIRECTORY: {dir_name}
LOCATION: {relative_path}

DIRECTORY SUMMARY:
Purpose: {purpose}
Key Functionalities: {functionalities}
Main Files: {main_files}
Dependencies: {dependencies}

FILES IN DIRECTORY:
{files_list}

DOCUMENTATION REQUIREMENTS:
1. Write a narrative overview of what this directory contains
2. Explain the directory's role in the larger codebase
3. Describe key files and their purposes in natural prose
4. Explain how files in this directory work together
5. Note important patterns or architectural decisions
6. Keep it concise but informative (300-800 words)
7. Use natural language - avoid bullet lists and rigid structure
8. Write as if orienting a new developer to this part of the codebase

OUTPUT FORMAT:
- Markdown format
- Natural, flowing prose
- Use inline code references like `filename.cpp` or `ClassName`
- Conversational tone
- Focus on the "big picture" of what this directory does

Generate the directory overview now:
"""

# Prompt template for merging chunked documentation
CHUNK_MERGE_TEMPLATE = """You are a technical documentation expert. Merge these per-chunk documentation segments into a single, cohesive narrative.

FILE: {file_name}
CHUNKS: {num_chunks}

CHUNK DOCUMENTATION:
{chunk_docs}

MERGE REQUIREMENTS:
1. Create a unified, flowing narrative (not separate sections)
2. Eliminate redundancy between chunks
3. Ensure smooth transitions between concepts from different chunks
4. Maintain technical accuracy
5. Keep natural, conversational tone
6. Remove any chunk-specific references (like "this chunk covers...")

Generate the merged documentation:
"""
