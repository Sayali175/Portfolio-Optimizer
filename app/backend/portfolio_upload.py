
import io
import math

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.backend.portfolio import Holding

router = APIRouter(
    prefix="/portfolio",
    tags=["Portfolio Management"],
)

REQUIRED_COLUMNS = {
    "name",
    "asset_class",
    "current_value",
}

MAX_FILE_SIZE = 5 * 1024 * 1024


@router.post("/upload")
async def upload_portfolio(file: UploadFile = File(...)):
    filename = (file.filename or "").lower()

    if not filename.endswith((".csv", ".xlsx")):
        raise HTTPException(
            status_code=400,
            detail="Only CSV and XLSX files are supported.",
        )

    contents = await file.read(MAX_FILE_SIZE + 1)

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File exceeds the 5 MB limit.",
        )

    try:
        buffer = io.BytesIO(contents)

        if filename.endswith(".csv"):
            df = pd.read_csv(buffer)
        else:
            df = pd.read_excel(buffer, engine="openpyxl")

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Could not read the uploaded file.",
        )

    df.columns = (
        df.columns.astype(str).str.strip().str.lower()
    )

    if df.columns.duplicated().any():
        raise HTTPException(
            status_code=422,
            detail="Duplicate column names are not allowed.",
        )

    missing = REQUIRED_COLUMNS - set(df.columns)

    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Missing columns: {sorted(missing)}",
        )

    if df.empty:
        raise HTTPException(
            status_code=422,
            detail="The uploaded file contains no holdings.",
        )

    holdings = []

    for index, row in df.iterrows():
        try:
            name = row["name"]
            category = row["asset_class"]
            value = row["current_value"]

            if pd.isna(name) or pd.isna(category):
                raise ValueError("Missing name or asset class")

            name = str(name).strip()
            category = str(category).strip().lower()

            value = float(value)

            if not math.isfinite(value):
                raise ValueError("Invalid investment value")

            holding = Holding(
                name=name,
                asset_class=category,
                current_value=value,
            )

            holdings.append(holding.model_dump())

        except (ValueError, TypeError) as exc:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid holding at row {index + 2}: {exc}",
            )

        except Exception as exc:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid holding at row {index + 2}: {exc}",
            )

    total = sum(
        holding["current_value"]
        for holding in holdings
    )

    return {
        "status": "uploaded",
        "filename": file.filename,
        "holdings_count": len(holdings),
        "portfolio_value": round(total, 2),
        "holdings": holdings,
    }
