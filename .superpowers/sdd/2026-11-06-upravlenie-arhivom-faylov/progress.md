# SDD ledger — plan: /srv/projects/ProjectDeleteFilesFromZKGU_BGU/docs/superpowers/plans/2026-11-06-upravlenie-arhivom-faylov.md

Executor: inline (executing-plans). Project is not a git repository.
Ruling: scripts/task-start and scripts/task-done require git (`git rev-parse HEAD`), which this project does not have — run tests manually and append ledger lines by hand; BASE is recorded as "n/a (no git)". Cost if wrong: no commit-range provenance for each task; the ledger + build artefacts are the only record.

## Pre-flight scan

| Producer | Consumer | Interface | Finding |
|---|---|---|---|
| Task 1 | Task 2 | `Forms/СписокФайлов/Ext/Form.xml` + `Module.bsl` | OK — Task 2 edits the copy. |
| Task 2 | Task 4 | `Очистка_ОчиститьЗаписьНаСервере(Индекс)` | OK — Task 4 augments its body. |
| Task 2 | Task 3 | form element ids 105..107 (attrs), 111..118 (items) | OK — Task 3 uses attr 104, items 108..110. No collision. |
| Task 2 | Task 3 | `ГруппаПараметры` order | OK — `Период` (id 108) sits before `ГруппаПрогресса` (id 111), so the "outside progress group" test holds. |
| Task 3 | Task 2/4 | `Период` attribute type `v8:StandardPeriod` | OK — separate attribute, no shared code. |
| Task 3 | Task 4 | manifest `periodStart`/`periodEnd` | OK — Task 4 does not touch the manifest header. |
| Task 5 | Task 1 | `tests/test_archive_guards.py` MODULE path | OK — Task 5 adds a test that reads the original tree, does not change MODULE. |

Pre-flight: no blocking conflicts.
## Task 1: complete

- Created scaffold via epf-init (2.20), copied `Forms/ВсеФайлы` → `Forms/СписокФайлов`, new form uuid `3414bede-e2e8-4f15-81f2-800682f8981b`, form registered as DefaultForm.
- `tests/test_archive_guards.py` MODULE → new module.
- Tests: `python3 -m unittest tests.test_archive_guards -v` → Ran 21 tests, OK.
- `epf-validate` → Validation OK (11 checks). `form-validate` → 0 errors, 1 warning (pre-existing dead code).
- Build: `build/УправлениеАрхивомПрисоединенныхФайловОчисткаИВосстановление.epf` created; log clean.
- Task 1: Ruling: plan Step 4 says add `<Version>1.0.0</Version>` to ExternalDataProcessor Properties, but platform 8.3.27 rejects it: "Свойство Version не входит в состав объекта метаданных ExternalDataProcessor". Removed the element; `Метаданные.Версия` returns empty as in the original processor, so `configVersion` in the manifest stays an empty string — same behaviour as before. Cost if wrong: manifest cannot advertise a version, but no consumer requires one (manifest validation only checks configName).

## Task 2: complete

- Form: attributes `Прогресс` (105), `ПрогрессНадпись` (106), `ПрогрессВидимость` (107); `UsualGroup ГруппаПрогресса` (111..118) with `ProgressBarField` + `LabelField`.
- Module: `НачатьПрогресс`, `ОбновитьПрогресс`, `ЗавершитьПрогресс`; old `ФормаПрогресс` opening removed; progress wired into archive/check/clear/restore.
- Clear split into `Функция Очистка_ОчиститьЗаписьНаСервере(Индекс)` returning `Структура("Результат, Сообщение")`; summary logged on the client.
- Tests: `python3 -m unittest tests.test_archive_guards` → Ran 22 tests, OK (RED observed first: 2 failures).
- `form-validate` → 0 errors, 1 pre-existing warning. Build clean.
- Task 2: Ruling: plan Step 3 does not mention initial visibility, but spec (design line ~157) requires the progress group hidden until work starts — added `<Visible>false</Visible>` to `ГруппаПрогресса`. Cost if wrong: none functional; the group simply starts hidden, `НачатьПрогресс` shows it.

