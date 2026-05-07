# Спецификация программного компонента DiffEngine

| Поле | Значение |
|---|---|
| **ЕСПД** | `RU.—.XXXXX-XX` |
| **Имя компонента** | `DiffEngine` |
| **Краткое описание** | Приложение для автоматической обработки данных. |
| **Component Use Category** | — |
| **Component Type** | APPLICATION |
| **CID** | `—` |
| **Marketplace URL** | — |
| **Статус** | черновик |
| **Дата изменения** | 5 мая 2026 |
| **Версия** | 0.1 |
| **Коммит** | `7c63314` |
| **Теги** | diff, API, сравнение, снапшот, изменения, Python |
| **Источник кода** | `work/diff_engine.py` |

| Авторы | Компания |
|---|---|
| _(не указаны, используйте --authors)_ | ПИРФ |

---

## Содержание

<pre>
1. Обзор
   1.1. Введение
   1.2. Примечание
   1.3. Ссылки
2. Компонент DiffEngine
   2.1. IDiffResult IDL
   2.2. Состав интерфейса
   2.3. Подробное описание интерфейса
      2.3.1. Класс EntityDiff
      2.3.2. Класс DiffResult
         2.3.2.1. Метод needs_llm_entities
         2.3.2.2. Метод has_changes
         2.3.2.3. Метод summary
      2.3.3. Функция compute_diff
      2.3.4. Функция save_snapshot
      2.3.5. Функция load_snapshot
      2.3.6. Функция diff_with_snapshot
3. Коды ошибок
Приложение А. Примеры использования
</pre>

---

## 1. Обзор

Данный документ описывает требования к реализации компонента `DiffEngine`.

### 1.1. Введение

Настоящий документ содержит автоматически сформированное описание программного компонента `DiffEngine` на основе анализа исходного кода. Документ отражает состав интерфейса, обнаруженные классы, функции, методы, их сигнатуры, параметры, возвращаемые значения и исключения.

### 1.2. Примечание

Документ сформирован автоматически. Структурные данные извлечены из исходного кода статическим анализом. Текстовые описания сгенерированы языковой моделью на основе сигнатур и docstring.

### 1.3. Ссылки

Данный параграф содержит ссылки на компонент и на другую полезную информацию:

—

---

## 2. Компонент DiffEngine

Приложение для автоматической обработки данных.

### 2.1. IDiffResult IDL

```idl
[uuid(XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX), helpstring("Interface for DiffResult")]
interface IDiffResult : IUnknown
{
    [helpstring("Checks if LLM entities are needed.")]
    HRESULT needs_llm_entities([out, retval] VARIANT_BOOL* pNeedsLLMEntities);

    [helpstring("Checks if there are any changes.")]
    HRESULT has_changes([out, retval] VARIANT_BOOL* pHasChanges);

    [helpstring("Returns a summary of the diff.")]
    HRESULT summary([out, retval] BSTR* pSummary);
};

// Assuming ApiNode is a simple structure for demonstration
typedef struct tagApiNode
{
    BSTR name;
    long id;
} ApiNode;

// Assuming DiffResultData is a structure to represent ApiNode list
typedef struct tagDiffResultData
{
    SAFEARRAY(ApiNode) apiNodes;
} DiffResultData;
```

### 2.2. Состав интерфейса

**Общая сводка:**

- 2 класса
- 4 функции верхнего уровня
- 3 метода

**Классы:**

- `EntityDiff` — строка `33`, публичных методов: `0`
- `DiffResult` — строка `45`, публичных методов: `3`

**Функции верхнего уровня:**

- `def compute_diff(old_root: ApiNode, new_root: ApiNode) -> DiffResult` — строка `79`
- `def save_snapshot(doc: ModuleDocModel, snapshot_dir: str = 'snapshots') -> Path` — строка `154`
- `def load_snapshot(module_name: str, snapshot_dir: str = 'snapshots') -> Optional[ApiNode]` — строка `173`
- `def diff_with_snapshot(doc: ModuleDocModel, snapshot_dir: str = 'snapshots') -> Tuple[DiffResult, bool]` — строка `188`

### 2.3. Подробное описание интерфейса

#### 2.3.1. Класс `EntityDiff`

**Полное имя:** `diff_engine.EntityDiff`

**Расположение:** `work/diff_engine.py:33-41`

**Назначение:** Представляет собой запись об отличии между двумя версиями одной и той же сущности API.

**Логика работы:** Является структурой данных, хранящей информацию о сущности, включая ее полное имя (`qualname`), тип узла (`node_type`), тип изменения (`change_type`), является ли сущность сложной (`is_complex`), требует ли обработки LLM (`needs_llm`), а также ссылки на старый (`old_node`) и новый (`new_node`) узлы API.

**Декораторы класса:** `dataclass`

**Количество публичных методов:** `0` методов

Публичные методы не обнаружены.

#### 2.3.2. Класс `DiffResult`

**Полное имя:** `diff_engine.DiffResult`

**Расположение:** `work/diff_engine.py:45-72`

**Назначение:** Хранит результаты сравнения двух деревьев API-узлов, категоризируя изменения.

