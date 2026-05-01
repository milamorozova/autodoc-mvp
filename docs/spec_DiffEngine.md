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
| **Дата изменения** | 29 апреля 2026 |
| **Версия** | 0.1 |
| **Теги** | — |
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
    [helpstring("Checks if LLM entities are needed")]
    HRESULT needs_llm_entities([out, retval] SAFEARRAY(IUnknown*)* pVal);

    [helpstring("Checks if there are any changes")]
    HRESULT has_changes([out, retval] VARIANT_BOOL* pVal);

    [helpstring("Returns a summary of the diff")]
    HRESULT summary([out, retval] BSTR* pVal);
};

// Assuming ApiNode is a COM interface as well, replace IUnknown* with the actual interface
// For example: SAFEARRAY(IApiNode*)
// If ApiNode is not a COM interface, you might need to define a struct for it.
// For simplicity, I've used IUnknown* here.

// If ApiNode is a struct, you would define it like this:
/*
typedef struct tagApiNodeData
{
    // ... members of ApiNode ...
} ApiNodeData;

[uuid(YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY), helpstring("Interface for ApiNode")]
interface IApiNode : IUnknown
{
    // ... methods of ApiNode ...
};
*/
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

**Назначение:** Представляет собой запись об одном конкретном изменении или отсутствии изменения для сущности API.

**Логика работы:** Является структурой данных, хранящей квалифицированное имя сущности (`qualname`), ее тип (`node_type`), тип изменения (`change_type`), флаги сложности (`is_complex`) и необходимости LLM-обработки (`needs_llm`), а также ссылки на старый (`old_node`) и новый (`new_node`) узлы API.

**Декораторы класса:** `dataclass`

**Количество публичных методов:** `0` методов

Публичные методы не обнаружены.

#### 2.3.2. Класс `DiffResult`

**Полное имя:** `diff_engine.DiffResult`

**Расположение:** `work/diff_engine.py:45-72`

**Назначение:** Хранит результаты сравнения двух деревьев API-узлов, категоризируя изменения.

**Логика работы:** Содержит списки для добавленных, удаленных, измененных и неизмененных сущностей (`EntityDiff`). Методы класса позволяют определить, какие сущности требуют дальнейшей обработки LLM, проверить наличие каких-либо изменений и получить сводную информацию о количестве каждого типа изменений.

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

**Логика работы:** Итерирует по спискам `added` и `changed` сущностей `EntityDiff`. Если у `EntityDiff` установлен флаг `needs_llm` и существует новый узел (`new_node`), то этот узел добавляется в результирующий список.

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

**Назначение:** Проверяет, были ли обнаружены какие-либо изменения между сравниваемыми API-узлами.

**Логика работы:** Возвращает `True`, если хотя бы один из списков `added`, `removed` или `changed` в объекте `DiffResult` не пуст, и `False` в противном случае.

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

**Назначение:** Генерирует текстовое резюме, описывающее количество различных типов изменений между API-узлами.

**Логика работы:** Формирует список строк, содержащих количество добавленных, удаленных, измененных и неизмененных сущностей, а также количество сущностей, требующих обработки LLM. Затем объединяет эти строки в единую многострочную строку.

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

**Назначение:** Вычисляет различия между двумя деревьями API-узлов и возвращает структурированный результат.

**Логика работы:** Преобразует входные деревья API-узлов в плоские словари по квалифицированным именам. Затем итерирует по всем уникальным квалифицированным именам, сравнивая соответствующие узлы из старого и нового деревьев. Определяет, была ли сущность добавлена, удалена или изменена, и создает объекты `EntityDiff` для каждого случая, классифицируя их по типу изменения, сложности и необходимости LLM-обработки, собирая все в объект `DiffResult`.

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

**Назначение:** Сохраняет текущее дерево API-узлов в виде JSON-файла (снимка) для последующего использования.

**Логика работы:** Создает указанный каталог для снимков, если он еще не существует. Формирует имя файла снимка на основе имени компонента модуля. Преобразует корневой узел дерева API в словарь с помощью вспомогательной функции `_node_to_dict`, затем сериализует этот словарь в JSON-строку с отступами и сохраняет ее в файл. Возвращает путь к созданному файлу снимка.

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

**Назначение:** Загружает сохраненное дерево API-узлов (снимок) для указанного модуля из файла.

**Логика работы:** Формирует путь к файлу снимка, используя имя модуля и каталог снимков. Проверяет существование файла; если файл не найден, возвращает `None`. В противном случае загружает JSON-данные из файла, преобразует их обратно в структуру дерева API-узлов с помощью вспомогательной функции `_dict_to_node` и возвращает полученный узел.

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

**Назначение:** Сравнивает текущее дерево API-узлов с сохраненным ранее "снимком" (snapshot) и определяет, является ли это первым запуском.

**Логика работы:** Пытается загрузить снимок для указанного модуля из заданного каталога. Если снимок не найден (первый запуск), создает `DiffResult`, где все сущности текущего дерева помечены как добавленные и требующие LLM-обработки, и возвращает этот результат вместе с флагом `True`. Если снимок найден, вызывает `compute_diff` для сравнения текущего дерева со старым снимком и возвращает результат сравнения вместе с флагом `False`.

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