## Task 3: complete

- Form: attribute `Период` (`v8:StandardPeriod`, id 104), InputField id 108 in `ГруппаПараметры` between `ГруппаКаталог` and `ГруппаСеанс`.
- Module: `ПериодЗадан`, `ВПериоде`, `ЭффективнаяДата`, `ДатаВладельцаЗаписи`, `ОписаниеПериода`; analysis split into `ВыполнитьАнализНаСервере` (dispatcher) + `ВыполнитьАнализПоПериоду` + `ВыполнитьАнализБезПериода`; queue builders filter by period; manifest gets `periodStart`/`periodEnd`.
- Tests: `python3 -m unittest tests.test_archive_guards` → Ran 26 tests, OK (RED observed: 6 failures).
- `form-validate` 0 errors; build clean.
- Task 3: Ruling: the spec's "реквизит «Дата» владельца" cannot be detected through `Метаданные...Реквизиты` — standard document attributes are not dumped into `Document.xml`, so `Реквизиты.Найти("Дата")` returns `Неопределено` even for documents. Implemented `ДатаВладельцаЗаписи` as a `Попытка` around `ВладелецФайла.Дата`, cached per owner (including the "no date" outcome) in the passed `Соответствие`. Cost if wrong: one caught exception per distinct owner type during analysis only; correctness unchanged (fallback is file creation date, as specified).
- Task 3: Ruling: for owner catalogs without `ДатаСоздания` the query emits `ДАТАВРЕМЯ(1, 1, 1)` instead of `НЕОПРЕДЕЛЕНО` (a NULL/undefined literal is not portable in query text); the empty date is treated as "no date" by `ВПериоде`. Cost if wrong: none — empty date already means unfilled.

## Task 4: complete

- Added `ЗаписатьОтметкуВАрхиве` (manager record: `Файл`, `Прочитать()`, `ДатаПереносаВАрхив`, `УсловноПеренесенВАрхив = Ложь`, `Записать()`), `ОтметитьАрхивным`, `СнятьОтметкуАрхива`.
- Clear marks before `УдалитьДвоичныеДанные`; restore clears the mark before `ЗаписатьДвоичныеДанные`; `СведенияОФайлах` record locked for file-rows whose catalog is not `Файлы`.
- Files without versions: cleared, not marked, message in the result row and in the log.
- Tests: Ran 31 tests, OK (RED observed: 5 failures). Build clean.

## Task 5: complete

- `src/СозданиеАрхиваДокументооборота.xml`: removed `<Form>ВсеФайлы</Form>`.
- `src/СозданиеАрхиваДокументооборота/Forms/Основная/Ext/Form.xml`: removed `<UsualGroup name="ГруппаВсеФайлы" id="902">…</UsualGroup>` (20 lines) and `<Command name="ВсеФайлы" id="7">…</Command>` (16 lines); diff against the previous EPF dump shows exactly 36 removed lines, 0 added.
- `src/СозданиеАрхиваДокументооборота/Forms/Основная/Ext/Form/Module.bsl`: removed `Процедура ВсеФайлы(Команда)` with its comment (10 lines).
- Deleted `Forms/ВсеФайлы/` and `Forms/ВсеФайлы.xml`.
- Tests: Ran 32 tests, OK. `epf-validate` OK for both catalogs; `form-validate` for `Основная` → 1 error, 3 warnings — the error and all warnings are pre-existing (identical result on the untouched EPF dump `/tmp/opencode/epf-old`).
- Both EPFs rebuilt; build logs clean.
- Task 5: Ruling: an earlier scripted deletion in `Основная/Ext/Form.xml` over-captured a block and broke the XML (987 lines, unbalanced `UsualGroup`). Recovered the file from the previously built EPF (`/tmp/opencode/epf-old`, dumped with `/DumpExternalDataProcessorOrReportToFiles`) and re-applied the two deletions with a line-based, XML-parsed cut. The restored file is the dumped form with CRLF→LF normalized and exactly the two blocks removed. Cost if wrong: the form's whitespace/indentation now matches the platform dump rather than the hand-edited original — cosmetic only; `form-validate` and the build confirm the structure.