**Логика работы:** Содержит списки для добавленных, удаленных, измененных и неизмененных сущностей (`EntityDiff`). Методы класса позволяют получить список узлов, требующих обработки LLM, проверить наличие каких-либо изменений и сгенерировать краткое текстовое резюме результатов сравнения.

**Декораторы класса:** `dataclass`

**Количество публичных методов:** `3` метода

**Список публичных методов:**

- `2.3.2.1. def needs_llm_entities(self) -> List[ApiNode]`
- `2.3.2.2. def has_changes(self) -> bool`
- `2.3.2.3. def summary(self) -> str`

##### 2.3.2.1. Метод `needs_llm_entities`

**Полное имя:** `diff_engine.DiffResult.needs_llm_entities`

**Сигнатура:** `def needs_llm_entities(self) -> List[ApiNode]`

**Расположение:** `work/diff_engine.py:51-57`

**Назначение:** Собирает список API-узлов, которые были добавлены или изменены и требуют дальнейшей обработки с помощью LLM.

**Логика работы:** Итерирует по спискам добавленных и измененных сущностей. Для каждой сущности, если она помечена как требующая LLM (`needs_llm`) и имеет новый узел (`new_node`), этот узел добавляется в результирующий список.

**Параметры:**

отсутствуют

**Возвращаемое значение:** `List[ApiNode]`

**Исключения:**

- явные исключения не обнаружены

**Пример использования:**

```python
obj = DiffResult()
result = obj.needs_llm_entities()
```

##### 2.3.2.2. Метод `has_changes`

**Полное имя:** `diff_engine.DiffResult.has_changes`

**Сигнатура:** `def has_changes(self) -> bool`

**Расположение:** `work/diff_engine.py:59-60`

**Назначение:** Определяет, были ли обнаружены какие-либо изменения между сравниваемыми API-узлами.

**Логика работы:** Проверяет, не пусты ли списки добавленных, удаленных или измененных сущностей в объекте `DiffResult`. Если хотя бы один из этих списков содержит элементы, метод возвращает `True`, указывая на наличие изменений.

**Параметры:**

отсутствуют

**Возвращаемое значение:** `bool`

**Исключения:**

- явные исключения не обнаружены

**Пример использования:**

```python
obj = DiffResult()
result = obj.has_changes()
```

##### 2.3.2.3. Метод `summary`

**Полное имя:** `diff_engine.DiffResult.summary`

**Сигнатура:** `def summary(self) -> str`

**Расположение:** `work/diff_engine.py:62-72`

**Назначение:** Генерирует текстовое резюме, обобщающее результаты сравнения API-узлов.

**Логика работы:** Формирует список строк, содержащих количество добавленных, удаленных, измененных и неизмененных сущностей. Также подсчитывается количество сущностей, требующих обработки LLM. Все строки объединяются в одну многострочную строку.

**Параметры:**

отсутствуют

**Возвращаемое значение:** `str`

**Исключения:**

- явные исключения не обнаружены

**Пример использования:**

```python
obj = DiffResult()
result = obj.summary()
```

#### 2.3.3. Функция `compute_diff`

**Полное имя:** `diff_engine.compute_diff`

**Сигнатура:** `def compute_diff(old_root: ApiNode, new_root: ApiNode) -> DiffResult`

**Расположение:** `work/diff_engine.py:79-147`

**Назначение:** Вычисляет различия между двумя деревьями API-узлов и возвращает их в виде структурированного объекта `DiffResult`.

**Логика работы:** Сначала оба входных дерева API-узлов преобразуются в плоские словари (`_flatten_tree`) для удобства доступа по полному имени (`qualname`). Затем происходит итерация по всем уникальным полным именам из обоих деревьев. Для каждой сущности определяется, была ли она добавлена, удалена или изменена. В зависимости от типа изменения и сложности узла (`_is_complex`, `_detect_change_type`, `_decide_needs_llm`) создаются соответствующие записи `EntityDiff` и добавляются в списки объекта `DiffResult`.

**Параметры:**

| Параметр | Тип | По умолчанию | Вид |
|---|---|---|---|
| `old_root` | `ApiNode` | обязательный | позиционный или именованный |
| `new_root` | `ApiNode` | обязательный | позиционный или именованный |

**Возвращаемое значение:** `DiffResult`

**Исключения:**

- явные исключения не обнаружены

**Пример использования:**

```python
# old_root: создайте объект типа ApiNode
# new_root: создайте объект типа ApiNode
result = compute_diff(old_root, new_root)
```

#### 2.3.4. Функция `save_snapshot`

**Полное имя:** `diff_engine.save_snapshot`

**Сигнатура:** `def save_snapshot(doc: ModuleDocModel, snapshot_dir: str = 'snapshots') -> Path`

**Расположение:** `work/diff_engine.py:154-170`

**Назначение:** Сохраняет текущее дерево API-узлов модуля в виде JSON-файла (снапшота) для последующего использования.

**Логика работы:** Создает директорию для снапшотов, если она не существует. Формирует имя файла снапшота на основе имени компонента модуля. Преобразует корневой узел дерева API в словарь с помощью `_node_to_dict`, затем сериализует этот словарь в JSON-строку с отступами и записывает ее в соответствующий файл. Возвращает путь к созданному файлу.

