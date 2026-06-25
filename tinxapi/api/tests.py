# -*- coding: utf-8 -*-
"""
Integration tests for the TIN-X API.

These tests run against the live stack (MySQL + Solr) as configured in
docker-compose-dev.yml.  Entity IDs are discovered dynamically from the list
endpoints so no fixture data is required; the tests validate response
*structure*, not specific data values.

Run with:
    docker compose -f docker-compose-dev.yml exec api python manage.py test api
"""

from __future__ import unicode_literals

from django.test import TestCase
from rest_framework.test import APIClient

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

ARTICLE_FIELDS = frozenset({"id", "title", "journal", "date", "authors", "abstract"})
PAGINATION_FIELDS = frozenset({"count", "next", "previous", "results"})


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


class _ArticlePairDiscoveryMixin:
    """
    Discovers a (doid, target_id) pair that exists in the live database.
    Mix into TestCase subclasses for the disease-target / target-disease
    article endpoints.
    """

    doid = None
    target_id = None

    @classmethod
    def _discover_pair(cls):
        """
        Walk the first few diseases until a pair with at least one target is
        found.  Stores the result in cls.doid / cls.target_id.
        """
        client = APIClient()
        disease_response = client.get("/diseases/?limit=10")
        if disease_response.status_code != 200:
            return
        for disease in disease_response.data.get("results", []):
            doid = disease["doid"]
            target_response = client.get(f"/diseases/{doid}/targets/?limit=1")
            if target_response.status_code != 200:
                continue
            results = target_response.data.get("results", [])
            if not results:
                continue
            cls.doid = doid
            cls.target_id = results[0]["target"]["id"]
            return

    def _skip_if_no_pair(self):
        if not self.doid or not self.target_id:
            self.skipTest(
                "Could not discover a disease-target pair from the live database"
            )


# ---------------------------------------------------------------------------
# GET /articles/
# ---------------------------------------------------------------------------


class ArticleListTests(TestCase):
    """Tests for the article list endpoint."""

    def setUp(self):
        self.client = APIClient()

    def test_returns_200(self):
        response = self.client.get("/articles/")
        self.assertEqual(response.status_code, 200)

    def test_has_pagination_envelope(self):
        response = self.client.get("/articles/")
        self.assertEqual(set(response.data.keys()), PAGINATION_FIELDS)

    def test_count_is_positive(self):
        response = self.client.get("/articles/")
        self.assertGreater(response.data["count"], 0)

    def test_results_have_correct_fields(self):
        response = self.client.get("/articles/?limit=1")
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(set(response.data["results"][0].keys()), ARTICLE_FIELDS)

    def test_limit_is_respected(self):
        response = self.client.get("/articles/?limit=3")
        self.assertLessEqual(len(response.data["results"]), 3)

    def test_offset_advances_page(self):
        r1 = self.client.get("/articles/?limit=1&offset=0")
        r2 = self.client.get("/articles/?limit=1&offset=1")
        self.assertNotEqual(
            r1.data["results"][0]["id"],
            r2.data["results"][0]["id"],
        )

    def test_next_link_present_when_more_results_exist(self):
        response = self.client.get("/articles/?limit=1")
        if response.data["count"] > 1:
            self.assertIsNotNone(response.data["next"])

    def test_previous_is_null_on_first_page(self):
        response = self.client.get("/articles/?limit=1&offset=0")
        self.assertIsNone(response.data["previous"])

    def test_previous_is_non_null_on_second_page(self):
        response = self.client.get("/articles/?limit=1&offset=1")
        self.assertIsNotNone(response.data["previous"])


# ---------------------------------------------------------------------------
# GET /articles/{id}/
# ---------------------------------------------------------------------------


class ArticleDetailTests(TestCase):
    """Tests for the article detail endpoint."""

    valid_article_id = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        client = APIClient()
        response = client.get("/articles/?limit=1")
        if response.status_code == 200 and response.data.get("results"):
            cls.valid_article_id = response.data["results"][0]["id"]

    def setUp(self):
        self.client = APIClient()

    def _skip_if_no_articles(self):
        if self.valid_article_id is None:
            self.skipTest("No articles found in the live database")

    def test_retrieve_returns_200(self):
        self._skip_if_no_articles()
        response = self.client.get(f"/articles/{self.valid_article_id}/")
        self.assertEqual(response.status_code, 200)

    def test_retrieve_has_correct_fields(self):
        self._skip_if_no_articles()
        response = self.client.get(f"/articles/{self.valid_article_id}/")
        self.assertEqual(set(response.data.keys()), ARTICLE_FIELDS)

    def test_retrieve_id_matches_requested_id(self):
        self._skip_if_no_articles()
        response = self.client.get(f"/articles/{self.valid_article_id}/")
        self.assertEqual(response.data["id"], self.valid_article_id)

    def test_id_zero_returns_404(self):
        response = self.client.get("/articles/0/")
        self.assertEqual(response.status_code, 404)

    def test_nonexistent_id_returns_404(self):
        response = self.client.get("/articles/999999999/")
        self.assertEqual(response.status_code, 404)