## Task 6: complete

- `README.md`: переписан под две обработки — новая (полный цикл) и исходная (только 1С-Отчётность); добавлены отличия (прогресс-бар, период, отметка), порядок работы, команды сборки, ограничения отметки (не видна в списке; файлы без версий не отмечаются; манифесты прежней сборки отклоняются по `configName`; `configVersion` пуст).
- `docs/design/all-attached-files.md`: исправлен пример `configName` (имя обработки, не конфигурации), `configVersion` пуст, добавлена шапка о выносе режима, «имя конфигурации» → «`configName` (имя обработки)».
- `docs/design/upravlenie-arhivom-faylov.md`: статус «реализован», зафиксирована недоступность `Метаданные.Версия` у `ExternalDataProcessor`.
- `docs/testing/bgu-area25-protocol.md`: помечено, что прогон относится к прежней сборке; шаг 1 дополнен новой обработкой.
- `docs/testing/upravlenie-arhivom-acceptance.md`: создан чек-лист приёмки (0 подготовка, 1 исходная обработка, 2 открытие, 3 период, 4 прогресс, 5 очистка/отметка, 6 восстановление, 7 негативные, 8 результат).
- `tests/acceptance-matrix.md`: строки 1–37 помечены как прежняя сборка; исправлена строка 3 (11 проверок, прежняя ошибка `ОстановитьВыполнение`), строка 35; добавлены строки 38–45 (вынос режима, прогресс, период, отметка, снятие отметки, файлы без версий, очистка по одной записи, приёмка на копии).
- Round-trip обеих обработок: все файлы совпали побайтно после нормализации BOM/CRLF. Файлов, отсутствующих в исходниках или в выгрузке, нет.
- Финальные проверки: 32 теста OK; `epf-validate` OK ×2; `form-validate` `СписокФайлов` — 0 ошибок, `Основная` — 1 прежняя ошибка + 3 прежних предупреждения (воспроизводятся на неизменённой выгрузке прежнего EPF); обе EPF собраны, логи чистые.
- Task 6: Ruling: обратная выгрузка выявила, что у реквизита `Прогресс` был не указан тип (`<Type><v8:NumberQualifiers>…` без `<v8:Type>xs:decimal</v8:Type>`), и платформа молча заменила тип на «любой» (`<Type/>`). Добавлен `<v8:Type>xs:decimal</v8:Type>`, обработка пересобрана, повторная выгрузка совпала. Cost if wrong: без этого тип реквизита остался бы составным, и `ProgressBarField` на нём мог не работать в рантайме.

## Правки по ревью (после Task 6)

- `ВыполнитьАнализКлиент`: прогресс двигается по источникам — один серверный шаг на справочник (`Анализ_ИсточникиНаСервере` → `Анализ_ШагНаСервере`); иначе на большой базе `НачатьПрогресс`/`ЗавершитьПрогресс` стояли без промежуточных обновлений.
- `ЗаписьВПериоде` выделена как отдельная функция; в кеше дат отсутствие даты владельца кешируется маркером `Дата(1, 1, 1)` — `Соответствие.Найти` не отличает отсутствующий ключ от сохранённого `Неопределено`.
- Счётчики исключённых по периоду записей добавлены в итоги анализа (`Анализ_ИтогиНаСервере`).
- `Попытка/Исключение` + гарантированный `ЗавершитьПрогресс()` во всех пяти операциях (архивирование, проверка, очистка, восстановление, анализ).
- `ТаблицаРезультата.Очистить()` перед циклом очистки; `ПутьФайлаАрхиваКлиент` перенесён внутрь `Попытка`.
- `СнятьОтметкуАрхива` вызывается и в ветке «Уже восстановлено».
- Добавлена блокировка `НаличиеФайлов` (`ОбъектСФайлами`) в порядке: карточка/версия → `НаличиеФайлов` → `СведенияОФайлах` → `ХранилищеФайлов`. Порядок устраняет ABBA-взаимоблокировку с подпиской БСП.
- Прогресс открывается **до** `Архив_НачатьНаСервере`.
- Тесты: `tests/test_archive_guards.py` — 41 тест (было 32): шаговый анализ, `ДатаНачала`, кеш дат, порядок блокировок, сброс таблицы. Удалены `tests/test_isolation_instrumentation.py` и `tests/isolation/instrumentation.py`. `python3 -m unittest discover -s tests` → 48 тестов OK.