**Параметры:**

| Параметр | Тип | По умолчанию | Вид |
|---|---|---|---|
| `doc` | `ModuleDocModel` | обязательный | позиционный или именованный |
| `snapshot_dir` | `str` | `'snapshots'` | позиционный или именованный |

**Возвращаемое значение:** `Path`

**Исключения:**

- явные исключения не обнаружены

**Пример использования:**

```python
# doc: создайте объект типа ModuleDocModel
result = save_snapshot(doc, 'snapshots')
```

#### 2.3.5. Функция `load_snapshot`

**Полное имя:** `diff_engine.load_snapshot`

**Сигнатура:** `def load_snapshot(module_name: str, snapshot_dir: str = 'snapshots') -> Optional[ApiNode]`

**Расположение:** `work/diff_engine.py:173-185`

**Назначение:** Загружает сохраненное дерево API-узлов (снапшот) для заданного модуля из JSON-файла.

**Логика работы:** Формирует путь к файлу снапшота, используя имя модуля и директорию снапшотов. Проверяет существование файла; если файл не найден, возвращает `None`. В случае успеха, читает содержимое файла, парсит JSON-данные и преобразует их обратно в структуру дерева API-узлов с помощью `_dict_to_node`.

**Параметры:**

| Параметр | Тип | По умолчанию | Вид |
|---|---|---|---|
| `module_name` | `str` | обязательный | позиционный или именованный |
| `snapshot_dir` | `str` | `'snapshots'` | позиционный или именованный |

**Возвращаемое значение:** `Optional[ApiNode]`

**Исключения:**

- явные исключения не обнаружены

**Пример использования:**

```python
result = load_snapshot('example_module', 'snapshots')
```

#### 2.3.6. Функция `diff_with_snapshot`

**Полное имя:** `diff_engine.diff_with_snapshot`

**Сигнатура:** `def diff_with_snapshot(doc: ModuleDocModel, snapshot_dir: str = 'snapshots') -> Tuple[DiffResult, bool]`

**Расположение:** `work/diff_engine.py:188-215`

**Назначение:** Сравнивает текущее дерево API-узлов модуля с его сохраненным состоянием (снапшотом) и определяет, является ли это первым запуском.

**Логика работы:** Пытается загрузить снапшот для указанного модуля с помощью `load_snapshot`. Если снапшот не найден (первый запуск), все узлы текущего дерева считаются добавленными, и возвращается `(DiffResult, True)`. Если снапшот найден, вызывается `compute_diff` для сравнения текущего дерева с загруженным снапшотом, и возвращается `(DiffResult, False)`.

**Параметры:**

| Параметр | Тип | По умолчанию | Вид |
|---|---|---|---|
| `doc` | `ModuleDocModel` | обязательный | позиционный или именованный |
| `snapshot_dir` | `str` | `'snapshots'` | позиционный или именованный |

**Возвращаемое значение:** `Tuple[DiffResult, bool]`

**Исключения:**

- явные исключения не обнаружены

**Пример использования:**

```python
# doc: создайте объект типа ModuleDocModel
result = diff_with_snapshot(doc, 'snapshots')
```

---

## 3. Коды ошибок

По результатам автоматического анализа явные пользовательские исключения в коде не обнаружены. Ниже приведены стандартные заглушки.

| Код ошибки | Значение | Описание |
|---|---|---|
| `ERR_ECO_SUCCESES`          | `0x0000` | Выполнено успешно. Ошибок нет. |
| `ERR_ECO_UNEXPECTED`        | `0xFFFF` | Непредвиденное условие. |
| `ERR_ECO_POINTER`           | `0xFFEE` | Передано неправильное значение указателя. |
| `ERR_ECO_NOINTERFACE`       | `0xFFED` | Такой интерфейс не поддерживается. |
| `ERR_ECO_COMPONENT_NOTFOUND`| `0xFFE9` | Компонент не найден. |

---

## Приложение А. Примеры использования

### А.1 `diff_engine.DiffResult.needs_llm_entities`

```python
obj = DiffResult()
result = obj.needs_llm_entities()
```

### А.2 `diff_engine.DiffResult.has_changes`

```python
obj = DiffResult()
result = obj.has_changes()
```

### А.3 `diff_engine.DiffResult.summary`

```python
obj = DiffResult()
result = obj.summary()
```

### А.4 `diff_engine.compute_diff`

```python
# old_root: создайте объект типа ApiNode
# new_root: создайте объект типа ApiNode
result = compute_diff(old_root, new_root)
```

### А.5 `diff_engine.save_snapshot`

```python
# doc: создайте объект типа ModuleDocModel
result = save_snapshot(doc, 'snapshots')
```

### А.6 `diff_engine.load_snapshot`

```python
result = load_snapshot('example_module', 'snapshots')
```

### А.7 `diff_engine.diff_with_snapshot`

```python
# doc: создайте объект типа ModuleDocModel
result = diff_with_snapshot(doc, 'snapshots')
```