from fastapi import APIRouter, HTTPException
import tomli
from pathlib import Path

router = APIRouter()


@router.get("/version")
async def get_version():
    """
    Get the application version from pyproject.toml file

    Returns:
        dict: Contains version information
    """
    try:
        # 嘗試讀取 pyproject.toml 文件
        pyproject_path = Path(__file__).parents[2] / "pyproject.toml"

        with open(pyproject_path, "rb") as f:
            pyproject_data = tomli.load(f)
        print("get version<============")
        print(pyproject_data)
        # 從 pyproject.toml 中獲取版本號
        # poetry_data = pyproject_data.get("tool", {}).get("poetry", {})
        version = pyproject_data.get("project", {}).get("version", "未知")
        name = pyproject_data.get("project", {}).get("name", "未知")

        return {"name": name, "version": version}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"無法獲取版本信息: {str(e)}")