### Дефект: свойства `СтандартныйПериод`

- **Симптом.** В рантайме «Анализ» падал: «Поле объекта не обнаружено (НачалоПериода)».
- **Причина.** Первая версия кода обращалась к `Период.НачалоПериода` / `Период.КонецПериода`. У значения типа `СтандартныйПериод` (реквизит формы `<v8:Type>v8:StandardPeriod</v8:Type>`) таких свойств нет: правильные — `ДатаНачала` и `ДатаОкончания` (подтверждено по `bgu`, `Обработки.ОбменССистемойУчетаИмущества.Форма`, стр. 177).
- **Ловушка.** У `ДокументЖурнал.ФормаСписка.Период` (динамический список, элемент `Period`) свойства `НачалоПериода`/`КонецПериода` есть — это другое значение, и проверка по имени элемента даёт ложное подтверждение.
- **Исправление.** 6 + 6 замен в `Module.bsl`; исправлены `docs/design/upravlenie-arhivom-faylov.md` и `README.md`; добавлен тест `test_standard_period_uses_datanachala_not_nachaloperioda` (отрицательные проверки на `Период.НачалоПериода`/`Период.КонецПериода`).

### Самодиагностика периода (временная процедура)

Временная `СамодиагностикаПериода` вызывалась из `ПриСозданииНаСервере`, 13 проверок, затем удалена:

| # | Проверка | Результат |
|---|---|---|
| 1 | пустой период: `ПериодЗадан()` | `Нет` |
| 2 | период 01.01.2024–31.12.2024: `ПериодЗадан()` | `Да` |
| 3 | `ОписаниеПериода()` | «с 01.01.2024 по 31.12.2024» |
| 4 | дата внутри периода | `Да` |
| 5 | граница начала периода | `Да` |
| 6 | дата до периода (23:59:59 31.12.2023) | `Нет` |
| 7 | дата после периода | `Нет` |
| 8 | пустая дата | `Нет` |
| 9 | эффективная дата без владельца = `ДатаСоздания` | 05.05.2024 |
| 10 | запись без владельца, дата в периоде | `Да` |
| 11 | запись без даты | `Нет` |
| 12 | после сброса границ: `ПериодЗадан()` | `Нет` |
| 13 | процедура завершилась | да |

- Самодиагностика удалена; `Module.bsl` — 2099 строк.

### Финальная сборка и проверки

- Пересборка: `build/УправлениеАрхивомПрисоединенныхФайловОчисткаИВосстановление.epf` (02:12), лог чистый.
- Обратная выгрузка `/tmp/opencode/epf-final` — **ROUND-TRIP EQUAL** (файлов только в исходниках или только в выгрузке нет).
- Рантайм-прогон финальной сборки на `_build_base_bgu` (`1cv8 ENTERPRISE /Execute`, Xvfb): форма открылась → модуль скомпилирован; «Анализ» выполнился («Период не задан: в анализ вошли все записи, включая записи без даты», «Всего: 0 байт», «0 записей»); строк самодиагностики в логе нет; прогресс открылся и скрылся.
- `python3 -m unittest discover -s tests` → 48 тестов OK; `epf-validate` — OK; `form-validate` `СписокФайлов` — 0 ошибок, 1 прежнее предупреждение.
- Изменяющие операции (архивирование, очистка с отметкой, восстановление) на копии базы с файлами остаются за чек-листом `docs/testing/upravlenie-arhivom-acceptance.md`.

