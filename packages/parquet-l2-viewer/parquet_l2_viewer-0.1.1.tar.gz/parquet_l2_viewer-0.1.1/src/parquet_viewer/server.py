from __future__ import annotations

from pathlib import Path
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import duckdb


def create_app(data_dir: Path) -> FastAPI:
    app = FastAPI()
    data_dir = data_dir.resolve()

    web_dir = Path(__file__).parent / "web"
    assets_dir = web_dir / "assets"

    # 前端静态文件
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/")
    def index():
        return FileResponse(web_dir / "index.html")
    
    @app.get("/vite.svg")
    def vite_svg():
        p = web_dir / "vite.svg"
        if p.exists():
            return FileResponse(p)
        return {"ok": False}

    # 兼容 Vite build 生成的 /vite.html（如果有）
    @app.get("/vite.html")
    def vite_html():
        p = web_dir / "vite.html"
        if p.exists():
            return FileResponse(p)
        return {"ok": False, "error": "vite.html not found"}

    @app.get("/contracts")
    def get_contracts(file: str = Query(...)):
        file_path = (data_dir / file).resolve()
        if not file_path.exists():
            return {"error": f"file not found: {file}"}

        con = duckdb.connect(database=":memory:")

        q = f"""
        SELECT DISTINCT Contract
        FROM read_parquet('{file_path.as_posix()}')
        ORDER BY Contract
        """
        rows = con.execute(q).fetchall()
        return {"file": file, "contracts": [r[0] for r in rows]}

    @app.get("/rows")
    def get_rows(
        file: str,
        limit: int = 200,
        contract: str | None = None,
        start: str | None = None,
        end: str | None = None,
    ):
        file_path = (data_dir / file).resolve()
        if not file_path.exists():
            return {"error": f"file not found: {file}"}

        con = duckdb.connect(database=":memory:")

        ts_expr = """
        coalesce(
          try_strptime(CAST(Date AS VARCHAR) || ' ' || TimeStr, '%Y%m%d %H:%M:%S.%f'),
          try_strptime(CAST(Date AS VARCHAR) || ' ' || TimeStr, '%Y%m%d %H:%M:%S')
        )
        """

        filters = []

        if contract:
            safe_contract = contract.replace("'", "''")
            filters.append(f"Contract = '{safe_contract}'")

        def time_literal(s: str) -> str:
            safe = s.replace("'", "''")
            return (
                "coalesce("
                f"try_strptime('{safe}', '%Y-%m-%d %H:%M:%S.%f'), "
                f"try_strptime('{safe}', '%Y-%m-%d %H:%M:%S')"
                ")"
            )

        if start:
            filters.append(f"{ts_expr} >= {time_literal(start)}")
        if end:
            filters.append(f"{ts_expr} < {time_literal(end)}")  # [start, end)

        where_sql = ""
        if filters:
            where_sql = "WHERE " + " AND ".join(filters)

        query = f"""
            SELECT
              strftime({ts_expr}, '%Y-%m-%d %H:%M:%S.%f') AS Timestamp,
              *
            FROM read_parquet('{file_path.as_posix()}')
            {where_sql}
            ORDER BY {ts_expr}
            LIMIT {limit}
        """

        res = con.execute(query)
        cols = [d[0] for d in res.description]
        rows = res.fetchall()

        return {"file": file, "columns": cols, "rows": rows}

    return app
