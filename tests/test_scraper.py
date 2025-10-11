import asyncio
import csv
import importlib.util
import tempfile
from pathlib import Path
import unittest

from chinatax_scraper import CSV_HEADERS, Record, load_existing_keys, scrape


class RecordTests(unittest.TestCase):
    def test_csv_row_matches_order(self) -> None:
        record = Record("1", "Title", "DocNo", "2024-01-01")
        self.assertEqual(record.csv_row, ["1", "Title", "DocNo", "2024-01-01"])

    def test_unique_key_trims_whitespace(self) -> None:
        record = Record("1", " Title ", " DocNo ", "2024-01-01")
        self.assertEqual(record.unique_key, ("Title", "DocNo"))


class LoadExistingKeysTests(unittest.TestCase):
    def test_returns_empty_set_when_file_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "missing.csv"
            self.assertFalse(path.exists())
            self.assertEqual(load_existing_keys(path), set())

    def test_reads_keys_from_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "data.csv"
            with path.open("w", encoding="utf-8", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(CSV_HEADERS)
                writer.writerow(["1", "Title A", "Doc 1", "2024-01-01"])
                writer.writerow(["2", "Title B", "Doc 2", "2024-02-01"])
            expected = {("Title A", "Doc 1"), ("Title B", "Doc 2")}
            self.assertEqual(load_existing_keys(path), expected)

    def test_raises_when_columns_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "invalid.csv"
            with path.open("w", encoding="utf-8", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["序号", "标题", "成文日期"])  # missing 发文字号
                writer.writerow(["1", "Title", "2024-01-01"])
            with self.assertRaises(ValueError):
                load_existing_keys(path)


class ScrapeDependencyTests(unittest.TestCase):
    def test_requires_playwright_dependency(self) -> None:
        try:
            has_playwright = importlib.util.find_spec("playwright.async_api") is not None
        except ModuleNotFoundError:
            has_playwright = False

        if has_playwright:
            self.skipTest("Playwright is available in the environment")

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "out.csv"
            with self.assertRaisesRegex(RuntimeError, "Playwright 未安装"):
                asyncio.run(scrape(csv_path=csv_path))
            self.assertFalse(csv_path.exists())


if __name__ == "__main__":
    unittest.main()
