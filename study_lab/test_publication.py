"""No acepta cambios del HTML de aplicación como transformación de plataforma."""
import importlib.util,pathlib,unittest
path=pathlib.Path(__file__).parent/'scripts/verify_private_publication.py'
spec=importlib.util.spec_from_file_location('publication',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class PublicationTest(unittest.TestCase):
    expected=b'<!doctype html><body><main>study</main>\n</body>\n</html>\n'
    extra=b"<script>window.__CF$cv$params={}; '/cdn-cgi/challenge-platform/example';</script>"
    def test_exact(self):self.assertFalse(module.compare_document(self.expected,self.expected)['edge_injection_detected'])
    def test_edge_reported(self):
        result=module.compare_document(self.expected.replace(b'</body>',self.extra+b'</body>'),self.expected)
        self.assertTrue(result['app_document_matches']);self.assertTrue(result['edge_injection_detected'])
    def test_application_change_rejected(self):
        with self.assertRaises(ValueError):module.compare_document(self.expected.replace(b'study',b'changed'),self.expected)
    def test_unknown_script_rejected(self):
        with self.assertRaises(ValueError):module.compare_document(self.expected.replace(b'</body>',b'<script>alert(1)</script></body>'),self.expected)
    def test_extra_markup_rejected(self):
        with self.assertRaises(ValueError):module.compare_document(self.expected.replace(b'</body>',self.extra+b'<img src=x></body>'),self.expected)
    def test_truncation_rejected(self):
        with self.assertRaises(ValueError):module.compare_document(self.expected[:-1],self.expected)
    def test_size_limit(self):
        with self.assertRaises(ValueError):module.compare_document(self.expected.replace(b'</body>',self.extra.replace(b'{}',b'{' + b'x'*20000+b'}')+b'</body>'),self.expected)
class HeaderTest(unittest.TestCase):
    expected={'content-security-policy':"default-src 'none'; script-src 'sha256-fixture'; connect-src 'none'",'cache-control':'private, no-store','referrer-policy':'no-referrer','permissions-policy':'camera=()','x-content-type-options':'nosniff'}
    def test_exact_headers(self):module.verify_headers(self.expected,self.expected)
    def test_relaxed_csp_rejected(self):
        observed={**self.expected,'content-security-policy':self.expected['content-security-policy']+" 'unsafe-inline'"}
        with self.assertRaises(ValueError):module.verify_headers(observed,self.expected)
    def test_missing_header_rejected(self):
        observed={**self.expected};del observed['permissions-policy']
        with self.assertRaises(ValueError):module.verify_headers(observed,self.expected)
    def test_cache_order_does_not_change_policy(self):module.verify_headers({**self.expected,'cache-control':'no-store, private'},self.expected)
if __name__=='__main__':unittest.main()
