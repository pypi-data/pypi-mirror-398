"""
Tests für pandas Integration in questra-data.

Diese Tests prüfen:
1. ImportError wenn pandas nicht installiert ist (via QueryResult.to_df())
2. Korrekte DataFrame-Konvertierung wenn pandas installiert ist
3. QueryResult verhält sich like eine Liste
"""

from __future__ import annotations

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

# Versuche pandas to importieren
try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class TestPandasIntegration(unittest.TestCase):
    """Tests für pandas-Integration via QueryResult."""

    def setUp(self):
        """Setup für jeden Test."""
        # Mock für QuestraDataCore
        self.mock_auth = MagicMock()
        self.mock_auth.is_authenticated.return_value = True

    @unittest.skipUnless(PANDAS_AVAILABLE, "pandas not installed")
    def test_list_items_to_df_with_pandas(self):
        """Test list_items() + to_df() with installiertem pandas."""
        from seven2one.questra.data import QuestraData

        with patch(
            "seven2one.questra.data.highlevel_client.QuestraDataCore"
        ) as mock_core:
            # Setup Mock
            mock_client = mock_core.return_value
            mock_client.is_authenticated.return_value = True

            # Mock inventory.list Response
            mock_client.inventory.list.return_value = {
                "nodes": [
                    {
                        "_id": "1",
                        "_rowVersion": "1",
                        "Name": "Alice",
                        "Email": "alice@example.com",
                    },
                    {
                        "_id": "2",
                        "_rowVersion": "1",
                        "Name": "Bob",
                        "Email": "bob@example.com",
                    },
                ]
            }

            # Erstelle QuestraData Client
            client = QuestraData(
                graphql_url="https://example.com/graphql", auth_client=self.mock_auth
            )

            # Rufe list_items() auf and konvertiere to DataFrame
            result = client.list_items(
                inventory_name="TestUser",
                properties=["_id", "_rowVersion", "Name", "Email"],
            )
            df = result.to_df()

            # Assertions
            self.assertIsInstance(df, pd.DataFrame)
            self.assertEqual(len(df), 2)
            self.assertIn("Name", df.columns)
            self.assertIn("Email", df.columns)
            self.assertEqual(df.iloc[0]["Name"], "Alice")
            self.assertEqual(df.iloc[1]["Name"], "Bob")

    @unittest.skipUnless(PANDAS_AVAILABLE, "pandas not installed")
    def test_query_result_behaves_like_list(self):
        """Test dass QueryResult sich like eine Liste verhält."""
        from seven2one.questra.data import QuestraData

        with patch(
            "seven2one.questra.data.highlevel_client.QuestraDataCore"
        ) as mock_core:
            # Setup Mock
            mock_client = mock_core.return_value
            mock_client.is_authenticated.return_value = True

            # Mock inventory.list Response
            mock_client.inventory.list.return_value = {
                "nodes": [
                    {"_id": "1", "Name": "Alice"},
                    {"_id": "2", "Name": "Bob"},
                    {"_id": "3", "Name": "Charlie"},
                ]
            }

            client = QuestraData(
                graphql_url="https://example.com/graphql", auth_client=self.mock_auth
            )

            result = client.list_items(
                inventory_name="TestUser", properties=["_id", "Name"]
            )

            # Test len()
            self.assertEqual(len(result), 3)

            # Test Indexing
            self.assertEqual(result[0]["Name"], "Alice")
            self.assertEqual(result[1]["Name"], "Bob")

            # Test Slicing
            subset = result[0:2]
            self.assertEqual(len(subset), 2)

            # Test Iteration
            names = [item["Name"] for item in result]
            self.assertEqual(names, ["Alice", "Bob", "Charlie"])

    @unittest.skipUnless(PANDAS_AVAILABLE, "pandas not installed")
    def test_list_roles_to_df(self):
        """Test list_roles() + to_df() with Model-Objekten."""
        from uuid import UUID

        from seven2one.questra.data import QuestraData
        from seven2one.questra.data.models import Role

        with patch(
            "seven2one.questra.data.highlevel_client.QuestraDataCore"
        ) as mock_core:
            mock_client = mock_core.return_value
            mock_client.is_authenticated.return_value = True

            # Mock für CatalogManager
            with patch(
                "seven2one.questra.data.highlevel_client.CatalogManager"
            ) as mock_catalog:
                mock_catalog_instance = mock_catalog.return_value
                mock_catalog_instance.list_roles.return_value = [
                    Role(  # type: ignore[call-arg]
                        name="Admin",
                        description="Administrator",
                        isSystem=True,
                        createdBy=UUID("00000000-0000-0000-0000-000000000001"),
                        createdAt=datetime.now(),
                        alteredBy=UUID("00000000-0000-0000-0000-000000000001"),
                        alteredAt=datetime.now(),
                    ),
                    Role(  # type: ignore[call-arg]
                        name="User",
                        description="Normal User",
                        isSystem=False,
                        createdBy=UUID("5472b091-383b-4971-806f-de9c6ceb82d0"),
                        createdAt=datetime.now(),
                        alteredBy=UUID("5472b091-383b-4971-806f-de9c6ceb82d0"),
                        alteredAt=datetime.now(),
                    ),
                ]

                client = QuestraData(
                    graphql_url="https://example.com/graphql",
                    auth_client=self.mock_auth,
                )

                roles = client.list_roles()
                df = roles.to_df()

                # Assertions
                self.assertIsInstance(df, pd.DataFrame)
                self.assertEqual(len(df), 2)
                self.assertIn("name", df.columns)
                self.assertIn("description", df.columns)
                self.assertEqual(df.iloc[0]["name"], "Admin")
                self.assertEqual(df.iloc[1]["name"], "User")

    @unittest.skipIf(PANDAS_AVAILABLE, "Test requires pandas NOT to be installed")
    def test_to_df_without_pandas(self):
        """Test to_df() without pandas - sollte ImportError werfen."""
        from seven2one.questra.data import QuestraData

        with patch(
            "seven2one.questra.data.highlevel_client.QuestraDataCore"
        ) as mock_core:
            mock_client = mock_core.return_value
            mock_client.is_authenticated.return_value = True

            # Mock inventory.list Response
            mock_client.inventory.list.return_value = {
                "nodes": [{"_id": "1", "Name": "Alice"}]
            }

            client = QuestraData(
                graphql_url="https://example.com/graphql", auth_client=self.mock_auth
            )

            result = client.list_items(
                inventory_name="TestUser", properties=["_id", "Name"]
            )

            # Should raise ImportError
            with self.assertRaises(ImportError) as context:
                result.to_df()

            self.assertIn("pandas is not installed", str(context.exception))


if __name__ == "__main__":
    unittest.main()
