from fastapi import FastAPI
import uvicorn
import typer

app = FastAPI(title="Docker Agent", version="0.1.0")
cli = typer.Typer(add_completion=False)


@app.get("/")
async def root():
    return {"message": "Docker Agent API", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

@cli.callback(invoke_without_command=True)
def main(
    host: str = typer.Option("0.0.0.0", help="서버 호스트"),
    port: int = typer.Option(8250, help="서버 포트"),
    reload: bool = typer.Option(False, help="개발 모드 자동 리로드"),
):
    """
    Docker Agent 서버를 시작합니다.
    """
    typer.echo(f"Docker Agent를 {host}:{port}에서 시작합니다...")
    uvicorn.run(
        "agent.main:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    cli()

