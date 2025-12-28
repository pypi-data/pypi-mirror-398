import argparse
import os
from collections import defaultdict
import datetime
import chromadb
from rich.console import Console
from rich.table import Table

def delete_file_from_collections(base_path: str, filename: str):
    """Delete a specific file from all collections in ChromaDB."""
    console = Console()
    abs_path = os.path.abspath(os.path.join(base_path, "data/chroma_db"))

    if not os.path.exists(abs_path):
        console.print(f"[bold red]Error:[/bold red] Path does not exist: [yellow]{abs_path}[/yellow]")
        return False

    client = chromadb.PersistentClient(path=abs_path)
    collections = client.list_collections()

    if not collections:
        console.print(f"[bold red]No collections found at:[/bold red] [yellow]{abs_path}[/yellow]")
        return False

    deleted_count = 0
    total_collections_checked = 0

    for collection in collections:
        # Handle both string names and Collection objects
        collection_name = collection if isinstance(collection, str) else collection.name
        col = client.get_collection(collection_name)
        data = col.get()  # fetch all documents
        
        # Find entries for this filename
        entries_to_delete = []
        for i, meta in enumerate(data["metadatas"]):
            if not meta:
                continue
            
            # Check if this entry matches our filename
            if "file_name" in meta and meta["file_name"] == filename:
                entries_to_delete.append(data["ids"][i])
            elif "document_name" in meta and meta["document_name"] == filename:
                entries_to_delete.append(data["ids"][i])
            elif "filename" in meta and meta["filename"] == filename:
                entries_to_delete.append(data["ids"][i])
        
        if entries_to_delete:
            console.print(f"[yellow]Found {len(entries_to_delete)} entries for '{filename}' in collection '{collection_name}'[/yellow]")
            col.delete(ids=entries_to_delete)
            deleted_count += len(entries_to_delete)
            console.print(f"[green]✅ Deleted {len(entries_to_delete)} entries from collection '{collection_name}'[/green]")
        
        total_collections_checked += 1

    if deleted_count > 0:
        console.print(f"\n[bold green]Successfully deleted {deleted_count} total entries for '{filename}' across {total_collections_checked} collections[/bold green]")
        return True
    else:
        console.print(f"\n[bold yellow]No entries found for '{filename}' in any collection[/bold yellow]")
        return False


def summarize_collections(base_path: str):
    """Summarize all collections in a Chroma persistent DB at the document level."""
    console = Console()
    abs_path = os.path.abspath(os.path.join(base_path, "data/chroma_db"))

    if not os.path.exists(abs_path):
        console.print(f"[bold red]Error:[/bold red] Path does not exist: [yellow]{abs_path}[/yellow]")
        return

    client = chromadb.PersistentClient(path=abs_path)
    collections = client.list_collections()

    if not collections:
        console.print(f"[bold red]No collections found at:[/bold red] [yellow]{abs_path}[/yellow]")
        return

    for collection in collections:
        # Handle both string names and Collection objects
        collection_name = collection if isinstance(collection, str) else collection.name
        col = client.get_collection(collection_name)
        data = col.get()  # fetch all documents

        # Build document-level summary
        doc_summary = defaultdict(lambda: {"embeddings": 0, "file_size": 0, "upload_date": None})
        for meta in data["metadatas"]:
            if not meta:
                continue
            
            # Handle different collection types (prioritize new standardized field)
            if "file_name" in meta:
                # New standardized field name
                name = meta["file_name"]
            elif "document_name" in meta:
                # Legacy documents collection
                name = meta["document_name"]
            elif "filename" in meta:
                # Legacy images collection
                name = meta["filename"]
            else:
                continue
                
            doc_summary[name]["embeddings"] += 1
            doc_summary[name]["file_size"] = meta.get("file_size", 0)
            if meta.get("upload_date"):
                date_obj = datetime.datetime.fromisoformat(meta["upload_date"])
                existing = doc_summary[name]["upload_date"]
                # Keep earliest upload date per document
                if existing is None or date_obj < existing:
                    doc_summary[name]["upload_date"] = date_obj

        # Print summary table
        table = Table(title=f"Collection: {collection_name}", show_header=True, header_style="bold magenta")
        table.add_column("File Name", style="cyan")
        table.add_column("Embeddings", style="green")
        table.add_column("File Size (MB)", style="yellow")
        table.add_column("Upload Date", style="white")

        for name, info in sorted(doc_summary.items()):
            file_size_mb = f"{info['file_size'] / (1024*1024):.2f}"  # convert bytes to MB
            upload_date = info["upload_date"].strftime("%Y-%m-%d %H:%M:%S") if info["upload_date"] else "N/A"
            table.add_row(name, str(info["embeddings"]), file_size_mb, upload_date)

        console.print(table)
        console.print("\n")  # extra spacing between collections


def main():
    parser = argparse.ArgumentParser(description="Summarize ChromaDB collections at document level.")
    parser.add_argument(
        "-u", "--url",
        type=str,
        required=True,
        help="Base path to data folder (script appends /chroma_db)"
    )
    parser.add_argument(
        "-d", "--delete",
        type=str,
        help="Delete a specific file from all collections (provide filename)"
    )
    args = parser.parse_args()
    
    if args.delete:
        # Delete mode
        delete_file_from_collections(args.url, args.delete)
    else:
        # Summary mode
        summarize_collections(args.url)


if __name__ == "__main__":
    main()
