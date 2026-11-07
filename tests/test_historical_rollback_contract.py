"""Checks test-script wiring only; it does not run BSL or prove rollback."""
import pathlib
import unittest


class HistoricalRollbackContract(unittest.TestCase):
    def test_compares_queue_before_and_after_for_the_test_version(self):
        path = pathlib.Path(__file__).parent / 'isolation' / 'historical_rollback.bsl'
        code = path.read_text(encoding='utf-8')
        self.assertIn('ОчередьДо = ТестКоличествоЗаписейОчереди(Старая);', code)
        self.assertIn('ОчередьПосле = ТестКоличествоЗаписейОчереди(Старая);', code)
        self.assertIn('Если ОчередьДо <> ОчередьПосле Тогда', code)
        self.assertIn('Очередь.ИсточникТекста = &ИсточникТекста', code)

    def test_restore_test_invokes_product_and_requires_injected_failure(self):
        path = pathlib.Path(__file__).parent / 'isolation' / 'product_restore_rollback.bsl'
        self.assertTrue(path.is_file(), 'restore rollback scenario is missing')
        code = path.read_text(encoding='utf-8')
        self.assertIn('Восстановление_ВосстановитьНаСервере(0, Адрес);', code)
        self.assertIn('TEST_INJECTED_AFTER_RESTORE_WRITE', code)
        self.assertIn('ТестСравнитьСнимки(СтараяДо, ТестСнимокВерсии(Старая));', code)


if __name__ == '__main__':
    unittest.main()
