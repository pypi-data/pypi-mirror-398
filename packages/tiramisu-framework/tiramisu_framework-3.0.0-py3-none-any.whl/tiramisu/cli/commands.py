"""
Tiramisu Framework CLI
Copyright (c) 2025 Jony Wolff. All rights reserved.
"""
import click
import os
import shutil
from pathlib import Path

@click.group()
def cli():
    """🍰 Tiramisu Framework - Multi-expert RAG system"""
    pass

@cli.command()
@click.argument('name')
def init(name):
    """Initialize a new Tiramisu project"""
    project_path = Path(name)
    
    if project_path.exists():
        click.echo(f"❌ Directory {name} already exists")
        return
    
    # Create project structure
    project_path.mkdir()
    (project_path / "data").mkdir()
    (project_path / "data" / "documents").mkdir()
    (project_path / "config").mkdir()
    
    # Create config file
    config_content = """# Tiramisu Configuration
model: gpt-4o
chunk_size: 800
chunk_overlap: 150
top_k: 5
temperature: 0.7
"""
    (project_path / "config" / "config.yaml").write_text(config_content)
    
    # Create .env template
    env_content = """OPENAI_API_KEY=your-key-here
EMBEDDING_MODEL=text-embedding-ada-002
"""
    (project_path / ".env").write_text(env_content)
    
    click.echo(f"✅ Project '{name}' initialized successfully!")
    click.echo(f"📁 Next steps:")
    click.echo(f"   1. cd {name}")
    click.echo(f"   2. Add your documents to data/documents/")
    click.echo(f"   3. tiramisu build-index")
    click.echo(f"   4. tiramisu run")

@cli.command()
@click.argument('path', type=click.Path(exists=True))
def add_docs(path):
    """Add documents to knowledge base"""
    documents_dir = Path("data/documents")
    
    if not documents_dir.exists():
        click.echo("❌ Not in a Tiramisu project. Run 'tiramisu init' first.")
        return
    
    source_path = Path(path)
    
    if source_path.is_file():
        shutil.copy2(source_path, documents_dir)
        click.echo(f"✅ Added: {source_path.name}")
    elif source_path.is_dir():
        for file in source_path.glob("**/*.{txt,pdf,md}"):
            shutil.copy2(file, documents_dir)
            click.echo(f"✅ Added: {file.name}")
    
    click.echo("📚 Documents added successfully!")

@cli.command()
@click.option('--force', is_flag=True, help='Force rebuild even if index exists')
def build_index(force):
    """Build FAISS vector index from documents"""
    from tiramisu.core.indexer import build_faiss_index
    
    documents_dir = Path("data/documents")
    index_dir = Path("data/faiss_index")
    
    if not documents_dir.exists():
        click.echo("❌ No documents directory found. Run 'tiramisu init' first.")
        return
    
    if index_dir.exists() and not force:
        click.echo("⚠️  Index already exists. Use --force to rebuild.")
        return
    
    click.echo("🔨 Building FAISS index...")
    
    try:
        num_chunks = build_faiss_index(documents_dir, index_dir)
        click.echo(f"✅ Index built successfully with {num_chunks} chunks!")
    except Exception as e:
        click.echo(f"❌ Error building index: {e}")

@cli.command()
@click.option('--port', default=8000, help='Port to run the server on')
@click.option('--host', default='127.0.0.1', help='Host to bind to')
def run(port, host):
    """Start the Tiramisu API server"""
    import uvicorn
    
    click.echo(f"🍰 Starting Tiramisu server on http://{host}:{port}")
    click.echo(f"📚 API docs: http://{host}:{port}/docs")
    
    uvicorn.run(
        "tiramisu.api.main:app",
        host=host,
        port=port,
        reload=True
    )

@cli.command()
def version():
    """Show Tiramisu version"""
    from tiramisu import __version__
    click.echo(f"Tiramisu Framework v{__version__}")

if __name__ == "__main__":
    cli()
