from pathlib import Path
import openpyxl


def read_excel(file_path: str) -> list[dict]:
    """
    Đọc file Excel, trả về list dict — mỗi dict là 1 hàng.
    Hàng đầu = tên cột (header), các hàng tiếp theo = data.
    Bỏ qua hàng trống hoàn toàn.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy file Excel: {file_path}")

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    if not rows:
        raise ValueError("File Excel trống")

    # Hàng đầu là headers — normalize: lowercase, strip, thay space bằng _
    headers = [_normalize(str(h)) if h is not None else f"col_{i}" for i, h in enumerate(rows[0])]

    result = []
    for row in rows[1:]:
        # Bỏ qua hàng trống hoàn toàn
        if all(cell is None or str(cell).strip() == "" for cell in row):
            continue
        entry = {headers[i]: (str(v).strip() if v is not None else "") for i, v in enumerate(row)}
        result.append(entry)

    return result


def _normalize(s: str) -> str:
    return s.strip().lower().replace(" ", "_").replace("-", "_")