# ---------------------------------------------------------------------------
# GET /articles/?<filter>=<value>
# ---------------------------------------------------------------------------


class ArticleFilterTests(TestCase):
    """Tests for filter and DRF search query parameters on /articles/."""

    def setUp(self):
        self.client = APIClient()

    def _assert_valid_list_response(self, response):
        """Assert the response has the correct pagination shape and article fields."""
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data.keys()), PAGINATION_FIELDS)
        for article in response.data.get("results", []):
            self.assertEqual(set(article.keys()), ARTICLE_FIELDS)

    # --- each filter param returns a well-formed response ---

    def test_filter_by_title_returns_valid_response(self):
        self._assert_valid_list_response(self.client.get("/articles/?title=cancer"))

    def test_filter_by_journal_returns_valid_response(self):
        self._assert_valid_list_response(self.client.get("/articles/?journal=nature"))

    def test_filter_by_author_returns_valid_response(self):
        self._assert_valid_list_response(self.client.get("/articles/?author=smith"))

    def test_filter_by_abstract_returns_valid_response(self):
        self._assert_valid_list_response(self.client.get("/articles/?abstract=protein"))

    def test_search_param_returns_valid_response(self):
        self._assert_valid_list_response(self.client.get("/articles/?search=cancer"))

    # --- filter behaviour ---

    def test_nonsense_title_filter_returns_empty_list(self):
        response = self.client.get(
            "/articles/?title=ZZZZZ_THIS_TITLE_DOES_NOT_EXIST_ZZZZZ"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])

    def test_filter_narrows_total_count(self):
        """A filtered result set must be no larger than the full set."""
        unfiltered = self.client.get("/articles/")
        filtered = self.client.get("/articles/?title=cancer")
        self.assertEqual(unfiltered.status_code, 200)
        self.assertEqual(filtered.status_code, 200)
        self.assertLessEqual(filtered.data["count"], unfiltered.data["count"])


# ---------------------------------------------------------------------------
# GET /diseases/{doid}/targets/{target_id}/articles
# ---------------------------------------------------------------------------


class DiseaseTargetArticleTests(_ArticlePairDiscoveryMixin, TestCase):
    """Tests for the disease→target articles endpoint."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._discover_pair()

    def setUp(self):
        self.client = APIClient()

    def test_returns_200(self):
        self._skip_if_no_pair()
        response = self.client.get(
            f"/diseases/{self.doid}/targets/{self.target_id}/articles"
        )
        self.assertEqual(response.status_code, 200)

    def test_has_pagination_envelope(self):
        self._skip_if_no_pair()
        response = self.client.get(
            f"/diseases/{self.doid}/targets/{self.target_id}/articles"
        )
        self.assertEqual(set(response.data.keys()), PAGINATION_FIELDS)

    def test_results_have_correct_fields(self):
        self._skip_if_no_pair()
        response = self.client.get(
            f"/diseases/{self.doid}/targets/{self.target_id}/articles?limit=1"
        )
        for article in response.data.get("results", []):
            self.assertEqual(set(article.keys()), ARTICLE_FIELDS)

    def test_nonexistent_pair_returns_200_with_empty_results(self):
        response = self.client.get("/diseases/DOID:FAKE99999/targets/99999/articles")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)


# ---------------------------------------------------------------------------
# GET /targets/{target_id}/diseases/{doid}/articles
# ---------------------------------------------------------------------------


class TargetDiseaseArticleTests(_ArticlePairDiscoveryMixin, TestCase):
    """Tests for the target→disease articles endpoint."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._discover_pair()

    def setUp(self):
        self.client = APIClient()

    def test_returns_200(self):
        self._skip_if_no_pair()
        response = self.client.get(
            f"/targets/{self.target_id}/diseases/{self.doid}/articles"
        )
        self.assertEqual(response.status_code, 200)

    def test_has_pagination_envelope(self):
        self._skip_if_no_pair()
        response = self.client.get(
            f"/targets/{self.target_id}/diseases/{self.doid}/articles"
        )
        self.assertEqual(set(response.data.keys()), PAGINATION_FIELDS)

    def test_results_have_correct_fields(self):
        self._skip_if_no_pair()
        response = self.client.get(
            f"/targets/{self.target_id}/diseases/{self.doid}/articles?limit=1"
        )
        for article in response.data.get("results", []):
            self.assertEqual(set(article.keys()), ARTICLE_FIELDS)

    def test_matches_disease_target_url_results(self):
        """Both URL orderings for the same pair must return the same article IDs."""
        self._skip_if_no_pair()
        r1 = self.client.get(
            f"/diseases/{self.doid}/targets/{self.target_id}/articles?limit=5"
        )
        r2 = self.client.get(
            f"/targets/{self.target_id}/diseases/{self.doid}/articles?limit=5"
        )
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r2.status_code, 200)
        ids1 = {a["id"] for a in r1.data["results"]}
        ids2 = {a["id"] for a in r2.data["results"]}
        self.assertEqual(ids1, ids2)

    def test_nonexistent_pair_returns_200_with_empty_results(self):
        response = self.client.get("/targets/99999/diseases/DOID:FAKE99999/articles")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)
