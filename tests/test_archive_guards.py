"""Static regression checks; not a substitute for tests in 1C."""
import pathlib
import re
import unittest

MODULE = pathlib.Path(__file__).resolve().parents[1] / 'src/УправлениеАрхивомПрисоединенныхФайловОчисткаИВосстановление/Forms/СписокФайлов/Ext/Form/Module.bsl'
SOURCE = MODULE.read_text(encoding='utf-8-sig')

def method(name):
    pattern = r'(?:Процедура|Функция)\s+' + name + r'\([^\n]*\)(.*?)Конец(?:Процедуры|Функции)'
    match = re.search(pattern, SOURCE, re.S)
    if not match:
        raise AssertionError('Метод не найден: ' + name)
    return match.group(1)

class ArchiveGuards(unittest.TestCase):
    def test_original_processor_no_longer_contains_all_files_form(self):
        root = pathlib.Path(__file__).resolve().parents[1] / 'src/СозданиеАрхиваДокументооборота.xml'
        self.assertNotIn('<Form>ВсеФайлы</Form>', root.read_text(encoding='utf-8-sig'))
        original = (pathlib.Path(__file__).resolve().parents[1] /
                    'src/СозданиеАрхиваДокументооборота/Forms/Основная/Ext/Form/Module.bsl')
        code = original.read_text(encoding='utf-8-sig')
        self.assertNotIn('Форма.ВсеФайлы', code)
        self.assertNotIn('Процедура ВсеФайлы(', code)

    def test_progress_is_embedded_and_covers_all_operations(self):
        self.assertNotIn('ОткрытьФорму(', SOURCE)
        self.assertNotIn('#ФормаПрогресса', SOURCE)
        for name in ('ВыполнитьАнализКлиент', 'ВыполнитьАрхивированиеКлиент',
                     'ВыполнитьПроверкуКлиент', 'ВыполнитьОчисткуКлиент',
                     'ВыполнитьВосстановлениеКлиент'):
            code = method(name)
            self.assertIn('НачатьПрогресс(', code)
            self.assertIn('ЗавершитьПрогресс()', code)
        self.assertIn('ОбновитьПрогресс(', method('ВыполнитьАнализКлиент'))
        self.assertIn('ОбновитьПрогресс(', method('ВыполнитьАрхивированиеКлиент'))
        self.assertIn('ОбновитьПрогресс(', method('ПроверитьФайлыАрхиваКлиент'))
        self.assertIn('ОбновитьПрогресс(', method('ВыполнитьОчисткуКлиент'))
        self.assertIn('ОбновитьПрогресс(', method('ВыполнитьВосстановлениеКлиент'))

    def test_progress_group_is_hidden_even_on_exception(self):
        for name in ('ВыполнитьАнализКлиент', 'ВыполнитьАрхивированиеКлиент',
                     'ВыполнитьПроверкуКлиент', 'ВыполнитьОчисткуКлиент',
                     'ВыполнитьВосстановлениеКлиент'):
            with self.subTest(method=name):
                code = method(name)
                self.assertIn('Попытка', code)
                self.assertIn('Исключение', code)
                # Завершение прогресса должно быть после обработчика, а не
                # только внутри него: иначе группа останется видимой.
                self.assertGreater(code.rindex('ЗавершитьПрогресс()'),
                                   code.rindex('Исключение'))

    def test_analysis_runs_one_server_step_per_source(self):
        client = method('ВыполнитьАнализКлиент')
        self.assertIn('Анализ_ИсточникиНаСервере()', client)
        self.assertIn('Анализ_ШагНаСервере(', client)
        self.assertIn('Для Индекс = 0 По Всего - 1 Цикл', client)
        self.assertIn('Анализ_ИтогиНаСервере(', client)
        sources = method('Анализ_ИсточникиНаСервере')
        for kind in ('"Версии"', '"ФайлыБезВерсий"', '"Присоединенный"'):
            self.assertIn(kind, sources)
        step = method('Анализ_ШагНаСервере')
        for counter in ('ВсегоБайт', 'ПоддерживаемыхБайт', 'ПоддерживаемыхЗаписей', 'Исключено'):
            self.assertIn(counter, step)
        self.assertIn('ДобавитьГруппуСтатистики(', step)

    def test_analysis_applies_period_through_queue_filter(self):
        code = method('Анализ_Пройти')
        self.assertIn('ПериодЗадан()', code)
        self.assertIn('ЗаписьВПериоде(Выборка.ВладелецФайла, Выборка.ДатаСоздания, КешДат)', code)

    def test_clear_runs_one_record_per_server_call(self):
        code = method('ВыполнитьОчисткуКлиент')
        self.assertIn('Очистка_ОчиститьЗаписьНаСервере(Индекс)', code)
        self.assertIn('Для Индекс = 0 По Всего - 1 Цикл', code)
        self.assertNotIn('Очистка_ВыполнитьНаСервере()', code)

    def test_clear_resets_result_table_after_verification(self):
        code = method('ВыполнитьОчисткуКлиент')
        self.assertIn('ТаблицаРезультата.Очистить()', code)
        self.assertLess(code.index('ТаблицаРезультата.Очистить()'),
                        code.index('Очистка_ОчиститьЗаписьНаСервере('))

    def test_restore_computes_archive_path_inside_try(self):
        code = method('ВыполнитьВосстановлениеКлиент')
        inner = code.index('Попытка', code.index('НачатьПрогресс('))
        body = code[inner:code.index('Восстановление_ВосстановитьНаСервере(', inner)]
        self.assertIn('ПутьФайлаАрхиваКлиент(', body)

    def test_directory_chooser_uses_platform_async_method(self):
        code = method('КаталогАрхиваНачалоВыбора')
        self.assertIn('Диалог.Показать(Оповещение);', code)
        self.assertNotIn('Диалог.НачатьПоказ(', code)

    def test_directory_check_does_not_create_or_delete_files(self):
        code = method('ПроверитьЗаписьВКаталогКлиент')
        self.assertNotIn('ЗаписатьТекстФайлаКлиент', code)
        self.assertNotIn('УдалитьФайлы', code)

    def test_finalization_rejects_any_unarchived_record(self):
        code = method('Архив_ЗавершитьНаСервере')
        self.assertIn('ОчередьФайлов.Количество()', code)
        self.assertIn('КоличествоЗаархивированных()', code)
        self.assertIn('ВызватьИсключение', code)

    def test_archive_queue_contains_only_infobase_storage(self):
        for name in ('Архив_ДобавитьВерсии', 'Архив_ДобавитьФайлыБезВерсий',
                     'ТекстЗапросаПрисоединенныхФайлов'):
            with self.subTest(method=name):
                self.assertIn('ТипыХраненияФайлов.ВИнформационнойБазе', method(name))

    def test_archive_reads_content_through_bsp_infobase_mechanism(self):
        code = method('СодержимоеФайлаИзИБ')
        self.assertIn('РаботаСФайлами.ХранилищеФайлаИзИнформационнойБазы(', code)
        self.assertIn('ФайлХранилище', code)
        self.assertIn('СодержимоеФайлаИзИБ(', method('Архив_ПодготовитьФайлНаСервере'))

    def test_archive_rechecks_storage_type_before_reading_content(self):
        code = method('Архив_ПодготовитьФайлНаСервере')
        check = code.index('ЭтоХранениеВИнформационнойБазе(ОбъектДанных.ТипХраненияФайла)')
        read = code.index('СодержимоеФайлаИзИБ(')
        self.assertLess(check, read)
        self.assertIn('СтрокаФайла.Поддерживается = Ложь', code)

    def test_finalization_compares_with_supported_expected_count(self):
        code = method('Архив_ЗавершитьНаСервере')
        self.assertIn('КоличествоОжидаемых()', code)

    def test_mutations_guard_precedes_writes(self):
        for name in ('Очистка_ОчиститьЗаписьНаСервере', 'Восстановление_ВосстановитьНаСервере'):
            with self.subTest(method=name):
                code = method(name)
                guard = code.find('ПроверитьБезопасностьИзмененияДанных();')
                first_write = min((p for p in (code.find('ЗаписатьПустоеСодержимое('),
                                                code.find('ЗаписатьСодержимое(')) if p >= 0), default=-1)
                self.assertGreaterEqual(guard, 0)
                self.assertGreater(first_write, guard)

    def test_period_filters_queue_but_not_session_operations(self):
        for name in ('Архив_ДобавитьВерсии', 'Архив_ДобавитьФайлыБезВерсий',
                     'Архив_ДобавитьПрисоединенные'):
            with self.subTest(method=name):
                self.assertIn('ЗаписьВПериоде(', method(name))
        self.assertIn('ПериодЗадан()', method('Анализ_Пройти'))
        for name in ('ВыполнитьПроверкуКлиент', 'ВыполнитьОчисткуКлиент',
                     'ВыполнитьВосстановлениеКлиент'):
            with self.subTest(method=name):
                self.assertNotIn('ЗаписьВПериоде(', method(name))
                self.assertNotIn('ПериодЗадан()', method(name))

    def test_standard_period_uses_datanachala_not_nachaloperioda(self):
        # Реквизит формы типа СтандартныйПериод имеет свойства ДатаНачала и
        # ДатаОкончания; НачалоПериода/КонецПериода у значения нет (проверено
        # в рантайме: «Поле объекта не обнаружено (НачалоПериода)»).
        self.assertNotIn('Период.НачалоПериода', SOURCE)
        self.assertNotIn('Период.КонецПериода', SOURCE)
        self.assertIn('Период.ДатаНачала', method('ПериодЗадан'))
        self.assertIn('Период.ДатаОкончания', method('ПериодЗадан'))

    def test_empty_period_keeps_records_without_dates(self):
        code = method('ЗаписьВПериоде')
        self.assertIn('Если Не ПериодЗадан() Тогда', code)
        self.assertIn('Возврат Истина', code)
        # Даты не вычисляются вовсе: проверка периода стоит до чтения владельца.
        self.assertLess(code.index('Если Не ПериодЗадан() Тогда'),
                        code.index('ЭффективнаяДата('))

    def test_queue_builders_share_one_date_cache_and_count_exclusions(self):
        start = method('Архив_НачатьНаСервере')
        self.assertIn('КешДат = Новый Соответствие', start)
        for call in ('Архив_ДобавитьВерсии(КешДат, Счётчики)',
                     'Архив_ДобавитьФайлыБезВерсий(КешДат, Счётчики)',
                     'Архив_ДобавитьПрисоединенные(КешДат, Счётчики)'):
            self.assertIn(call, start)
        self.assertIn('Исключено по периоду', start)
        self.assertIn('БезДаты', start)

    def test_date_cache_lookup_uses_poluchit_not_naiti(self):
        # У Соответствия нет метода Найти — в рантайме 8.3.27 вызов
        # «Кеш.Найти(...)» падает: «Метод объекта не обнаружен (Найти)».
        # Поиск в кеше — Получить. Неопределено в кеш не попадает: отсутствие
        # даты хранится маркером Дата(1, 1, 1), поэтому Неопределено от
        # Получить однозначно означает «ключа нет».
        self.assertNotIn('Кеш.Найти', SOURCE)
        code = method('ЭффективнаяДата')
        self.assertIn('Кеш.Получить(ВладелецФайла)', code)
        self.assertIn('Кеш.Вставить(ВладелецФайла, Дата(1, 1, 1))', code)

    def test_manifest_stores_period_bounds(self):
        code = method('Архив_НачатьНаСервере')
        self.assertIn('"periodStart"', code)
        self.assertIn('"periodEnd"', code)

    def test_form_period_field_is_outside_progress_group(self):
        xml = (pathlib.Path(__file__).resolve().parents[1] /
               'src/УправлениеАрхивомПрисоединенныхФайловОчисткаИВосстановление/Forms/СписокФайлов/Ext/Form.xml').read_text(encoding='utf-8-sig')
        self.assertIn('<v8:Type>v8:StandardPeriod</v8:Type>', xml)
        group = xml[xml.index('<UsualGroup name="ГруппаПрогресса"'):]
        group = group[:group.index('</UsualGroup>')]
        self.assertNotIn('name="Период"', group)

    def test_mutation_guard_fails_closed(self):
        code = method('ПроверитьБезопасностьИзмененияДанных')
        self.assertIn('ВызватьИсключение', code)

    def test_manifest_binds_session_to_infobase_and_data_area(self):
        start = method('Архив_НачатьНаСервере')
        self.assertIn('"infobaseId"', start)
        self.assertIn('"dataArea"', start)
        self.assertIn('ИдентификаторБазыДляАрхива()', start)
        self.assertIn('ОбластьДанныхДляАрхива()', start)

    def test_manifest_load_rejects_foreign_or_anonymous_identity(self):
        code = method('Манифест_ЗагрузитьНаСервере')
        self.assertIn('infobaseId', code)
        self.assertIn('dataArea', code)
        self.assertIn('ИдентификаторБазыДляАрхива()', code)
        self.assertIn('ОбластьДанныхДляАрхива()', code)
        identity = code.index('infobaseId')
        records = code.index('Манифест.Получить("records")')
        self.assertLess(identity, records)

    def test_mutation_guard_checks_identity_instead_of_refusing_always(self):
        code = method('ПроверитьБезопасностьИзмененияДанных')
        self.assertIn('infobaseId', code)
        self.assertIn('dataArea', code)
        self.assertIn('ИдентификаторБазыДляАрхива()', code)
        self.assertIn('ОбластьДанныхДляАрхива()', code)
        self.assertNotIn('безопасность операций ещё не подтверждена', code)

    def test_clear_removes_content_from_infobase_register_inside_transaction(self):
        code = method('Очистка_ОчиститьЗаписьНаСервере')
        for token in ('НачатьТранзакцию()', 'ОтменитьТранзакцию()',
                      'ЗафиксироватьТранзакцию()', 'ЗаблокироватьЗаписьХранилищаФайлов(',
                      'РегистрыСведений.ХранилищеФайлов.УдалитьДвоичныеДанные(',
                      'СодержимоеФайлаИзИБ('):
            with self.subTest(token=token):
                self.assertIn(token, code)
        lock = code.index('ЗаблокироватьЗаписьХранилищаФайлов(')
        reread = code.index('СодержимоеФайлаИзИБ(')
        delete = code.index('УдалитьДвоичныеДанные(')
        self.assertLess(lock, reread)
        self.assertLess(reread, delete)

    def test_clear_marks_archive_before_removing_content(self):
        code = method('Очистка_ОчиститьЗаписьНаСервере')
        self.assertIn('ОтметитьАрхивным(', code)
        self.assertLess(code.index('ОтметитьАрхивным('),
                        code.index('УдалитьДвоичныеДанные('))

    def test_restore_clears_archive_mark_before_writing_content(self):
        code = method('Восстановление_ВосстановитьНаСервере')
        self.assertIn('СнятьОтметкуАрхива(', code)
        self.assertLess(code.index('СнятьОтметкуАрхива('),
                        code.index('ЗаписатьДвоичныеДанные('))

    def test_restore_clears_mark_when_content_already_matches(self):
        code = method('Восстановление_ВосстановитьНаСервере')
        branch = code.index('Уже восстановлено')
        start = code.rindex('Если ХешДанных(Текущие) = СтрокаФайла.Хеш Тогда', 0, branch)
        self.assertIn('СнятьОтметкуАрхива(', code[start:branch])

    def test_conditional_archive_flag_is_never_set_true(self):
        self.assertNotIn('УсловноПеренесенВАрхив = Истина', SOURCE)
        self.assertIn('УсловноПеренесенВАрхив = Ложь', method('ЗаписатьОтметкуВАрхиве'))

    def test_files_without_versions_are_cleared_without_mark(self):
        code = method('ОтметитьАрхивным')
        self.assertIn('"Файлы"', code)
        self.assertIn('Возврат Ложь', code)

    def test_archive_mark_register_record_is_locked(self):
        self.assertIn('СведенияОФайлах', method('ЗаблокироватьЗаписьХранилищаФайлов'))

    def test_lock_order_matches_bsp_attachment_subscription(self):
        code = method('ЗаблокироватьЗаписьХранилищаФайлов')
        self.assertIn('РегистрСведений.НаличиеФайлов', code)
        self.assertIn('ОбъектСФайлами', code)
        self.assertLess(code.index('РегистрСведений.НаличиеФайлов'),
                        code.index('РегистрСведений.СведенияОФайлах'))

    def test_restore_writes_content_to_infobase_register_inside_transaction(self):
        code = method('Восстановление_ВосстановитьНаСервере')
        for token in ('НачатьТранзакцию()', 'ОтменитьТранзакцию()',
                      'ЗафиксироватьТранзакцию()', 'ЗаблокироватьЗаписьХранилищаФайлов(',
                      'РегистрыСведений.ХранилищеФайлов.ЗаписатьДвоичныеДанные(',
                      'СодержимоеФайлаИзИБ('):
            with self.subTest(token=token):
                self.assertIn(token, code)
        lock = code.index('ЗаблокироватьЗаписьХранилищаФайлов(')
        write = code.index('ЗаписатьДвоичныеДанные(')
        self.assertLess(lock, write)

    def test_mutations_recheck_infobase_storage_type(self):
        for name in ('Очистка_ОчиститьЗаписьНаСервере', 'Восстановление_ВосстановитьНаСервере'):
            with self.subTest(method=name):
                self.assertIn('ЭтоХранениеВИнформационнойБазе(', method(name))

    def test_empty_content_is_excluded_from_expected_count(self):
        code = method('Архив_ПодготовитьФайлНаСервере')
        empty = code.index('пустое содержимое в информационной базе')
        branch_start = code.rindex('Если Данные = Неопределено', 0, empty)
        branch = code[branch_start:code.index('КонецЕсли', empty)]
        self.assertIn('СтрокаФайла.Поддерживается = Ложь', branch)
        expected = method('КоличествоОжидаемых')
        self.assertIn('СтрокаФайла.Поддерживается', expected)

    def test_manifest_validates_field_types_without_raising(self):
        load = method('Манифест_ЗагрузитьНаСервере')
        self.assertIn('ТипЗнч(ОжидаемаяОбласть) <> Тип("Число")', load)
        self.assertIn('ТипЗнч(Записи) <> Тип("Массив")', load)
        self.assertIn('Манифест.Получить("completed") <> Истина', load)
        guard = method('ПроверитьБезопасностьИзмененияДанных')
        self.assertIn('ТипЗнч(ОжидаемаяОбласть) <> Тип("Число")', guard)
        self.assertIn('Шапка.Получить("completed") <> Истина', guard)
        self.assertIn('Шапка.Получить("verified") <> Истина', guard)

    def test_lock_covers_file_version_and_register_record(self):
        code = method('ЗаблокироватьЗаписьХранилищаФайлов')
        self.assertIn('Справочник.ВерсииФайлов', code)
        self.assertIn('Справочник.Файлы', code)
        self.assertIn('РегистрСведений.ХранилищеФайлов', code)
        self.assertIn('Блокировка.Заблокировать()', code)

    def test_historical_version_write_does_not_rewrite_file_card(self):
        code = method('ЗаписатьОбъектСодержимогоФайла')
        self.assertIn('ТекущаяВерсия', code)
        self.assertIn('КонвертацияФайлов', code)

    def test_low_level_writers_guard_before_any_object_access(self):
        for name in ('ЗаписатьПустоеСодержимое', 'ЗаписатьСодержимое', 'ОбновитьРазмерФайла'):
            with self.subTest(method=name):
                code = method(name).strip()
                self.assertTrue(code.startswith('ПроверитьБезопасностьИзмененияДанных();'),
                                f'{name}: guard must be the first statement')

if __name__ == '__main__':
    unittest.main()
