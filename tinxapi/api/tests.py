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

DISEASE_FIELDS = frozenset(
    {
        "doid",
        "name",
        "category",
        "summary",
        "num_important_targets",
        "novelty",
        "targets",
        "children",
        "parent",
    }
)

TARGET_FIELDS = frozenset(
    {
        "id",
        "name",
        "uniprot",
        "sym",
        "fam",
        "famext",
        "tdl",
        "dtoid",
        "num_important_diseases",
        "novelty",
        "diseases",
    }
)

DISEASE_TARGET_FIELDS = frozenset({"target", "articles", "nds_rank", "importance"})
TARGET_DISEASE_FIELDS = frozenset({"disease", "articles", "importance", "category"})

# Fields of the nested "target" dict inside /diseases/{doid}/targets/ results
# (a different, flatter shape than TARGET_FIELDS above).
NESTED_TARGET_FIELDS = frozenset(
    {"id", "name", "uniprot", "fam", "famext", "tdl", "novelty", "sym", "dtoid"}
)

DISEASE_CHILD_FIELDS = frozenset({"doid", "parent_id", "name"})


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


class _ArticlePairDiscoveryMixin:
    """
    Discovers a (doid, target_id) pair that exists in the live database.
    Mix into TestCase subclasses for the disease-target / target-disease
    endpoints (association endpoints as well as their nested article
    endpoints).
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


# ---------------------------------------------------------------------------
# GET /diseases/
# ---------------------------------------------------------------------------


class DiseaseListTests(TestCase):
    """Tests for the disease list endpoint."""

    def setUp(self):
        self.client = APIClient()

    def test_returns_200(self):
        response = self.client.get("/diseases/")
        self.assertEqual(response.status_code, 200)

    def test_has_pagination_envelope(self):
        response = self.client.get("/diseases/")
        self.assertEqual(set(response.data.keys()), PAGINATION_FIELDS)

    def test_count_is_positive(self):
        response = self.client.get("/diseases/")
        self.assertGreater(response.data["count"], 0)

    def test_results_have_correct_fields(self):
        response = self.client.get("/diseases/?limit=1")
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(set(response.data["results"][0].keys()), DISEASE_FIELDS)

    def test_limit_is_respected(self):
        response = self.client.get("/diseases/?limit=3")
        self.assertLessEqual(len(response.data["results"]), 3)

    def test_offset_advances_page(self):
        r1 = self.client.get("/diseases/?limit=1&offset=0")
        r2 = self.client.get("/diseases/?limit=1&offset=1")
        self.assertNotEqual(
            r1.data["results"][0]["doid"],
            r2.data["results"][0]["doid"],
        )

    def test_next_link_present_when_more_results_exist(self):
        response = self.client.get("/diseases/?limit=1")
        if response.data["count"] > 1:
            self.assertIsNotNone(response.data["next"])

    def test_previous_is_null_on_first_page(self):
        response = self.client.get("/diseases/?limit=1&offset=0")
        self.assertIsNone(response.data["previous"])

    def test_previous_is_non_null_on_second_page(self):
        response = self.client.get("/diseases/?limit=1&offset=1")
        self.assertIsNotNone(response.data["previous"])


# ---------------------------------------------------------------------------
# GET /diseases/{doid}/
# ---------------------------------------------------------------------------


class DiseaseDetailTests(TestCase):
    """Tests for the disease detail endpoint."""

    valid_doid = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        client = APIClient()
        response = client.get("/diseases/?limit=1")
        if response.status_code == 200 and response.data.get("results"):
            cls.valid_doid = response.data["results"][0]["doid"]

    def setUp(self):
        self.client = APIClient()

    def _skip_if_no_diseases(self):
        if self.valid_doid is None:
            self.skipTest("No diseases found in the live database")

    def test_retrieve_returns_200(self):
        self._skip_if_no_diseases()
        response = self.client.get(f"/diseases/{self.valid_doid}/")
        self.assertEqual(response.status_code, 200)

    def test_retrieve_has_correct_fields(self):
        self._skip_if_no_diseases()
        response = self.client.get(f"/diseases/{self.valid_doid}/")
        self.assertEqual(set(response.data.keys()), DISEASE_FIELDS)

    def test_retrieve_doid_matches_requested_doid(self):
        self._skip_if_no_diseases()
        response = self.client.get(f"/diseases/{self.valid_doid}/")
        self.assertEqual(response.data["doid"], self.valid_doid)

    def test_nonexistent_doid_returns_404(self):
        response = self.client.get("/diseases/DOID:FAKE99999/")
        self.assertEqual(response.status_code, 404)


# ---------------------------------------------------------------------------
# GET /diseases/{doid}/children/ and /diseases/{doid}/parent/
# ---------------------------------------------------------------------------


class DiseaseChildrenAndParentTests(TestCase):
    """Tests for the disease children/parent sub-resource endpoints."""

    valid_doid = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        client = APIClient()
        response = client.get("/diseases/?limit=1")
        if response.status_code == 200 and response.data.get("results"):
            cls.valid_doid = response.data["results"][0]["doid"]

    def setUp(self):
        self.client = APIClient()

    def _skip_if_no_diseases(self):
        if self.valid_doid is None:
            self.skipTest("No diseases found in the live database")

    def test_children_returns_200_with_list(self):
        self._skip_if_no_diseases()
        response = self.client.get(f"/diseases/{self.valid_doid}/children/")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)

    def test_children_results_have_correct_fields(self):
        self._skip_if_no_diseases()
        response = self.client.get(f"/diseases/{self.valid_doid}/children/")
        for child in response.data:
            self.assertEqual(set(child.keys()), DISEASE_CHILD_FIELDS)

    def test_parent_returns_200(self):
        self._skip_if_no_diseases()
        response = self.client.get(f"/diseases/{self.valid_doid}/parent/")
        self.assertEqual(response.status_code, 200)

    def test_parent_has_correct_fields_when_present(self):
        self._skip_if_no_diseases()
        response = self.client.get(f"/diseases/{self.valid_doid}/parent/")
        if response.data:
            self.assertEqual(set(response.data.keys()), DISEASE_CHILD_FIELDS)

    def test_nonexistent_doid_children_returns_404(self):
        response = self.client.get("/diseases/DOID:FAKE99999/children/")
        self.assertEqual(response.status_code, 404)

    def test_nonexistent_doid_parent_returns_404(self):
        response = self.client.get("/diseases/DOID:FAKE99999/parent/")
        self.assertEqual(response.status_code, 404)


# ---------------------------------------------------------------------------
# GET /diseases/?<filter>=<value>
# ---------------------------------------------------------------------------


class DiseaseFilterTests(TestCase):
    """Tests for filter and DRF search query parameters on /diseases/."""

    sample_doid = None
    sample_name = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        client = APIClient()
        response = client.get("/diseases/?limit=1")
        if response.status_code == 200 and response.data.get("results"):
            disease = response.data["results"][0]
            cls.sample_doid = disease["doid"]
            cls.sample_name = disease["name"]

    def setUp(self):
        self.client = APIClient()

    def _skip_if_no_sample(self):
        if self.sample_doid is None or self.sample_name is None:
            self.skipTest("No diseases found in the live database")

    def _assert_valid_list_response(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data.keys()), PAGINATION_FIELDS)
        for disease in response.data.get("results", []):
            self.assertEqual(set(disease.keys()), DISEASE_FIELDS)

    def test_filter_by_doid_returns_valid_response(self):
        self._skip_if_no_sample()
        response = self.client.get("/diseases/", {"doid": self.sample_doid})
        self._assert_valid_list_response(response)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["doid"], self.sample_doid)

    def test_search_param_returns_valid_response(self):
        self._skip_if_no_sample()
        # DRF's SearchFilter splits the search value on whitespace (after
        # replacing commas with spaces) and requires every resulting term to
        # match, so a multi-word search value can never satisfy a single
        # "^name" (startswith) field. Use just the name's first token.
        first_word = self.sample_name.replace(",", " ").split()[0]
        response = self.client.get("/diseases/", {"search": first_word, "limit": 100})
        self._assert_valid_list_response(response)
        doids = {d["doid"] for d in response.data["results"]}
        self.assertIn(self.sample_doid, doids)

    def test_nonsense_doid_filter_returns_empty_list(self):
        response = self.client.get(
            "/diseases/", {"doid": "DOID:ZZZZ_DOES_NOT_EXIST_ZZZZ"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])

    def test_filter_narrows_total_count(self):
        self._skip_if_no_sample()
        unfiltered = self.client.get("/diseases/")
        filtered = self.client.get("/diseases/", {"doid": self.sample_doid})
        self.assertEqual(unfiltered.status_code, 200)
        self.assertEqual(filtered.status_code, 200)
        self.assertLessEqual(filtered.data["count"], unfiltered.data["count"])


# ---------------------------------------------------------------------------
# GET /targets/
# ---------------------------------------------------------------------------


class TargetListTests(TestCase):
    """Tests for the target list endpoint."""

    def setUp(self):
        self.client = APIClient()

    def test_returns_200(self):
        response = self.client.get("/targets/")
        self.assertEqual(response.status_code, 200)

    def test_has_pagination_envelope(self):
        response = self.client.get("/targets/")
        self.assertEqual(set(response.data.keys()), PAGINATION_FIELDS)

    def test_count_is_positive(self):
        response = self.client.get("/targets/")
        self.assertGreater(response.data["count"], 0)

    def test_results_have_correct_fields(self):
        response = self.client.get("/targets/?limit=1")
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(set(response.data["results"][0].keys()), TARGET_FIELDS)

    def test_limit_is_respected(self):
        response = self.client.get("/targets/?limit=3")
        self.assertLessEqual(len(response.data["results"]), 3)

    def test_offset_advances_page(self):
        r1 = self.client.get("/targets/?limit=1&offset=0")
        r2 = self.client.get("/targets/?limit=1&offset=1")
        self.assertNotEqual(
            r1.data["results"][0]["id"],
            r2.data["results"][0]["id"],
        )

    def test_next_link_present_when_more_results_exist(self):
        response = self.client.get("/targets/?limit=1")
        if response.data["count"] > 1:
            self.assertIsNotNone(response.data["next"])

    def test_previous_is_null_on_first_page(self):
        response = self.client.get("/targets/?limit=1&offset=0")
        self.assertIsNone(response.data["previous"])

    def test_previous_is_non_null_on_second_page(self):
        response = self.client.get("/targets/?limit=1&offset=1")
        self.assertIsNotNone(response.data["previous"])


# ---------------------------------------------------------------------------
# GET /targets/{target_id}/
# ---------------------------------------------------------------------------


class TargetDetailTests(TestCase):
    """Tests for the target detail endpoint."""

    valid_target_id = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        client = APIClient()
        response = client.get("/targets/?limit=1")
        if response.status_code == 200 and response.data.get("results"):
            cls.valid_target_id = response.data["results"][0]["id"]

    def setUp(self):
        self.client = APIClient()

    def _skip_if_no_targets(self):
        if self.valid_target_id is None:
            self.skipTest("No targets found in the live database")

    def test_retrieve_returns_200(self):
        self._skip_if_no_targets()
        response = self.client.get(f"/targets/{self.valid_target_id}/")
        self.assertEqual(response.status_code, 200)

    def test_retrieve_has_correct_fields(self):
        self._skip_if_no_targets()
        response = self.client.get(f"/targets/{self.valid_target_id}/")
        self.assertEqual(set(response.data.keys()), TARGET_FIELDS)

    def test_retrieve_id_matches_requested_id(self):
        self._skip_if_no_targets()
        response = self.client.get(f"/targets/{self.valid_target_id}/")
        self.assertEqual(response.data["id"], self.valid_target_id)

    def test_id_zero_returns_404(self):
        response = self.client.get("/targets/0/")
        self.assertEqual(response.status_code, 404)

    def test_nonexistent_id_returns_404(self):
        response = self.client.get("/targets/999999999/")
        self.assertEqual(response.status_code, 404)


# ---------------------------------------------------------------------------
# GET /targets/?<filter>=<value>
# ---------------------------------------------------------------------------


class TargetFilterTests(TestCase):
    """Tests for filter and DRF search query parameters on /targets/."""

    targets_sample = []

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        client = APIClient()
        response = client.get("/targets/?limit=50")
        if response.status_code == 200:
            cls.targets_sample = response.data.get("results", [])

    def setUp(self):
        self.client = APIClient()

    def _first_target_with(self, field):
        for target in self.targets_sample:
            if target.get(field):
                return target
        return None

    def _skip_if_none(self, target, field):
        if target is None:
            self.skipTest(f"No target with a non-empty '{field}' found in sample")

    def _assert_valid_list_response(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data.keys()), PAGINATION_FIELDS)
        for target in response.data.get("results", []):
            self.assertEqual(set(target.keys()), TARGET_FIELDS)

    def test_filter_by_name_returns_valid_response(self):
        target = self._first_target_with("name")
        self._skip_if_none(target, "name")
        response = self.client.get("/targets/", {"name": target["name"]})
        self._assert_valid_list_response(response)
        ids = {t["id"] for t in response.data["results"]}
        self.assertIn(target["id"], ids)

    def test_filter_by_uniprot_returns_valid_response(self):
        target = self._first_target_with("uniprot")
        self._skip_if_none(target, "uniprot")
        response = self.client.get("/targets/", {"uniprot": target["uniprot"]})
        self._assert_valid_list_response(response)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], target["id"])

    def test_filter_by_sym_returns_valid_response(self):
        target = self._first_target_with("sym")
        self._skip_if_none(target, "sym")
        response = self.client.get("/targets/", {"sym": target["sym"]})
        self._assert_valid_list_response(response)
        ids = {t["id"] for t in response.data["results"]}
        self.assertIn(target["id"], ids)

    def test_filter_by_fam_returns_valid_response(self):
        target = self._first_target_with("fam")
        self._skip_if_none(target, "fam")
        response = self.client.get("/targets/", {"fam": target["fam"]})
        self._assert_valid_list_response(response)
        ids = {t["id"] for t in response.data["results"]}
        self.assertIn(target["id"], ids)

    def test_filter_by_famext_returns_valid_response(self):
        target = self._first_target_with("famext")
        self._skip_if_none(target, "famext")
        response = self.client.get("/targets/", {"famext": target["famext"]})
        self._assert_valid_list_response(response)
        ids = {t["id"] for t in response.data["results"]}
        self.assertIn(target["id"], ids)

    def test_filter_by_tdl_returns_valid_response(self):
        target = self._first_target_with("tdl")
        self._skip_if_none(target, "tdl")
        response = self.client.get("/targets/", {"tdl": target["tdl"]})
        self._assert_valid_list_response(response)
        ids = {t["id"] for t in response.data["results"]}
        self.assertIn(target["id"], ids)

    def test_search_param_returns_valid_response(self):
        target = self._first_target_with("sym")
        self._skip_if_none(target, "sym")
        response = self.client.get("/targets/", {"search": target["sym"]})
        self._assert_valid_list_response(response)
        ids = {t["id"] for t in response.data["results"]}
        self.assertIn(target["id"], ids)

    def test_in_dto_true_and_false_partition_all_targets(self):
        """
        NOTE: this django-filter version's BooleanFilter only recognizes the
        capitalized "True"/"False" strings; lowercase "true"/"false" (and
        "1"/"0") are silently ignored and the filter has no effect.
        """
        total = self.client.get("/targets/")
        with_dto = self.client.get("/targets/", {"in_dto": "True"})
        without_dto = self.client.get("/targets/", {"in_dto": "False"})
        self.assertEqual(total.status_code, 200)
        self.assertEqual(with_dto.status_code, 200)
        self.assertEqual(without_dto.status_code, 200)
        self.assertEqual(
            with_dto.data["count"] + without_dto.data["count"], total.data["count"]
        )
        for target in with_dto.data["results"]:
            self.assertIsNotNone(target["dtoid"])
        for target in without_dto.data["results"]:
            self.assertIsNone(target["dtoid"])

    def test_nonsense_name_filter_returns_empty_list(self):
        response = self.client.get(
            "/targets/", {"name": "ZZZZZ_THIS_NAME_DOES_NOT_EXIST_ZZZZZ"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])

    def test_filter_narrows_total_count(self):
        target = self._first_target_with("sym")
        self._skip_if_none(target, "sym")
        unfiltered = self.client.get("/targets/")
        filtered = self.client.get("/targets/", {"sym": target["sym"]})
        self.assertEqual(unfiltered.status_code, 200)
        self.assertEqual(filtered.status_code, 200)
        self.assertLessEqual(filtered.data["count"], unfiltered.data["count"])


# ---------------------------------------------------------------------------
# GET /diseases/{doid}/targets/ and /diseases/{doid}/targets/{target_id}
# ---------------------------------------------------------------------------


class DiseaseTargetsTests(_ArticlePairDiscoveryMixin, TestCase):
    """Tests for the disease→targets association endpoint."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._discover_pair()

    def setUp(self):
        self.client = APIClient()

    def test_list_returns_200(self):
        self._skip_if_no_pair()
        response = self.client.get(f"/diseases/{self.doid}/targets/")
        self.assertEqual(response.status_code, 200)

    def test_list_has_pagination_envelope(self):
        self._skip_if_no_pair()
        response = self.client.get(f"/diseases/{self.doid}/targets/")
        self.assertEqual(set(response.data.keys()), PAGINATION_FIELDS)

    def test_list_results_have_correct_fields(self):
        self._skip_if_no_pair()
        response = self.client.get(f"/diseases/{self.doid}/targets/?limit=1")
        for entry in response.data.get("results", []):
            self.assertEqual(set(entry.keys()), DISEASE_TARGET_FIELDS)
            self.assertEqual(set(entry["target"].keys()), NESTED_TARGET_FIELDS)

    def test_retrieve_returns_200(self):
        self._skip_if_no_pair()
        response = self.client.get(f"/diseases/{self.doid}/targets/{self.target_id}")
        self.assertEqual(response.status_code, 200)

    def test_retrieve_has_correct_fields(self):
        self._skip_if_no_pair()
        response = self.client.get(f"/diseases/{self.doid}/targets/{self.target_id}")
        self.assertEqual(set(response.data.keys()), DISEASE_TARGET_FIELDS)

    def test_retrieve_nonexistent_target_id_returns_404(self):
        self._skip_if_no_pair()
        response = self.client.get(f"/diseases/{self.doid}/targets/999999999")
        self.assertEqual(response.status_code, 404)

    def test_list_nonexistent_doid_returns_200_with_empty_results(self):
        response = self.client.get("/diseases/DOID:FAKE99999/targets/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

    def test_filter_by_sym_returns_valid_response(self):
        self._skip_if_no_pair()
        target_response = self.client.get(
            f"/diseases/{self.doid}/targets/{self.target_id}"
        )
        sym = target_response.data["target"]["sym"]
        if not sym:
            self.skipTest("Discovered target has no 'sym' to filter on")
        response = self.client.get(f"/diseases/{self.doid}/targets/", {"sym": sym})
        self.assertEqual(response.status_code, 200)
        ids = {entry["target"]["id"] for entry in response.data["results"]}
        self.assertIn(self.target_id, ids)


# ---------------------------------------------------------------------------
# GET /targets/{target_id}/diseases/ and /targets/{target_id}/diseases/{doid}
# ---------------------------------------------------------------------------


class TargetDiseasesTests(_ArticlePairDiscoveryMixin, TestCase):
    """Tests for the target→diseases association endpoint."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._discover_pair()

    def setUp(self):
        self.client = APIClient()

    def test_list_returns_200(self):
        self._skip_if_no_pair()
        response = self.client.get(f"/targets/{self.target_id}/diseases/")
        self.assertEqual(response.status_code, 200)

    def test_list_has_pagination_envelope(self):
        self._skip_if_no_pair()
        response = self.client.get(f"/targets/{self.target_id}/diseases/")
        self.assertEqual(set(response.data.keys()), PAGINATION_FIELDS)

    def test_list_results_have_correct_fields(self):
        self._skip_if_no_pair()
        response = self.client.get(f"/targets/{self.target_id}/diseases/?limit=1")
        for entry in response.data.get("results", []):
            self.assertEqual(set(entry.keys()), TARGET_DISEASE_FIELDS)
            self.assertEqual(set(entry["disease"].keys()), DISEASE_FIELDS)

    def test_retrieve_returns_200(self):
        self._skip_if_no_pair()
        response = self.client.get(f"/targets/{self.target_id}/diseases/{self.doid}/")
        self.assertEqual(response.status_code, 200)

    def test_retrieve_has_correct_fields(self):
        self._skip_if_no_pair()
        response = self.client.get(f"/targets/{self.target_id}/diseases/{self.doid}/")
        self.assertEqual(set(response.data.keys()), TARGET_DISEASE_FIELDS)

    def test_retrieve_nonexistent_doid_returns_404(self):
        self._skip_if_no_pair()
        response = self.client.get(
            f"/targets/{self.target_id}/diseases/DOID:FAKE99999/"
        )
        self.assertEqual(response.status_code, 404)

    def test_list_nonexistent_target_id_returns_200_with_empty_results(self):
        response = self.client.get("/targets/999999999/diseases/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)


# ---------------------------------------------------------------------------
# GET /search/
# ---------------------------------------------------------------------------


class SearchTests(TestCase):
    """
    Tests for the /search/ endpoint. This queries the live Solr instance
    directly (via haystack), rather than the MySQL-backed views used
    elsewhere in this file.
    """

    def setUp(self):
        self.client = APIClient()

    def test_target_search_returns_200_with_list(self):
        response = self.client.get("/search/", {"q": "kinase"})
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertGreater(len(response.data), 0)

    def test_target_search_results_only_include_entries_with_dtoid(self):
        response = self.client.get("/search/", {"q": "kinase"})
        for entry in response.data:
            self.assertTrue(entry["dtoid"])

    def test_disease_search_returns_200_with_list(self):
        response = self.client.get("/search/", {"q": "cancer", "type": "disease"})
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertGreater(len(response.data), 0)

    def test_disease_search_results_have_expected_fields(self):
        response = self.client.get("/search/", {"q": "cancer", "type": "disease"})
        for entry in response.data:
            self.assertEqual(
                set(entry.keys()), {"text", "doid", "doid_exact", "name", "summary"}
            )

    def test_nonsense_query_returns_empty_list(self):
        response = self.client.get(
            "/search/", {"q": "ZZZZNONSENSEQUERY_DOES_NOT_EXIST_12345"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])
