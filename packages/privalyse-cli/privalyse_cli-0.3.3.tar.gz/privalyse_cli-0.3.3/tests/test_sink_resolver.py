import unittest
from privalyse_scanner.core.sink_resolver import SinkResolver, SinkInfo

class TestSinkResolver(unittest.TestCase):
    def setUp(self):
        self.resolver = SinkResolver()

    def test_exact_match_openai(self):
        info = self.resolver.resolve("https://api.openai.com/v1/chat/completions")
        self.assertIsNotNone(info)
        self.assertEqual(info.provider, "OpenAI")
        self.assertEqual(info.country, "US")
        self.assertEqual(info.category, "AI_MODEL")

    def test_exact_match_sentry(self):
        info = self.resolver.resolve("https://o450.ingest.sentry.io/api/123456/envelope/")
        self.assertIsNotNone(info)
        self.assertEqual(info.provider, "Sentry")
        self.assertEqual(info.category, "LOGGING")

    def test_aws_s3_eu_region(self):
        info = self.resolver.resolve("https://s3.eu-central-1.amazonaws.com/my-bucket")
        self.assertIsNotNone(info)
        self.assertEqual(info.provider, "AWS S3")
        self.assertEqual(info.country, "EU (eu-central-1)")
        self.assertEqual(info.gdpr_risk, "low")

    def test_aws_s3_us_region(self):
        info = self.resolver.resolve("https://s3.us-east-1.amazonaws.com/my-bucket")
        self.assertIsNotNone(info)
        self.assertEqual(info.provider, "AWS S3")
        self.assertEqual(info.country, "US (us-east-1)")
        self.assertEqual(info.gdpr_risk, "medium")

    def test_azure_blob_storage(self):
        info = self.resolver.resolve("https://mystorageaccount.blob.core.windows.net/container")
        self.assertIsNotNone(info)
        self.assertEqual(info.provider, "Azure Blob Storage")
        self.assertEqual(info.country, "Region-Dependent")
        self.assertEqual(info.category, "CLOUD_STORAGE")

    def test_unknown_domain(self):
        info = self.resolver.resolve("https://example.com/api")
        self.assertIsNone(info)

    def test_malformed_url(self):
        info = self.resolver.resolve("not-a-url")
        self.assertIsNone(info)

if __name__ == '__main__':
    unittest.main()
