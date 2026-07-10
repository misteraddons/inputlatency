import os
import sys
import unittest
from pathlib import Path
from unittest import mock


sys.path.insert(0, str(Path(__file__).resolve().parent / "scripts"))

import update_prices  # noqa: E402


class UpdatePricesTests(unittest.TestCase):
    def test_row_product_url_ignores_boolean_amazon_cell(self):
        row = ["Example Pad", "YES", "https://www.amazon.com/dp/B012345678", ""]

        self.assertEqual(
            update_prices.row_product_url(row, amazon_col=1, link_col=2),
            "https://www.amazon.com/dp/B012345678",
        )

    def test_resolve_asin_expands_short_amazon_url(self):
        asin = update_prices.resolve_asin(
            "https://amzn.to/example",
            expand_url=lambda _url: "https://www.amazon.com/dp/B012345678?tag=test",
        )

        self.assertEqual(asin, "B012345678")

    def test_collect_row_asins_uses_each_rows_real_product_url(self):
        values = [
            ["Device", "Amazon", "Link", "Price"],
            ["Direct", "", "https://www.amazon.com/dp/B012345678", ""],
            ["Short", "YES", "https://amzn.to/example", ""],
        ]

        result = update_prices.collect_row_asins(
            values,
            amazon_col=1,
            link_col=2,
            resolve=lambda url: {
                "https://www.amazon.com/dp/B012345678": "B012345678",
                "https://amzn.to/example": "B087654321",
            }.get(url),
        )

        self.assertEqual(result, {2: "B012345678", 3: "B087654321"})

    def test_missing_paapi_credentials_fail_instead_of_succeeding_empty(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError):
                update_prices.fetch_prices_paapi(["B012345678"])


if __name__ == "__main__":
    unittest.main()
