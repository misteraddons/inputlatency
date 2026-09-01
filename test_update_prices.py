import os
import sys
import unittest
from pathlib import Path
from unittest import mock


sys.path.insert(0, str(Path(__file__).resolve().parent / "scripts"))

import update_prices  # noqa: E402


class UpdatePricesTests(unittest.TestCase):
    def test_find_header_column_is_case_insensitive(self):
        self.assertEqual(
            update_prices.find_header_column(["Device", " PRICE "], "Price"),
            1,
        )

    def test_ensure_price_column_adds_managed_column(self):
        worksheet = mock.Mock(col_count=4)

        price_col = update_prices.ensure_price_column(
            worksheet,
            ["Device", "Amazon", "Link", "Mode"],
            dry_run=False,
        )

        self.assertEqual(price_col, 4)
        worksheet.add_cols.assert_called_once_with(1)
        worksheet.update_cell.assert_called_once_with(1, 5, "Price")

    def test_ensure_price_column_dry_run_does_not_modify_sheet(self):
        worksheet = mock.Mock(col_count=4)

        price_col = update_prices.ensure_price_column(
            worksheet,
            ["Device", "Amazon", "Link", "Mode"],
            dry_run=True,
        )

        self.assertEqual(price_col, 4)
        worksheet.add_cols.assert_not_called()
        worksheet.update_cell.assert_not_called()

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

    def test_creators_token_endpoint_uses_credential_region(self):
        self.assertEqual(
            update_prices.creators_token_endpoint("3.1"),
            "https://api.amazon.com/auth/o2/token",
        )
        self.assertEqual(
            update_prices.creators_token_endpoint("v3.2"),
            "https://api.amazon.co.uk/auth/o2/token",
        )
        with self.assertRaisesRegex(RuntimeError, "Unsupported Creators API credential version"):
            update_prices.creators_token_endpoint("2.0")

    def test_creators_access_token_uses_oauth_client_credentials(self):
        calls = []

        def request_json(url, payload, headers=None):
            calls.append((url, payload, headers))
            return {"access_token": "test-token", "expires_in": 3600}

        token = update_prices.fetch_creators_access_token(
            "credential-id",
            "credential-secret",
            "3.1",
            request_json=request_json,
        )

        self.assertEqual(token, "test-token")
        self.assertEqual(calls[0][0], "https://api.amazon.com/auth/o2/token")
        self.assertEqual(
            calls[0][1],
            {
                "grant_type": "client_credentials",
                "client_id": "credential-id",
                "client_secret": "credential-secret",
                "scope": "creatorsapi::default",
            },
        )
        self.assertIsNone(calls[0][2])

    def test_extract_creators_prices_prefers_buy_box_listing(self):
        response = {
            "itemsResult": {
                "items": [
                    {
                        "asin": "b012345678",
                        "offersV2": {
                            "listings": [
                                {"price": {"money": {"amount": 29.99}}},
                                {
                                    "isBuyBoxWinner": True,
                                    "price": {"money": {"amount": 24.5}},
                                },
                            ]
                        },
                    },
                    {"asin": "B087654321", "offersV2": None},
                ]
            }
        }

        self.assertEqual(
            update_prices.extract_creators_prices(response),
            {"B012345678": 24.5},
        )

    def test_fetch_prices_creators_batches_requests_and_reuses_token(self):
        token_calls = []
        api_calls = []
        sleeps = []

        def token_fetcher(credential_id, credential_secret, credential_version):
            token_calls.append((credential_id, credential_secret, credential_version))
            return "test-token"

        def request_json(url, payload, headers=None):
            api_calls.append((url, payload, headers))
            return {
                "itemsResult": {
                    "items": [
                        {
                            "asin": payload["itemIds"][0],
                            "offersV2": {
                                "listings": [
                                    {"price": {"money": {"amount": 19.99}}}
                                ]
                            },
                        }
                    ]
                }
            }

        environment = {
            "AMAZON_CREATORS_CREDENTIAL_ID": "credential-id",
            "AMAZON_CREATORS_CREDENTIAL_SECRET": "credential-secret",
            "AMAZON_CREATORS_CREDENTIAL_VERSION": "3.1",
            "AMAZON_PARTNER_TAG": "example-20",
        }
        with mock.patch.dict(os.environ, environment, clear=True):
            prices = update_prices.fetch_prices_creators(
                [f"B{i:09d}" for i in range(11)],
                token_fetcher=token_fetcher,
                request_json=request_json,
                sleep=sleeps.append,
            )

        self.assertEqual(token_calls, [("credential-id", "credential-secret", "3.1")])
        self.assertEqual(len(api_calls), 2)
        self.assertEqual(len(api_calls[0][1]["itemIds"]), 10)
        self.assertEqual(api_calls[0][1]["resources"], list(update_prices.CREATORS_PRICE_RESOURCES))
        self.assertEqual(api_calls[0][2]["Authorization"], "Bearer test-token")
        self.assertEqual(api_calls[0][2]["x-marketplace"], "www.amazon.com")
        self.assertEqual(sleeps, [1])
        self.assertEqual(prices["B000000000"], 19.99)
        self.assertEqual(prices["B000000010"], 19.99)

    def test_missing_creators_credentials_fail_instead_of_succeeding_empty(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "AMAZON_CREATORS_CREDENTIAL_ID"):
                update_prices.fetch_prices_creators(["B012345678"])

    def test_column_name_uses_a1_notation(self):
        self.assertEqual(update_prices.column_name(1), "A")
        self.assertEqual(update_prices.column_name(26), "Z")
        self.assertEqual(update_prices.column_name(27), "AA")
        self.assertEqual(update_prices.column_name(58), "BF")

    def test_price_updates_are_batched_into_one_sheets_request(self):
        worksheet = mock.Mock()
        updated, protected = update_prices.apply_price_updates(
            worksheet,
            [(2, 58, "$11.00"), (3, 58, "$21.00")],
        )

        self.assertEqual((updated, protected), (2, 0))
        worksheet.batch_update.assert_called_once_with(
            [
                {"range": "BF2", "values": [["$11.00"]]},
                {"range": "BF3", "values": [["$21.00"]]},
            ],
            value_input_option="RAW",
        )

    def test_protected_price_column_is_reported_without_aborting(self):
        worksheet = mock.Mock()
        worksheet.batch_update.side_effect = Exception(
            "APIError: [400]: You are trying to edit a protected cell or object"
        )

        with (
            self.assertLogs(update_prices.log, level="WARNING") as captured,
        ):
            updated, protected = update_prices.apply_price_updates(
                worksheet,
                [(2, 58, "$11.00"), (3, 58, "$21.00")],
            )

        self.assertEqual((updated, protected), (0, 2))
        self.assertIn("Price column is protected", "\n".join(captured.output))

    def test_unexpected_sheet_write_errors_still_fail(self):
        worksheet = mock.Mock()
        worksheet.batch_update.side_effect = Exception("APIError: [503]: backend unavailable")

        with self.assertRaisesRegex(Exception, "backend unavailable"):
            update_prices.apply_price_updates(worksheet, [(2, 58, "$11.00")])


if __name__ == "__main__":
    unittest.main()