## Дефект №2: `Кеш.Найти` у `Соответствия`

- **Симптом (из отчёта пользователя).** «Ошибка анализа: {…Форма.СписокФайлов.Форма(733)}: Метод объекта не обнаружен (Найти)».
- **Причина.** `ЭффективнаяДата` искала дату владельца в кеше через `Кеш.Найти(ВладелецФайла)`. У `Соответствия` метода `Найти` нет — поиск выполняется `Получить`. Воспроизведено минимальной проверкой в рантайме 8.3.27 на `_build_base_bgu`: `ТипЗнч(Новый Соответствие)` = `Соответствие`, а `К.Найти(1)` сразу падает с этой ошибкой; `К.Получить(1)` работает.
- **Почему не поймалось раньше.** Путь исполняется только при **заполненном периоде и непустом владельце**. Рантайм-прогон шёл без периода (`ПоПериоду = Ложь` — `ЗаписьВПериоде` не вызывалась), а прежняя самодиагностика подавала `Неопределено` в качестве владельца, и `ЭффективнаяДата` выходила по раннему `Возврат` до обращения к кешу. Слепое пятно самодиагностики: все 13 пунктов использовали `Неопределено` как владельца.
- **Исправление.** `Кеш.Найти(...)` → `Кеш.Получить(...)`; комментарий переписан. Логика маркера сохранена: `Получить` тоже не отличает отсутствующий ключ от сохранённого `Неопределено`, поэтому отсутствие даты по-прежнему кешируется `Дата(1, 1, 1)`, а `Неопределено` в кеш не попадает никогда.
- **Проверка функции в рантайме** (временная `ДиагностикаКеша`, затем удалена; значения — `_build_base_bgu`, `Справочники.Организации.ПустаяСсылка()` как владелец, период 2024):

| Проверка | Результат |
|---|---|
| тип кеша | `Соответствие` |
| `Получить(1)` на пустом | `Неопределено` |
| `Количество()` | 0 |
| `ПериодЗадан()` | Да |
| промах кеша, дата в периоде | Да |
| ключей после промаха | 1 |
| в кеше маркер `Дата(1,1,1)` | Да |
| попадание кеша, дата в периоде | Да |
| попадание кеша, дата вне периода | Нет |
| эффективная дата без владельца | 05.05.2024 |
| итог | успех |

- **Проверка полного пути на реальных записях** (`_build_base`, 5 записей, 284 байта; временно заполненный период 2000–2030, затем снято): «Период отбора: с 01.01.2000 по 31.12.2030», «Исключено по периоду записей: 5», итоги анализа — без исключения. Строка «Исключено по периоду» пишется только после прохода всех источников, то есть `ЗаписьВПериоде` → `ЭффективнаяДата` → `Кеш.Получить` отработали для реальных владельцев.
- **Регрессия.** Добавлен тест `test_date_cache_lookup_uses_poluchit_not_naiti` (нет `Кеш.Найти`, есть `Кеш.Получить` и маркер `Дата(1, 1, 1)`). `python3 -m unittest discover -s tests` → 49 тестов OK. `epf-validate` — OK.
- **Сборка.** Финальный EPF пересобран (02:45) из чистых исходников, обратная выгрузка `/tmp/opencode/epf-fix` — **ROUND-TRIP EQUAL**.
- Документация: `README.md` (ловушка `Соответствие` без `Найти`; рантайм-проверка периода), `docs/design/upravlenie-arhivom-faylov.md` (поиск в кеше через `Получить`, маркер), `tests/acceptance-matrix.md` (строка 47).
