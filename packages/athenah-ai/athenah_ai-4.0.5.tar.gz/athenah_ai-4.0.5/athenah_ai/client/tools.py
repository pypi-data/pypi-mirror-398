#!/usr/bin/env python


from athenah_ai.logger import logger
from athenah_ai.client import AthenahClient


def get_relevant_file_names(
    client: AthenahClient, query: str, max_files: int = 10
) -> list:
    try:
        # Run similarity search with scores
        results = client.db.similarity_search(query, k=500)
        import json

        results = json.loads(results) if isinstance(results, str) else results
        # print(results[0])
        # results: List[Tuple[Document, float]]
        # Filter by min_score and sort by score descending
        # filtered = [
        #     (doc)
        #     for doc in results
        #     # if score >= min_score
        #     and hasattr(doc.metadata, "get")
        #     and doc.metadata.get("source")
        # ]
        # Sort by score descending
        # results.sort(key=lambda x: x[1], reverse=True)
        # Extract file paths (assuming 'source' in metadata is the file path)
        file_paths = []
        for doc in results:
            # print(doc)
            file_path = doc.metadata.get("file_path")
            if file_path and file_path not in file_paths:
                _file_path = file_path.replace(
                    "/root/athena-ai/", "/Users/darkmatter/projects/transia/athena-ai/"
                )
                file_paths.append(
                    {
                        "path": _file_path,
                        "content": doc.page_content,
                    }
                )
            if len(file_paths) >= max_files:
                break
        return file_paths
    except Exception as e:
        logger.error(f"Error in get_relevant_file_names: {e}")
        return []
