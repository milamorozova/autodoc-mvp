# Спецификация программного компонента fastapi_app

| Поле | Значение |
|---|---|
| **ЕСПД** | `RU.—.XXXXX-XX` |
| **Имя компонента** | `fastapi_app` |
| **Краткое описание** | Основной класс FastAPI-приложения для создания REST API с автоматической документацией OpenAPI. |
| **Component Use Category** | — |
| **Component Type** | APPLICATION |
| **CID** | `—` |
| **Marketplace URL** | — |
| **Статус** | черновик |
| **Дата изменения** | 18 мая 2026 |
| **Версия** | 0.1 |
| **Коммит** | `53b512a` |
| **Теги** | API, веб-сервер, маршрутизация, обработка ошибок, события, middleware, WebSocket |
| **Источник кода** | `work/fastapi_app.py` |

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
2. Компонент fastapi_app
   2.1. IFastAPI IDL
   2.2. Состав интерфейса
   2.3. Подробное описание интерфейса
      2.3.1. Класс FastAPI
         2.3.1.1. Метод build_middleware_stack
         2.3.1.2. Метод openapi
         2.3.1.3. Метод setup
         2.3.1.4. Метод add_api_route
         2.3.1.5. Метод api_route
         2.3.1.6. Метод add_api_websocket_route
         2.3.1.7. Метод websocket
         2.3.1.8. Метод include_router
         2.3.1.9. Метод get
         2.3.1.10. Метод put
         2.3.1.11. Метод post
         2.3.1.12. Метод delete
         2.3.1.13. Метод options
         2.3.1.14. Метод head
         2.3.1.15. Метод patch
         2.3.1.16. Метод trace
         2.3.1.17. Метод websocket_route
         2.3.1.18. Метод on_event
         2.3.1.19. Метод middleware
         2.3.1.20. Метод exception_handler
3. Коды ошибок
Приложение А. Примеры использования
</pre>

---

## 1. Обзор

Данный документ описывает требования к реализации компонента `fastapi_app`.

### 1.1. Введение

Настоящий документ содержит автоматически сформированное описание программного компонента `fastapi_app` на основе анализа исходного кода. Документ отражает состав интерфейса, обнаруженные классы, функции, методы, их сигнатуры, параметры, возвращаемые значения и исключения.

### 1.2. Примечание

Документ сформирован автоматически. Структурные данные извлечены из исходного кода статическим анализом. Текстовые описания сгенерированы языковой моделью на основе сигнатур и docstring.

### 1.3. Ссылки

Данный параграф содержит ссылки на компонент и на другую полезную информацию:

—

---

## 2. Компонент fastapi_app

Основной класс FastAPI-приложения для создания REST API с автоматической документацией OpenAPI.

### 2.1. IFastAPI IDL

```idl
// Forward declarations for complex types
// Assuming these types are defined elsewhere or can be represented as simple structures.
// For simplicity, we'll use basic structures for dict and list elements.

// Placeholder for ASGIApp
typedef [uuid(00000000-0000-0000-0000-000000000001)] struct ASGIApp {};

// Placeholder for Callable
typedef [uuid(00000000-0000-0000-0000-000000000002)] struct Callable {};

// Placeholder for Any
typedef [uuid(00000000-0000-0000-0000-000000000003)] struct AnyType {};

// Placeholder for Depends
typedef [uuid(00000000-0000-0000-0000-000000000004)] struct Depends {};

// Placeholder for Enum
typedef [uuid(00000000-0000-0000-0000-000000000005)] struct EnumType {};

// Placeholder for IncEx
typedef [uuid(00000000-0000-0000-0000-000000000006)] struct IncEx {};

// Placeholder for Response
typedef [uuid(00000000-0000-0000-0000-000000000007)] struct Response {};

// Placeholder for DefaultPlaceholder
typedef [uuid(00000000-0000-0000-0000-000000000008)] struct DefaultPlaceholder {};

// Placeholder for BaseRoute
typedef [uuid(00000000-0000-0000-0000-000000000009)] struct BaseRoute {};

// Placeholder for DecoratedCallable
typedef [uuid(00000000-0000-0000-0000-00000000000A)] struct DecoratedCallable {};

// Structure to represent dict[str, Any]
typedef [uuid(00000000-0000-0000-0000-00000000000B)] struct StringAnyDict {
    [string] BSTR key;
    AnyType value;
};

// Structure to represent list[str | Enum]
typedef [uuid(00000000-0000-0000-0000-00000000000C)] struct StringEnumList {
    VARIANT_BOOL isString; // 0 for EnumType, 1 for string
    [switch_is(isString)] union {
        [case(1)] [string] BSTR stringValue;
        [case(0)] EnumType enumValue;
    };
};

// Structure to represent dict[int | str, dict[str, Any]]
typedef [uuid(00000000-0000-0000-0000-00000000000D)] struct IntStrStringAnyDict {
    VARIANT_BOOL isInt; // 0 for string, 1 for int
    [switch_is(isInt)] union {
        [case(1)] long intKey;
        [case(0)] [string] BSTR stringKey;
    };
    SAFEARRAY(StringAnyDict) value;
};

// Structure to represent list[Depends]
typedef [uuid(00000000-0000-0000-0000-00000000000E)] struct DependsList {
    [size_is(cElements)] Depends aElements[1];
    ULONG cElements;
};

// Structure to represent list[str]
typedef [uuid(00000000-0000-0000-0000-00000000000F)] struct StringList {
    [size_is(cElements)] [string] BSTR aElements[1];
    ULONG cElements;
};

// Structure to represent list[BaseRoute]
typedef [uuid(00000000-0000-0000-0000-000000000010)] struct BaseRouteList {
    [size_is(cElements)] BaseRoute aElements[1];
    ULONG cElements;
};

// Structure to represent dict[str, Any] for openapi_extra
typedef [uuid(00000000-0000-0000-0000-000000000011)] struct OpenapiExtraDict {
    [string] BSTR key;
    AnyType value;
};

// Structure to represent list[str | Enum] for tags
typedef [uuid(00000000-0000-0000-0000-000000000012)] struct TagsList {
    VARIANT_BOOL isString; // 0 for EnumType, 1 for string
    [switch_is(isString)] union {
        [case(1)] [string] BSTR stringValue;
        [case(0)] EnumType enumValue;
    };
};

// Structure to represent dict[int | str, dict[str, Any]] for responses
typedef [uuid(00000000-0000-0000-0000-000000000013)] struct ResponsesDict {
    VARIANT_BOOL isInt; // 0 for string, 1 for int
    [switch_is(isInt)] union {
        [case(1)] long intKey;
        [case(0)] [string] BSTR stringKey;
    };
    SAFEARRAY(StringAnyDict) value;
};

// Structure to represent list[str] for methods
typedef [uuid(00000000-0000-0000-0000-000000000014)] struct MethodsList {
    [size_is(cElements)] [string] BSTR aElements[1];
    ULONG cElements;
};

// Structure to represent dict[str, Any] for openapi_extra
typedef [uuid(00000000-0000-0000-0000-000000000015)] struct OpenapiExtraDict {
    [string] BSTR key;
    AnyType value;
};

// Structure to represent list[BaseRoute] for callbacks
typedef [uuid(00000000-0000-0000-0000-000000000016)] struct CallbacksList {
    [size_is(cElements)] BaseRoute aElements[1];
    ULONG cElements;
};

// Structure to represent dict[str, Any] for openapi_extra
typedef [uuid(00000000-0000-0000-0000-000000000017)] struct OpenapiExtraDict {
    [string] BSTR key;
    AnyType value;
};

// Structure to represent dict[str, Any] for openapi_extra
typedef [uuid(00000000-0000-0000-0000-000000000018)] struct OpenapiExtraDict {
    [string] BSTR key;
    AnyType value;
};

// Structure to represent dict[str, Any] for openapi_extra
typedef [uuid(00000000-0000-0000-0000-000000000019)] struct OpenapiExtraDict {
    [string] BSTR key;
    AnyType value;
};

// Structure to represent dict[str, Any] for openapi_extra
typedef [uuid(00000000-0000-0000-0000-00000000001A)] struct OpenapiExtraDict {
    [string] BSTR key;
    AnyType value;
};

// Structure to represent dict[str, Any] for openapi_extra
typedef [uuid(00000000-0000-0000-0000-00000000001B)] struct OpenapiExtraDict {
    [string] BSTR key;
    AnyType value;
};

// Structure to represent dict[str, Any] for openapi_extra
typedef [uuid(00000000-0000-0000-0000-00000000001C)] struct OpenapiExtraDict {
    [string] BSTR key;
    AnyType value;
};

// Structure to represent dict[str, Any] for openapi_extra
typedef [uuid(00000000-0000-0000-0000-00000000001D)] struct OpenapiExtraDict {
    [string] BSTR key;
    AnyType value;
};

// Structure to represent dict[str, Any] for openapi_extra
typedef [uuid(00000000-0000-0000-0000-00000000001E)] struct OpenapiExtraDict {
    [string] BSTR key;
    AnyType value;
};

// Structure to represent dict[str, Any] for openapi_extra
typedef [uuid(00000000-0000-0000-0000-00000000001F)] struct OpenapiExtraDict {
    [string] BSTR key;
    AnyType value;
};

// Structure to represent dict[str, Any] for openapi_extra
typedef [uuid(00000000-0000-0000-0000-000000000020)] struct OpenapiExtraDict {
    [string] BSTR key;
    AnyType value;
};

// Structure to represent dict[str, Any] for openapi_extra
typedef [uuid(00000000-0000-0000-0000-000000000021)] struct OpenapiExtraDict {
    [string] BSTR key;
    AnyType value;
};

// Structure to represent dict[str, Any] for openapi_extra
typedef [uuid(00000000-0000-0000-0000-000000000022)] struct OpenapiExtraDict {
    [string] BSTR key;
    AnyType value;
};

// Structure to represent dict[str, Any] for openapi_extra
typedef [uuid(00000000-0000-0000-0000-000000000023)] struct OpenapiExtraDict {
    [string] BSTR key;
    AnyType value;
};

// Structure to represent dict[str, Any] for openapi_extra
typedef [uuid(00000000-0000-0000-0000-000000000024)] struct OpenapiExtraDict {
    [string] BSTR key;
    AnyType value;
};

// Structure to represent dict[str, Any] for openapi_extra
typedef [uuid(00000000-0000-0000-0000-000000000025)] struct OpenapiExtraDict {
    [string] BSTR key;
    AnyType value;
};

// Structure to represent dict[str, Any] for openapi_extra
typedef [uuid(00000000-0000-0000-0000-000000000026)] struct OpenapiExtraDict {
    [string] BSTR key;
    AnyType value;
};

// Structure to represent dict[str, Any] for openapi_extra
typedef [uuid(00000000-0000-0000-0000-000000000027)] struct OpenapiExtraDict {
    [string] BSTR key;
    AnyType value;
};

// Structure to represent dict[str, Any] for openapi_extra
typedef [uuid(00000000-0000-0000-0000-000000000028)] struct OpenapiExtraDict {
    [string] BSTR key;
    AnyType value;
};

// Structure to represent dict[str, Any] for openapi_extra
typedef [uuid(00000000-0000-0000-0000-000000000029)] struct OpenapiExtraDict {
    [string] BSTR key;
    AnyType value;
};

// Structure to represent dict[str, Any] for openapi_extra
typedef [uuid(00000000-0000-0000-0000-00000000002A)] struct OpenapiExtraDict {
    [string] BSTR key;
    AnyType value;
};

// Structure to represent dict[str, Any] for openapi_extra
typedef [uuid(00000000-0000-0000-0000-00000000002B)] struct OpenapiExtraDict {
    [string] BSTR key;
    AnyType value;
};

// Structure to represent dict[str, Any] for openapi_extra
typedef [uuid(00000000-0000-0000-0000-00000000002C)] struct OpenapiExtraDict {
    [string] BSTR key;
    AnyType value;
};

// Structure to represent dict[str, Any] for openapi_extra
typedef [uuid(00000000-0000-0000-0000-00000000002D)] struct OpenapiExtraDict {
    [string] BSTR key;
    AnyType value;
};

// Structure to represent dict[str, Any] for openapi_extra
typedef [uuid(00000000-0000-0000-0000-00000000002E)] struct OpenapiExtraDict {
    [string] BSTR key;
    AnyType value;
};

// Structure to represent dict[str, Any] for openapi_extra
typedef [uuid(00000000-0000-0000-0000-00000000002F)] struct OpenapiExtraDict {
    [string] BSTR key;
    AnyType value;
};

// Structure to represent dict[str, Any] for openapi_extra
typedef [uuid(00000000-0000-0000-0000-000000000030)] struct OpenapiExtraDict {
    [string] BSTR key;
    AnyType value;
};

// Structure to represent dict[str, Any] for openapi_extra
typedef [uuid(00000000-0000-0000-0000-000000000031)] struct OpenapiExtraDict {
    [string] BSTR key;
    AnyType value;
};

// Structure to represent dict[str, Any] for openapi_extra
typedef [uuid(00000000-0000-0000-0000-000000000032)] struct OpenapiExtraDict {
    [string] BSTR key;
    AnyType value;
};

// Structure to represent dict[str, Any] for openapi_extra
typedef [uuid(00000000-0000-0000-0000-000000000033)] struct OpenapiExtraDict {
    [string] BSTR key;
    AnyType value;
};

// Structure to represent dict[str, Any] for openapi_extra
typedef [uuid(00000000-
```

### 2.2. Состав интерфейса

**Общая сводка:**

- 1 класс
- 0 функций верхнего уровня
- 20 методов

**Классы:**

- `FastAPI` — строка `41`, публичных методов: `20`

### 2.3. Подробное описание интерфейса

#### 2.3.1. Класс `FastAPI`

**Полное имя:** `fastapi_app.FastAPI`

**Расположение:** `work/fastapi_app.py:41-4691`

**Назначение:** `FastAPI` app class, the main entrypoint to use FastAPI.

**Количество публичных методов:** `20` методов

**Конструктор:**

```python
obj = FastAPI(False, None, 'FastAPI', None, '', '0.1.0', '/openapi.json', None, None, None, Default(JSONResponse), True, '/docs', '/redoc', '/docs/oauth2-redirect', None, None, None, None, None, None, None, None, None, '', '', True, None, None, None, None, True, None, Default(generate_unique_id), True, None, True, key='value')
```

**Список публичных методов:**

- `2.3.1.1. def build_middleware_stack(self) -> ASGIApp`
- `2.3.1.2. def openapi(self) -> dict[str, Any]`
- `2.3.1.3. def setup(self) -> None`
- `2.3.1.4. def add_api_route(self, path: str, endpoint: Callable[..., Any], *, response_model: Any = Default(None), status_code: int | None = None, tags: list[str | Enum] | None = None, dependencies: Sequence[Depends] | None = None, summary: str | None = None, description: str | None = None, response_description: str = 'Successful Response', responses: dict[int | str, dict[str, Any]] | None = None, deprecated: bool | None = None, methods: list[str] | None = None, operation_id: str | None = None, response_model_include: IncEx | None = None, response_model_exclude: IncEx | None = None, response_model_by_alias: bool = True, response_model_exclude_unset: bool = False, response_model_exclude_defaults: bool = False, response_model_exclude_none: bool = False, include_in_schema: bool = True, response_class: type[Response] | DefaultPlaceholder = Default(JSONResponse), name: str | None = None, openapi_extra: dict[str, Any] | None = None, generate_unique_id_function: Callable[[routing.APIRoute], str] = Default(generate_unique_id)) -> None`
- `2.3.1.5. def api_route(self, path: str, *, response_model: Any = Default(None), status_code: int | None = None, tags: list[str | Enum] | None = None, dependencies: Sequence[Depends] | None = None, summary: str | None = None, description: str | None = None, response_description: str = 'Successful Response', responses: dict[int | str, dict[str, Any]] | None = None, deprecated: bool | None = None, methods: list[str] | None = None, operation_id: str | None = None, response_model_include: IncEx | None = None, response_model_exclude: IncEx | None = None, response_model_by_alias: bool = True, response_model_exclude_unset: bool = False, response_model_exclude_defaults: bool = False, response_model_exclude_none: bool = False, include_in_schema: bool = True, response_class: type[Response] = Default(JSONResponse), name: str | None = None, openapi_extra: dict[str, Any] | None = None, generate_unique_id_function: Callable[[routing.APIRoute], str] = Default(generate_unique_id)) -> Callable[[DecoratedCallable], DecoratedCallable]`
- `2.3.1.6. def add_api_websocket_route(self, path: str, endpoint: Callable[..., Any], name: str | None = None, *, dependencies: Sequence[Depends] | None = None) -> None`
- `2.3.1.7. def websocket(self, path: str, name: str | None = None, *, dependencies: Sequence[Depends] | None = None) -> Callable[[DecoratedCallable], DecoratedCallable]`
- `2.3.1.8. def include_router(self, router: routing.APIRouter, *, prefix: str = '', tags: list[str | Enum] | None = None, dependencies: Sequence[Depends] | None = None, responses: dict[int | str, dict[str, Any]] | None = None, deprecated: bool | None = None, include_in_schema: bool = True, default_response_class: type[Response] = Default(JSONResponse), callbacks: list[BaseRoute] | None = None, generate_unique_id_function: Callable[[routing.APIRoute], str] = Default(generate_unique_id)) -> None`
- `2.3.1.9. def get(self, path: str, *, response_model: Any = Default(None), status_code: int | None = None, tags: list[str | Enum] | None = None, dependencies: Sequence[Depends] | None = None, summary: str | None = None, description: str | None = None, response_description: str = 'Successful Response', responses: dict[int | str, dict[str, Any]] | None = None, deprecated: bool | None = None, operation_id: str | None = None, response_model_include: IncEx | None = None, response_model_exclude: IncEx | None = None, response_model_by_alias: bool = True, response_model_exclude_unset: bool = False, response_model_exclude_defaults: bool = False, response_model_exclude_none: bool = False, include_in_schema: bool = True, response_class: type[Response] = Default(JSONResponse), name: str | None = None, callbacks: list[BaseRoute] | None = None, openapi_extra: dict[str, Any] | None = None, generate_unique_id_function: Callable[[routing.APIRoute], str] = Default(generate_unique_id)) -> Callable[[DecoratedCallable], DecoratedCallable]`
- `2.3.1.10. def put(self, path: str, *, response_model: Any = Default(None), status_code: int | None = None, tags: list[str | Enum] | None = None, dependencies: Sequence[Depends] | None = None, summary: str | None = None, description: str | None = None, response_description: str = 'Successful Response', responses: dict[int | str, dict[str, Any]] | None = None, deprecated: bool | None = None, operation_id: str | None = None, response_model_include: IncEx | None = None, response_model_exclude: IncEx | None = None, response_model_by_alias: bool = True, response_model_exclude_unset: bool = False, response_model_exclude_defaults: bool = False, response_model_exclude_none: bool = False, include_in_schema: bool = True, response_class: type[Response] = Default(JSONResponse), name: str | None = None, callbacks: list[BaseRoute] | None = None, openapi_extra: dict[str, Any] | None = None, generate_unique_id_function: Callable[[routing.APIRoute], str] = Default(generate_unique_id)) -> Callable[[DecoratedCallable], DecoratedCallable]`
- `2.3.1.11. def post(self, path: str, *, response_model: Any = Default(None), status_code: int | None = None, tags: list[str | Enum] | None = None, dependencies: Sequence[Depends] | None = None, summary: str | None = None, description: str | None = None, response_description: str = 'Successful Response', responses: dict[int | str, dict[str, Any]] | None = None, deprecated: bool | None = None, operation_id: str | None = None, response_model_include: IncEx | None = None, response_model_exclude: IncEx | None = None, response_model_by_alias: bool = True, response_model_exclude_unset: bool = False, response_model_exclude_defaults: bool = False, response_model_exclude_none: bool = False, include_in_schema: bool = True, response_class: type[Response] = Default(JSONResponse), name: str | None = None, callbacks: list[BaseRoute] | None = None, openapi_extra: dict[str, Any] | None = None, generate_unique_id_function: Callable[[routing.APIRoute], str] = Default(generate_unique_id)) -> Callable[[DecoratedCallable], DecoratedCallable]`
- `2.3.1.12. def delete(self, path: str, *, response_model: Any = Default(None), status_code: int | None = None, tags: list[str | Enum] | None = None, dependencies: Sequence[Depends] | None = None, summary: str | None = None, description: str | None = None, response_description: str = 'Successful Response', responses: dict[int | str, dict[str, Any]] | None = None, deprecated: bool | None = None, operation_id: str | None = None, response_model_include: IncEx | None = None, response_model_exclude: IncEx | None = None, response_model_by_alias: bool = True, response_model_exclude_unset: bool = False, response_model_exclude_defaults: bool = False, response_model_exclude_none: bool = False, include_in_schema: bool = True, response_class: type[Response] = Default(JSONResponse), name: str | None = None, callbacks: list[BaseRoute] | None = None, openapi_extra: dict[str, Any] | None = None, generate_unique_id_function: Callable[[routing.APIRoute], str] = Default(generate_unique_id)) -> Callable[[DecoratedCallable], DecoratedCallable]`
- `2.3.1.13. def options(self, path: str, *, response_model: Any = Default(None), status_code: int | None = None, tags: list[str | Enum] | None = None, dependencies: Sequence[Depends] | None = None, summary: str | None = None, description: str | None = None, response_description: str = 'Successful Response', responses: dict[int | str, dict[str, Any]] | None = None, deprecated: bool | None = None, operation_id: str | None = None, response_model_include: IncEx | None = None, response_model_exclude: IncEx | None = None, response_model_by_alias: bool = True, response_model_exclude_unset: bool = False, response_model_exclude_defaults: bool = False, response_model_exclude_none: bool = False, include_in_schema: bool = True, response_class: type[Response] = Default(JSONResponse), name: str | None = None, callbacks: list[BaseRoute] | None = None, openapi_extra: dict[str, Any] | None = None, generate_unique_id_function: Callable[[routing.APIRoute], str] = Default(generate_unique_id)) -> Callable[[DecoratedCallable], DecoratedCallable]`
- `2.3.1.14. def head(self, path: str, *, response_model: Any = Default(None), status_code: int | None = None, tags: list[str | Enum] | None = None, dependencies: Sequence[Depends] | None = None, summary: str | None = None, description: str | None = None, response_description: str = 'Successful Response', responses: dict[int | str, dict[str, Any]] | None = None, deprecated: bool | None = None, operation_id: str | None = None, response_model_include: IncEx | None = None, response_model_exclude: IncEx | None = None, response_model_by_alias: bool = True, response_model_exclude_unset: bool = False, response_model_exclude_defaults: bool = False, response_model_exclude_none: bool = False, include_in_schema: bool = True, response_class: type[Response] = Default(JSONResponse), name: str | None = None, callbacks: list[BaseRoute] | None = None, openapi_extra: dict[str, Any] | None = None, generate_unique_id_function: Callable[[routing.APIRoute], str] = Default(generate_unique_id)) -> Callable[[DecoratedCallable], DecoratedCallable]`
- `2.3.1.15. def patch(self, path: str, *, response_model: Any = Default(None), status_code: int | None = None, tags: list[str | Enum] | None = None, dependencies: Sequence[Depends] | None = None, summary: str | None = None, description: str | None = None, response_description: str = 'Successful Response', responses: dict[int | str, dict[str, Any]] | None = None, deprecated: bool | None = None, operation_id: str | None = None, response_model_include: IncEx | None = None, response_model_exclude: IncEx | None = None, response_model_by_alias: bool = True, response_model_exclude_unset: bool = False, response_model_exclude_defaults: bool = False, response_model_exclude_none: bool = False, include_in_schema: bool = True, response_class: type[Response] = Default(JSONResponse), name: str | None = None, callbacks: list[BaseRoute] | None = None, openapi_extra: dict[str, Any] | None = None, generate_unique_id_function: Callable[[routing.APIRoute], str] = Default(generate_unique_id)) -> Callable[[DecoratedCallable], DecoratedCallable]`
- `2.3.1.16. def trace(self, path: str, *, response_model: Any = Default(None), status_code: int | None = None, tags: list[str | Enum] | None = None, dependencies: Sequence[Depends] | None = None, summary: str | None = None, description: str | None = None, response_description: str = 'Successful Response', responses: dict[int | str, dict[str, Any]] | None = None, deprecated: bool | None = None, operation_id: str | None = None, response_model_include: IncEx | None = None, response_model_exclude: IncEx | None = None, response_model_by_alias: bool = True, response_model_exclude_unset: bool = False, response_model_exclude_defaults: bool = False, response_model_exclude_none: bool = False, include_in_schema: bool = True, response_class: type[Response] = Default(JSONResponse), name: str | None = None, callbacks: list[BaseRoute] | None = None, openapi_extra: dict[str, Any] | None = None, generate_unique_id_function: Callable[[routing.APIRoute], str] = Default(generate_unique_id)) -> Callable[[DecoratedCallable], DecoratedCallable]`
- `2.3.1.17. def websocket_route(self, path: str, name: str | None = None) -> Callable[[DecoratedCallable], DecoratedCallable]`
- `2.3.1.18. def on_event(self, event_type: str) -> Callable[[DecoratedCallable], DecoratedCallable]`
- `2.3.1.19. def middleware(self, middleware_type: str) -> Callable[[DecoratedCallable], DecoratedCallable]`
- `2.3.1.20. def exception_handler(self, exc_class_or_status_code: int | type[Exception]) -> Callable[[DecoratedCallable], DecoratedCallable]`

##### 2.3.1.1. Метод `build_middleware_stack`

**Полное имя:** `fastapi_app.FastAPI.build_middleware_stack`

**Сигнатура:** `def build_middleware_stack(self) -> ASGIApp`

**Расположение:** `work/fastapi_app.py:1018-1066`

**Назначение:** Эта функция собирает и конфигурирует стек промежуточного программного обеспечения (middleware) для приложения FastAPI.

**Логика работы:** Функция создает список промежуточного программного обеспечения, включая обработчики ошибок, пользовательские middleware и специфичные для FastAPI middleware, такие как `AsyncExitStackMiddleware`. Затем она последовательно оборачивает основной маршрутизатор приложения (`self.router`) каждым элементом middleware, создавая итоговое ASGI-приложение.

**Параметры:**

отсутствуют

**Возвращаемое значение:** `ASGIApp`

**Исключения:**

- явные исключения не обнаружены

**Пример использования:**

```python
obj = FastAPI()
result = obj.build_middleware_stack()
```

##### 2.3.1.2. Метод `openapi`

**Полное имя:** `fastapi_app.FastAPI.openapi`

**Сигнатура:** `def openapi(self) -> dict[str, Any]`

**Расположение:** `work/fastapi_app.py:1068-1099`

**Назначение:** Generate the OpenAPI schema of the application. This is called by FastAPI
internally.

The first time it is called it stores the result in the attribute
`app.openapi_schema`, and next times it is called, it just returns that same
result. To avoid the cost of generating the schema every time.

If you need to modify the generated OpenAPI schema, you could modify it.

Read more in the
[FastAPI docs for OpenAPI](https://fastapi.tiangolo.com/how-to/extending-openapi/).

**Параметры:**

отсутствуют

**Возвращаемое значение:** `dict[str, Any]`

**Исключения:**

- явные исключения не обнаружены

**Пример использования:**

```python
obj = FastAPI()
result = obj.openapi()
```

##### 2.3.1.3. Метод `setup`

**Полное имя:** `fastapi_app.FastAPI.setup`

**Сигнатура:** `def setup(self) -> None`

**Расположение:** `work/fastapi_app.py:1101-1154`

**Назначение:** Эта функция выполняет начальную настройку приложения FastAPI, в частности, добавляет маршруты для документации API (Swagger UI и ReDoc), если они включены.

**Логика работы:** Функция проверяет наличие URL-адресов для документации (`openapi_url`, `docs_url`, `redoc_url`). Если они заданы, она определяет соответствующие асинхронные функции-обработчики, которые генерируют и возвращают HTML-страницы документации, и добавляет их как маршруты к приложению с помощью `self.add_route`.

**Параметры:**

отсутствуют

**Возвращаемое значение:** `None`

**Исключения:**

- явные исключения не обнаружены

**Пример использования:**

```python
obj = FastAPI()
result = obj.setup()
```

##### 2.3.1.4. Метод `add_api_route`

**Полное имя:** `fastapi_app.FastAPI.add_api_route`

**Сигнатура:** `def add_api_route(self, path: str, endpoint: Callable[..., Any], *, response_model: Any = Default(None), status_code: int | None = None, tags: list[str | Enum] | None = None, dependencies: Sequence[Depends] | None = None, summary: str | None = None, description: str | None = None, response_description: str = 'Successful Response', responses: dict[int | str, dict[str, Any]] | None = None, deprecated: bool | None = None, methods: list[str] | None = None, operation_id: str | None = None, response_model_include: IncEx | None = None, response_model_exclude: IncEx | None = None, response_model_by_alias: bool = True, response_model_exclude_unset: bool = False, response_model_exclude_defaults: bool = False, response_model_exclude_none: bool = False, include_in_schema: bool = True, response_class: type[Response] | DefaultPlaceholder = Default(JSONResponse), name: str | None = None, openapi_extra: dict[str, Any] | None = None, generate_unique_id_function: Callable[[routing.APIRoute], str] = Default(generate_unique_id)) -> None`

**Расположение:** `work/fastapi_app.py:1161-1216`

**Назначение:** Эта функция используется для добавления HTTP-маршрута к приложению FastAPI, который будет обрабатывать входящие запросы по указанному пути.

**Логика работы:** Функция принимает путь, конечную точку (функцию-обработчик запроса) и множество необязательных параметров для настройки поведения маршрута. Она делегирует добавление маршрута объекту `self.router`, передавая ему все полученные параметры.

**Параметры:**

| Параметр | Тип | По умолчанию | Вид |
|---|---|---|---|
| `path` | `str` | обязательный | позиционный или именованный |
| `endpoint` | `Callable[..., Any]` | обязательный | позиционный или именованный |
| `response_model` | `Any` | `Default(None)` | только именованный |
| `status_code` | `int | None` | `None` | только именованный |
| `tags` | `list[str | Enum] | None` | `None` | только именованный |
| `dependencies` | `Sequence[Depends] | None` | `None` | только именованный |
| `summary` | `str | None` | `None` | только именованный |
| `description` | `str | None` | `None` | только именованный |
| `response_description` | `str` | `'Successful Response'` | только именованный |
| `responses` | `dict[int | str, dict[str, Any]] | None` | `None` | только именованный |
| `deprecated` | `bool | None` | `None` | только именованный |
| `methods` | `list[str] | None` | `None` | только именованный |
| `operation_id` | `str | None` | `None` | только именованный |
| `response_model_include` | `IncEx | None` | `None` | только именованный |
| `response_model_exclude` | `IncEx | None` | `None` | только именованный |
| `response_model_by_alias` | `bool` | `True` | только именованный |
| `response_model_exclude_unset` | `bool` | `False` | только именованный |
| `response_model_exclude_defaults` | `bool` | `False` | только именованный |
| `response_model_exclude_none` | `bool` | `False` | только именованный |
| `include_in_schema` | `bool` | `True` | только именованный |
| `response_class` | `type[Response] | DefaultPlaceholder` | `Default(JSONResponse)` | только именованный |
| `name` | `str | None` | `None` | только именованный |
| `openapi_extra` | `dict[str, Any] | None` | `None` | только именованный |
| `generate_unique_id_function` | `Callable[[routing.APIRoute], str]` | `Default(generate_unique_id)` | только именованный |

**Возвращаемое значение:** `None`

**Исключения:**

- явные исключения не обнаружены

**Пример использования:**

```python
obj = FastAPI()
result = obj.add_api_route('output.json', 'http://example.com', response_model=Default(None), status_code=None, tags=None, dependencies=None, summary=None, description=None, response_description='Successful Response', responses=None, deprecated=None, methods=None, operation_id=None, response_model_include=None, response_model_exclude=None, response_model_by_alias=True, response_model_exclude_unset=False, response_model_exclude_defaults=False, response_model_exclude_none=False, include_in_schema=True, response_class=Default(JSONResponse), name='Alice', openapi_extra=None, generate_unique_id_function=Default(generate_unique_id))
```

##### 2.3.1.5. Метод `api_route`

**Полное имя:** `fastapi_app.FastAPI.api_route`

**Сигнатура:** `def api_route(self, path: str, *, response_model: Any = Default(None), status_code: int | None = None, tags: list[str | Enum] | None = None, dependencies: Sequence[Depends] | None = None, summary: str | None = None, description: str | None = None, response_description: str = 'Successful Response', responses: dict[int | str, dict[str, Any]] | None = None, deprecated: bool | None = None, methods: list[str] | None = None, operation_id: str | None = None, response_model_include: IncEx | None = None, response_model_exclude: IncEx | None = None, response_model_by_alias: bool = True, response_model_exclude_unset: bool = False, response_model_exclude_defaults: bool = False, response_model_exclude_none: bool = False, include_in_schema: bool = True, response_class: type[Response] = Default(JSONResponse), name: str | None = None, openapi_extra: dict[str, Any] | None = None, generate_unique_id_function: Callable[[routing.APIRoute], str] = Default(generate_unique_id)) -> Callable[[DecoratedCallable], DecoratedCallable]`

**Расположение:** `work/fastapi_app.py:1218-1276`

**Назначение:** Эта функция служит декоратором для определения HTTP-маршрутов в приложении FastAPI, позволяя настраивать их поведение через аргументы.

**Логика работы:** Функция принимает путь и множество необязательных параметров для настройки маршрута. Она возвращает декоратор, который при применении к функции-обработчику запроса регистрирует этот маршрут через `self.router.add_api_route`, передавая все настроенные параметры.

**Параметры:**

| Параметр | Тип | По умолчанию | Вид |
|---|---|---|---|
| `path` | `str` | обязательный | позиционный или именованный |
| `response_model` | `Any` | `Default(None)` | только именованный |
| `status_code` | `int | None` | `None` | только именованный |
| `tags` | `list[str | Enum] | None` | `None` | только именованный |
| `dependencies` | `Sequence[Depends] | None` | `None` | только именованный |
| `summary` | `str | None` | `None` | только именованный |
| `description` | `str | None` | `None` | только именованный |
| `response_description` | `str` | `'Successful Response'` | только именованный |
| `responses` | `dict[int | str, dict[str, Any]] | None` | `None` | только именованный |
| `deprecated` | `bool | None` | `None` | только именованный |
| `methods` | `list[str] | None` | `None` | только именованный |
| `operation_id` | `str | None` | `None` | только именованный |
| `response_model_include` | `IncEx | None` | `None` | только именованный |
| `response_model_exclude` | `IncEx | None` | `None` | только именованный |
| `response_model_by_alias` | `bool` | `True` | только именованный |
| `response_model_exclude_unset` | `bool` | `False` | только именованный |
| `response_model_exclude_defaults` | `bool` | `False` | только именованный |
| `response_model_exclude_none` | `bool` | `False` | только именованный |
| `include_in_schema` | `bool` | `True` | только именованный |
| `response_class` | `type[Response]` | `Default(JSONResponse)` | только именованный |
| `name` | `str | None` | `None` | только именованный |
| `openapi_extra` | `dict[str, Any] | None` | `None` | только именованный |
| `generate_unique_id_function` | `Callable[[routing.APIRoute], str]` | `Default(generate_unique_id)` | только именованный |

**Возвращаемое значение:** `Callable[[DecoratedCallable], DecoratedCallable]`

**Исключения:**

- явные исключения не обнаружены

**Пример использования:**

```python
obj = FastAPI()
result = obj.api_route('output.json', response_model=Default(None), status_code=None, tags=None, dependencies=None, summary=None, description=None, response_description='Successful Response', responses=None, deprecated=None, methods=None, operation_id=None, response_model_include=None, response_model_exclude=None, response_model_by_alias=True, response_model_exclude_unset=False, response_model_exclude_defaults=False, response_model_exclude_none=False, include_in_schema=True, response_class=Default(JSONResponse), name='Alice', openapi_extra=None, generate_unique_id_function=Default(generate_unique_id))
```

##### 2.3.1.6. Метод `add_api_websocket_route`

**Полное имя:** `fastapi_app.FastAPI.add_api_websocket_route`

**Сигнатура:** `def add_api_websocket_route(self, path: str, endpoint: Callable[..., Any], name: str | None = None, *, dependencies: Sequence[Depends] | None = None) -> None`

**Расположение:** `work/fastapi_app.py:1278-1291`

**Назначение:** Эта функция добавляет маршрут для обработки WebSocket-соединений к приложению FastAPI.

**Логика работы:** Функция принимает путь, конечную точку (функцию-обработчик WebSocket-соединения) и необязательное имя маршрута, а также зависимости. Она передает эти параметры объекту `self.router` для регистрации WebSocket-маршрута.

**Параметры:**

| Параметр | Тип | По умолчанию | Вид |
|---|---|---|---|
| `path` | `str` | обязательный | позиционный или именованный |
| `endpoint` | `Callable[..., Any]` | обязательный | позиционный или именованный |
| `name` | `str | None` | `None` | позиционный или именованный |
| `dependencies` | `Sequence[Depends] | None` | `None` | только именованный |

**Возвращаемое значение:** `None`

**Исключения:**

- явные исключения не обнаружены

**Пример использования:**

```python
obj = FastAPI()
result = obj.add_api_websocket_route('output.json', 'http://example.com', 'Alice', dependencies=None)
```

##### 2.3.1.7. Метод `websocket`

**Полное имя:** `fastapi_app.FastAPI.websocket`

**Сигнатура:** `def websocket(self, path: str, name: str | None = None, *, dependencies: Sequence[Depends] | None = None) -> Callable[[DecoratedCallable], DecoratedCallable]`

**Расположение:** `work/fastapi_app.py:1293-1356`

**Назначение:** Decorate a WebSocket function.

**Параметры:**

| Параметр | Тип | По умолчанию | Вид |
|---|---|---|---|
| `path` | `str` | обязательный | позиционный или именованный |
| `name` | `str | None` | `None` | позиционный или именованный |
| `dependencies` | `Sequence[Depends] | None` | `None` | только именованный |

**Возвращаемое значение:** `Callable[[DecoratedCallable], DecoratedCallable]`

**Исключения:**

- явные исключения не обнаружены

**Пример использования:**

```python
obj = FastAPI()
result = obj.websocket('output.json', 'Alice', dependencies=None)
```

##### 2.3.1.8. Метод `include_router`

**Полное имя:** `fastapi_app.FastAPI.include_router`

**Сигнатура:** `def include_router(self, router: routing.APIRouter, *, prefix: str = '', tags: list[str | Enum] | None = None, dependencies: Sequence[Depends] | None = None, responses: dict[int | str, dict[str, Any]] | None = None, deprecated: bool | None = None, include_in_schema: bool = True, default_response_class: type[Response] = Default(JSONResponse), callbacks: list[BaseRoute] | None = None, generate_unique_id_function: Callable[[routing.APIRoute], str] = Default(generate_unique_id)) -> None`

**Расположение:** `work/fastapi_app.py:1358-1561`

**Назначение:** Include an `APIRouter` in the same app.

**Параметры:**

| Параметр | Тип | По умолчанию | Вид |
|---|---|---|---|
| `router` | `routing.APIRouter` | обязательный | позиционный или именованный |
| `prefix` | `str` | `''` | только именованный |
| `tags` | `list[str | Enum] | None` | `None` | только именованный |
| `dependencies` | `Sequence[Depends] | None` | `None` | только именованный |
| `responses` | `dict[int | str, dict[str, Any]] | None` | `None` | только именованный |
| `deprecated` | `bool | None` | `None` | только именованный |
| `include_in_schema` | `bool` | `True` | только именованный |
| `default_response_class` | `type[Response]` | `Default(JSONResponse)` | только именованный |
| `callbacks` | `list[BaseRoute] | None` | `None` | только именованный |
| `generate_unique_id_function` | `Callable[[routing.APIRoute], str]` | `Default(generate_unique_id)` | только именованный |

**Возвращаемое значение:** `None`

**Исключения:**

- явные исключения не обнаружены

**Пример использования:**

```python
# router: создайте объект типа routing.APIRouter
obj = FastAPI()
result = obj.include_router(router, prefix='', tags=None, dependencies=None, responses=None, deprecated=None, include_in_schema=True, default_response_class=Default(JSONResponse), callbacks=None, generate_unique_id_function=Default(generate_unique_id))
```

##### 2.3.1.9. Метод `get`

**Полное имя:** `fastapi_app.FastAPI.get`

**Сигнатура:** `def get(self, path: str, *, response_model: Any = Default(None), status_code: int | None = None, tags: list[str | Enum] | None = None, dependencies: Sequence[Depends] | None = None, summary: str | None = None, description: str | None = None, response_description: str = 'Successful Response', responses: dict[int | str, dict[str, Any]] | None = None, deprecated: bool | None = None, operation_id: str | None = None, response_model_include: IncEx | None = None, response_model_exclude: IncEx | None = None, response_model_by_alias: bool = True, response_model_exclude_unset: bool = False, response_model_exclude_defaults: bool = False, response_model_exclude_none: bool = False, include_in_schema: bool = True, response_class: type[Response] = Default(JSONResponse), name: str | None = None, callbacks: list[BaseRoute] | None = None, openapi_extra: dict[str, Any] | None = None, generate_unique_id_function: Callable[[routing.APIRoute], str] = Default(generate_unique_id)) -> Callable[[DecoratedCallable], DecoratedCallable]`

**Расположение:** `work/fastapi_app.py:1563-1934`

**Назначение:** Add a *path operation* using an HTTP GET operation.

**Параметры:**

| Параметр | Тип | По умолчанию | Вид |
|---|---|---|---|
| `path` | `str` | обязательный | позиционный или именованный |
| `response_model` | `Any` | `Default(None)` | только именованный |
| `status_code` | `int | None` | `None` | только именованный |
| `tags` | `list[str | Enum] | None` | `None` | только именованный |
| `dependencies` | `Sequence[Depends] | None` | `None` | только именованный |
| `summary` | `str | None` | `None` | только именованный |
| `description` | `str | None` | `None` | только именованный |
| `response_description` | `str` | `'Successful Response'` | только именованный |
| `responses` | `dict[int | str, dict[str, Any]] | None` | `None` | только именованный |
| `deprecated` | `bool | None` | `None` | только именованный |
| `operation_id` | `str | None` | `None` | только именованный |
| `response_model_include` | `IncEx | None` | `None` | только именованный |
| `response_model_exclude` | `IncEx | None` | `None` | только именованный |
| `response_model_by_alias` | `bool` | `True` | только именованный |
| `response_model_exclude_unset` | `bool` | `False` | только именованный |
| `response_model_exclude_defaults` | `bool` | `False` | только именованный |
| `response_model_exclude_none` | `bool` | `False` | только именованный |
| `include_in_schema` | `bool` | `True` | только именованный |
| `response_class` | `type[Response]` | `Default(JSONResponse)` | только именованный |
| `name` | `str | None` | `None` | только именованный |
| `callbacks` | `list[BaseRoute] | None` | `None` | только именованный |
| `openapi_extra` | `dict[str, Any] | None` | `None` | только именованный |
| `generate_unique_id_function` | `Callable[[routing.APIRoute], str]` | `Default(generate_unique_id)` | только именованный |

**Возвращаемое значение:** `Callable[[DecoratedCallable], DecoratedCallable]`

**Исключения:**

- явные исключения не обнаружены

**Пример использования:**

```python
obj = FastAPI()
result = obj.get('output.json', response_model=Default(None), status_code=None, tags=None, dependencies=None, summary=None, description=None, response_description='Successful Response', responses=None, deprecated=None, operation_id=None, response_model_include=None, response_model_exclude=None, response_model_by_alias=True, response_model_exclude_unset=False, response_model_exclude_defaults=False, response_model_exclude_none=False, include_in_schema=True, response_class=Default(JSONResponse), name='Alice', callbacks=None, openapi_extra=None, generate_unique_id_function=Default(generate_unique_id))
```

##### 2.3.1.10. Метод `put`

**Полное имя:** `fastapi_app.FastAPI.put`

**Сигнатура:** `def put(self, path: str, *, response_model: Any = Default(None), status_code: int | None = None, tags: list[str | Enum] | None = None, dependencies: Sequence[Depends] | None = None, summary: str | None = None, description: str | None = None, response_description: str = 'Successful Response', responses: dict[int | str, dict[str, Any]] | None = None, deprecated: bool | None = None, operation_id: str | None = None, response_model_include: IncEx | None = None, response_model_exclude: IncEx | None = None, response_model_by_alias: bool = True, response_model_exclude_unset: bool = False, response_model_exclude_defaults: bool = False, response_model_exclude_none: bool = False, include_in_schema: bool = True, response_class: type[Response] = Default(JSONResponse), name: str | None = None, callbacks: list[BaseRoute] | None = None, openapi_extra: dict[str, Any] | None = None, generate_unique_id_function: Callable[[routing.APIRoute], str] = Default(generate_unique_id)) -> Callable[[DecoratedCallable], DecoratedCallable]`

**Расположение:** `work/fastapi_app.py:1936-2312`

**Назначение:** Add a *path operation* using an HTTP PUT operation.

**Параметры:**

| Параметр | Тип | По умолчанию | Вид |
|---|---|---|---|
| `path` | `str` | обязательный | позиционный или именованный |
| `response_model` | `Any` | `Default(None)` | только именованный |
| `status_code` | `int | None` | `None` | только именованный |
| `tags` | `list[str | Enum] | None` | `None` | только именованный |
| `dependencies` | `Sequence[Depends] | None` | `None` | только именованный |
| `summary` | `str | None` | `None` | только именованный |
| `description` | `str | None` | `None` | только именованный |
| `response_description` | `str` | `'Successful Response'` | только именованный |
| `responses` | `dict[int | str, dict[str, Any]] | None` | `None` | только именованный |
| `deprecated` | `bool | None` | `None` | только именованный |
| `operation_id` | `str | None` | `None` | только именованный |
| `response_model_include` | `IncEx | None` | `None` | только именованный |
| `response_model_exclude` | `IncEx | None` | `None` | только именованный |
| `response_model_by_alias` | `bool` | `True` | только именованный |
| `response_model_exclude_unset` | `bool` | `False` | только именованный |
| `response_model_exclude_defaults` | `bool` | `False` | только именованный |
| `response_model_exclude_none` | `bool` | `False` | только именованный |
| `include_in_schema` | `bool` | `True` | только именованный |
| `response_class` | `type[Response]` | `Default(JSONResponse)` | только именованный |
| `name` | `str | None` | `None` | только именованный |
| `callbacks` | `list[BaseRoute] | None` | `None` | только именованный |
| `openapi_extra` | `dict[str, Any] | None` | `None` | только именованный |
| `generate_unique_id_function` | `Callable[[routing.APIRoute], str]` | `Default(generate_unique_id)` | только именованный |

**Возвращаемое значение:** `Callable[[DecoratedCallable], DecoratedCallable]`

**Исключения:**

- явные исключения не обнаружены

**Пример использования:**

```python
obj = FastAPI()
result = obj.put('output.json', response_model=Default(None), status_code=None, tags=None, dependencies=None, summary=None, description=None, response_description='Successful Response', responses=None, deprecated=None, operation_id=None, response_model_include=None, response_model_exclude=None, response_model_by_alias=True, response_model_exclude_unset=False, response_model_exclude_defaults=False, response_model_exclude_none=False, include_in_schema=True, response_class=Default(JSONResponse), name='Alice', callbacks=None, openapi_extra=None, generate_unique_id_function=Default(generate_unique_id))
```

##### 2.3.1.11. Метод `post`

**Полное имя:** `fastapi_app.FastAPI.post`

**Сигнатура:** `def post(self, path: str, *, response_model: Any = Default(None), status_code: int | None = None, tags: list[str | Enum] | None = None, dependencies: Sequence[Depends] | None = None, summary: str | None = None, description: str | None = None, response_description: str = 'Successful Response', responses: dict[int | str, dict[str, Any]] | None = None, deprecated: bool | None = None, operation_id: str | None = None, response_model_include: IncEx | None = None, response_model_exclude: IncEx | None = None, response_model_by_alias: bool = True, response_model_exclude_unset: bool = False, response_model_exclude_defaults: bool = False, response_model_exclude_none: bool = False, include_in_schema: bool = True, response_class: type[Response] = Default(JSONResponse), name: str | None = None, callbacks: list[BaseRoute] | None = None, openapi_extra: dict[str, Any] | None = None, generate_unique_id_function: Callable[[routing.APIRoute], str] = Default(generate_unique_id)) -> Callable[[DecoratedCallable], DecoratedCallable]`

**Расположение:** `work/fastapi_app.py:2314-2690`

**Назначение:** Add a *path operation* using an HTTP POST operation.

**Параметры:**

| Параметр | Тип | По умолчанию | Вид |
|---|---|---|---|
| `path` | `str` | обязательный | позиционный или именованный |
| `response_model` | `Any` | `Default(None)` | только именованный |
| `status_code` | `int | None` | `None` | только именованный |
| `tags` | `list[str | Enum] | None` | `None` | только именованный |
| `dependencies` | `Sequence[Depends] | None` | `None` | только именованный |
| `summary` | `str | None` | `None` | только именованный |
| `description` | `str | None` | `None` | только именованный |
| `response_description` | `str` | `'Successful Response'` | только именованный |
| `responses` | `dict[int | str, dict[str, Any]] | None` | `None` | только именованный |
| `deprecated` | `bool | None` | `None` | только именованный |
| `operation_id` | `str | None` | `None` | только именованный |
| `response_model_include` | `IncEx | None` | `None` | только именованный |
| `response_model_exclude` | `IncEx | None` | `None` | только именованный |
| `response_model_by_alias` | `bool` | `True` | только именованный |
| `response_model_exclude_unset` | `bool` | `False` | только именованный |
| `response_model_exclude_defaults` | `bool` | `False` | только именованный |
| `response_model_exclude_none` | `bool` | `False` | только именованный |
| `include_in_schema` | `bool` | `True` | только именованный |
| `response_class` | `type[Response]` | `Default(JSONResponse)` | только именованный |
| `name` | `str | None` | `None` | только именованный |
| `callbacks` | `list[BaseRoute] | None` | `None` | только именованный |
| `openapi_extra` | `dict[str, Any] | None` | `None` | только именованный |
| `generate_unique_id_function` | `Callable[[routing.APIRoute], str]` | `Default(generate_unique_id)` | только именованный |

**Возвращаемое значение:** `Callable[[DecoratedCallable], DecoratedCallable]`

**Исключения:**

- явные исключения не обнаружены

**Пример использования:**

```python
obj = FastAPI()
result = obj.post('output.json', response_model=Default(None), status_code=None, tags=None, dependencies=None, summary=None, description=None, response_description='Successful Response', responses=None, deprecated=None, operation_id=None, response_model_include=None, response_model_exclude=None, response_model_by_alias=True, response_model_exclude_unset=False, response_model_exclude_defaults=False, response_model_exclude_none=False, include_in_schema=True, response_class=Default(JSONResponse), name='Alice', callbacks=None, openapi_extra=None, generate_unique_id_function=Default(generate_unique_id))
```

##### 2.3.1.12. Метод `delete`

**Полное имя:** `fastapi_app.FastAPI.delete`

**Сигнатура:** `def delete(self, path: str, *, response_model: Any = Default(None), status_code: int | None = None, tags: list[str | Enum] | None = None, dependencies: Sequence[Depends] | None = None, summary: str | None = None, description: str | None = None, response_description: str = 'Successful Response', responses: dict[int | str, dict[str, Any]] | None = None, deprecated: bool | None = None, operation_id: str | None = None, response_model_include: IncEx | None = None, response_model_exclude: IncEx | None = None, response_model_by_alias: bool = True, response_model_exclude_unset: bool = False, response_model_exclude_defaults: bool = False, response_model_exclude_none: bool = False, include_in_schema: bool = True, response_class: type[Response] = Default(JSONResponse), name: str | None = None, callbacks: list[BaseRoute] | None = None, openapi_extra: dict[str, Any] | None = None, generate_unique_id_function: Callable[[routing.APIRoute], str] = Default(generate_unique_id)) -> Callable[[DecoratedCallable], DecoratedCallable]`

**Расположение:** `work/fastapi_app.py:2692-3063`

**Назначение:** Add a *path operation* using an HTTP DELETE operation.

**Параметры:**

| Параметр | Тип | По умолчанию | Вид |
|---|---|---|---|
| `path` | `str` | обязательный | позиционный или именованный |
| `response_model` | `Any` | `Default(None)` | только именованный |
| `status_code` | `int | None` | `None` | только именованный |
| `tags` | `list[str | Enum] | None` | `None` | только именованный |
| `dependencies` | `Sequence[Depends] | None` | `None` | только именованный |
| `summary` | `str | None` | `None` | только именованный |
| `description` | `str | None` | `None` | только именованный |
| `response_description` | `str` | `'Successful Response'` | только именованный |
| `responses` | `dict[int | str, dict[str, Any]] | None` | `None` | только именованный |
| `deprecated` | `bool | None` | `None` | только именованный |
| `operation_id` | `str | None` | `None` | только именованный |
| `response_model_include` | `IncEx | None` | `None` | только именованный |
| `response_model_exclude` | `IncEx | None` | `None` | только именованный |
| `response_model_by_alias` | `bool` | `True` | только именованный |
| `response_model_exclude_unset` | `bool` | `False` | только именованный |
| `response_model_exclude_defaults` | `bool` | `False` | только именованный |
| `response_model_exclude_none` | `bool` | `False` | только именованный |
| `include_in_schema` | `bool` | `True` | только именованный |
| `response_class` | `type[Response]` | `Default(JSONResponse)` | только именованный |
| `name` | `str | None` | `None` | только именованный |
| `callbacks` | `list[BaseRoute] | None` | `None` | только именованный |
| `openapi_extra` | `dict[str, Any] | None` | `None` | только именованный |
| `generate_unique_id_function` | `Callable[[routing.APIRoute], str]` | `Default(generate_unique_id)` | только именованный |

**Возвращаемое значение:** `Callable[[DecoratedCallable], DecoratedCallable]`

**Исключения:**

- явные исключения не обнаружены

**Пример использования:**

```python
obj = FastAPI()
result = obj.delete('output.json', response_model=Default(None), status_code=None, tags=None, dependencies=None, summary=None, description=None, response_description='Successful Response', responses=None, deprecated=None, operation_id=None, response_model_include=None, response_model_exclude=None, response_model_by_alias=True, response_model_exclude_unset=False, response_model_exclude_defaults=False, response_model_exclude_none=False, include_in_schema=True, response_class=Default(JSONResponse), name='Alice', callbacks=None, openapi_extra=None, generate_unique_id_function=Default(generate_unique_id))
```

##### 2.3.1.13. Метод `options`

**Полное имя:** `fastapi_app.FastAPI.options`

**Сигнатура:** `def options(self, path: str, *, response_model: Any = Default(None), status_code: int | None = None, tags: list[str | Enum] | None = None, dependencies: Sequence[Depends] | None = None, summary: str | None = None, description: str | None = None, response_description: str = 'Successful Response', responses: dict[int | str, dict[str, Any]] | None = None, deprecated: bool | None = None, operation_id: str | None = None, response_model_include: IncEx | None = None, response_model_exclude: IncEx | None = None, response_model_by_alias: bool = True, response_model_exclude_unset: bool = False, response_model_exclude_defaults: bool = False, response_model_exclude_none: bool = False, include_in_schema: bool = True, response_class: type[Response] = Default(JSONResponse), name: str | None = None, callbacks: list[BaseRoute] | None = None, openapi_extra: dict[str, Any] | None = None, generate_unique_id_function: Callable[[routing.APIRoute], str] = Default(generate_unique_id)) -> Callable[[DecoratedCallable], DecoratedCallable]`

**Расположение:** `work/fastapi_app.py:3065-3436`

**Назначение:** Add a *path operation* using an HTTP OPTIONS operation.

**Параметры:**

| Параметр | Тип | По умолчанию | Вид |
|---|---|---|---|
| `path` | `str` | обязательный | позиционный или именованный |
| `response_model` | `Any` | `Default(None)` | только именованный |
| `status_code` | `int | None` | `None` | только именованный |
| `tags` | `list[str | Enum] | None` | `None` | только именованный |
| `dependencies` | `Sequence[Depends] | None` | `None` | только именованный |
| `summary` | `str | None` | `None` | только именованный |
| `description` | `str | None` | `None` | только именованный |
| `response_description` | `str` | `'Successful Response'` | только именованный |
| `responses` | `dict[int | str, dict[str, Any]] | None` | `None` | только именованный |
| `deprecated` | `bool | None` | `None` | только именованный |
| `operation_id` | `str | None` | `None` | только именованный |
| `response_model_include` | `IncEx | None` | `None` | только именованный |
| `response_model_exclude` | `IncEx | None` | `None` | только именованный |
| `response_model_by_alias` | `bool` | `True` | только именованный |
| `response_model_exclude_unset` | `bool` | `False` | только именованный |
| `response_model_exclude_defaults` | `bool` | `False` | только именованный |
| `response_model_exclude_none` | `bool` | `False` | только именованный |
| `include_in_schema` | `bool` | `True` | только именованный |
| `response_class` | `type[Response]` | `Default(JSONResponse)` | только именованный |
| `name` | `str | None` | `None` | только именованный |
| `callbacks` | `list[BaseRoute] | None` | `None` | только именованный |
| `openapi_extra` | `dict[str, Any] | None` | `None` | только именованный |
| `generate_unique_id_function` | `Callable[[routing.APIRoute], str]` | `Default(generate_unique_id)` | только именованный |

**Возвращаемое значение:** `Callable[[DecoratedCallable], DecoratedCallable]`

**Исключения:**

- явные исключения не обнаружены

**Пример использования:**

```python
obj = FastAPI()
result = obj.options('output.json', response_model=Default(None), status_code=None, tags=None, dependencies=None, summary=None, description=None, response_description='Successful Response', responses=None, deprecated=None, operation_id=None, response_model_include=None, response_model_exclude=None, response_model_by_alias=True, response_model_exclude_unset=False, response_model_exclude_defaults=False, response_model_exclude_none=False, include_in_schema=True, response_class=Default(JSONResponse), name='Alice', callbacks=None, openapi_extra=None, generate_unique_id_function=Default(generate_unique_id))
```

##### 2.3.1.14. Метод `head`

**Полное имя:** `fastapi_app.FastAPI.head`

**Сигнатура:** `def head(self, path: str, *, response_model: Any = Default(None), status_code: int | None = None, tags: list[str | Enum] | None = None, dependencies: Sequence[Depends] | None = None, summary: str | None = None, description: str | None = None, response_description: str = 'Successful Response', responses: dict[int | str, dict[str, Any]] | None = None, deprecated: bool | None = None, operation_id: str | None = None, response_model_include: IncEx | None = None, response_model_exclude: IncEx | None = None, response_model_by_alias: bool = True, response_model_exclude_unset: bool = False, response_model_exclude_defaults: bool = False, response_model_exclude_none: bool = False, include_in_schema: bool = True, response_class: type[Response] = Default(JSONResponse), name: str | None = None, callbacks: list[BaseRoute] | None = None, openapi_extra: dict[str, Any] | None = None, generate_unique_id_function: Callable[[routing.APIRoute], str] = Default(generate_unique_id)) -> Callable[[DecoratedCallable], DecoratedCallable]`

**Расположение:** `work/fastapi_app.py:3438-3809`

**Назначение:** Add a *path operation* using an HTTP HEAD operation.

**Параметры:**

| Параметр | Тип | По умолчанию | Вид |
|---|---|---|---|
| `path` | `str` | обязательный | позиционный или именованный |
| `response_model` | `Any` | `Default(None)` | только именованный |
| `status_code` | `int | None` | `None` | только именованный |
| `tags` | `list[str | Enum] | None` | `None` | только именованный |
| `dependencies` | `Sequence[Depends] | None` | `None` | только именованный |
| `summary` | `str | None` | `None` | только именованный |
| `description` | `str | None` | `None` | только именованный |
| `response_description` | `str` | `'Successful Response'` | только именованный |
| `responses` | `dict[int | str, dict[str, Any]] | None` | `None` | только именованный |
| `deprecated` | `bool | None` | `None` | только именованный |
| `operation_id` | `str | None` | `None` | только именованный |
| `response_model_include` | `IncEx | None` | `None` | только именованный |
| `response_model_exclude` | `IncEx | None` | `None` | только именованный |
| `response_model_by_alias` | `bool` | `True` | только именованный |
| `response_model_exclude_unset` | `bool` | `False` | только именованный |
| `response_model_exclude_defaults` | `bool` | `False` | только именованный |
| `response_model_exclude_none` | `bool` | `False` | только именованный |
| `include_in_schema` | `bool` | `True` | только именованный |
| `response_class` | `type[Response]` | `Default(JSONResponse)` | только именованный |
| `name` | `str | None` | `None` | только именованный |
| `callbacks` | `list[BaseRoute] | None` | `None` | только именованный |
| `openapi_extra` | `dict[str, Any] | None` | `None` | только именованный |
| `generate_unique_id_function` | `Callable[[routing.APIRoute], str]` | `Default(generate_unique_id)` | только именованный |

**Возвращаемое значение:** `Callable[[DecoratedCallable], DecoratedCallable]`

**Исключения:**

- явные исключения не обнаружены

**Пример использования:**

```python
obj = FastAPI()
result = obj.head('output.json', response_model=Default(None), status_code=None, tags=None, dependencies=None, summary=None, description=None, response_description='Successful Response', responses=None, deprecated=None, operation_id=None, response_model_include=None, response_model_exclude=None, response_model_by_alias=True, response_model_exclude_unset=False, response_model_exclude_defaults=False, response_model_exclude_none=False, include_in_schema=True, response_class=Default(JSONResponse), name='Alice', callbacks=None, openapi_extra=None, generate_unique_id_function=Default(generate_unique_id))
```

##### 2.3.1.15. Метод `patch`

**Полное имя:** `fastapi_app.FastAPI.patch`

**Сигнатура:** `def patch(self, path: str, *, response_model: Any = Default(None), status_code: int | None = None, tags: list[str | Enum] | None = None, dependencies: Sequence[Depends] | None = None, summary: str | None = None, description: str | None = None, response_description: str = 'Successful Response', responses: dict[int | str, dict[str, Any]] | None = None, deprecated: bool | None = None, operation_id: str | None = None, response_model_include: IncEx | None = None, response_model_exclude: IncEx | None = None, response_model_by_alias: bool = True, response_model_exclude_unset: bool = False, response_model_exclude_defaults: bool = False, response_model_exclude_none: bool = False, include_in_schema: bool = True, response_class: type[Response] = Default(JSONResponse), name: str | None = None, callbacks: list[BaseRoute] | None = None, openapi_extra: dict[str, Any] | None = None, generate_unique_id_function: Callable[[routing.APIRoute], str] = Default(generate_unique_id)) -> Callable[[DecoratedCallable], DecoratedCallable]`

**Расположение:** `work/fastapi_app.py:3811-4187`

**Назначение:** Add a *path operation* using an HTTP PATCH operation.

**Параметры:**

| Параметр | Тип | По умолчанию | Вид |
|---|---|---|---|
| `path` | `str` | обязательный | позиционный или именованный |
| `response_model` | `Any` | `Default(None)` | только именованный |
| `status_code` | `int | None` | `None` | только именованный |
| `tags` | `list[str | Enum] | None` | `None` | только именованный |
| `dependencies` | `Sequence[Depends] | None` | `None` | только именованный |
| `summary` | `str | None` | `None` | только именованный |
| `description` | `str | None` | `None` | только именованный |
| `response_description` | `str` | `'Successful Response'` | только именованный |
| `responses` | `dict[int | str, dict[str, Any]] | None` | `None` | только именованный |
| `deprecated` | `bool | None` | `None` | только именованный |
| `operation_id` | `str | None` | `None` | только именованный |
| `response_model_include` | `IncEx | None` | `None` | только именованный |
| `response_model_exclude` | `IncEx | None` | `None` | только именованный |
| `response_model_by_alias` | `bool` | `True` | только именованный |
| `response_model_exclude_unset` | `bool` | `False` | только именованный |
| `response_model_exclude_defaults` | `bool` | `False` | только именованный |
| `response_model_exclude_none` | `bool` | `False` | только именованный |
| `include_in_schema` | `bool` | `True` | только именованный |
| `response_class` | `type[Response]` | `Default(JSONResponse)` | только именованный |
| `name` | `str | None` | `None` | только именованный |
| `callbacks` | `list[BaseRoute] | None` | `None` | только именованный |
| `openapi_extra` | `dict[str, Any] | None` | `None` | только именованный |
| `generate_unique_id_function` | `Callable[[routing.APIRoute], str]` | `Default(generate_unique_id)` | только именованный |

**Возвращаемое значение:** `Callable[[DecoratedCallable], DecoratedCallable]`

**Исключения:**

- явные исключения не обнаружены

**Пример использования:**

```python
obj = FastAPI()
result = obj.patch('output.json', response_model=Default(None), status_code=None, tags=None, dependencies=None, summary=None, description=None, response_description='Successful Response', responses=None, deprecated=None, operation_id=None, response_model_include=None, response_model_exclude=None, response_model_by_alias=True, response_model_exclude_unset=False, response_model_exclude_defaults=False, response_model_exclude_none=False, include_in_schema=True, response_class=Default(JSONResponse), name='Alice', callbacks=None, openapi_extra=None, generate_unique_id_function=Default(generate_unique_id))
```

##### 2.3.1.16. Метод `trace`

**Полное имя:** `fastapi_app.FastAPI.trace`

**Сигнатура:** `def trace(self, path: str, *, response_model: Any = Default(None), status_code: int | None = None, tags: list[str | Enum] | None = None, dependencies: Sequence[Depends] | None = None, summary: str | None = None, description: str | None = None, response_description: str = 'Successful Response', responses: dict[int | str, dict[str, Any]] | None = None, deprecated: bool | None = None, operation_id: str | None = None, response_model_include: IncEx | None = None, response_model_exclude: IncEx | None = None, response_model_by_alias: bool = True, response_model_exclude_unset: bool = False, response_model_exclude_defaults: bool = False, response_model_exclude_none: bool = False, include_in_schema: bool = True, response_class: type[Response] = Default(JSONResponse), name: str | None = None, callbacks: list[BaseRoute] | None = None, openapi_extra: dict[str, Any] | None = None, generate_unique_id_function: Callable[[routing.APIRoute], str] = Default(generate_unique_id)) -> Callable[[DecoratedCallable], DecoratedCallable]`

**Расположение:** `work/fastapi_app.py:4189-4560`

**Назначение:** Add a *path operation* using an HTTP TRACE operation.

**Параметры:**

| Параметр | Тип | По умолчанию | Вид |
|---|---|---|---|
| `path` | `str` | обязательный | позиционный или именованный |
| `response_model` | `Any` | `Default(None)` | только именованный |
| `status_code` | `int | None` | `None` | только именованный |
| `tags` | `list[str | Enum] | None` | `None` | только именованный |
| `dependencies` | `Sequence[Depends] | None` | `None` | только именованный |
| `summary` | `str | None` | `None` | только именованный |
| `description` | `str | None` | `None` | только именованный |
| `response_description` | `str` | `'Successful Response'` | только именованный |
| `responses` | `dict[int | str, dict[str, Any]] | None` | `None` | только именованный |
| `deprecated` | `bool | None` | `None` | только именованный |
| `operation_id` | `str | None` | `None` | только именованный |
| `response_model_include` | `IncEx | None` | `None` | только именованный |
| `response_model_exclude` | `IncEx | None` | `None` | только именованный |
| `response_model_by_alias` | `bool` | `True` | только именованный |
| `response_model_exclude_unset` | `bool` | `False` | только именованный |
| `response_model_exclude_defaults` | `bool` | `False` | только именованный |
| `response_model_exclude_none` | `bool` | `False` | только именованный |
| `include_in_schema` | `bool` | `True` | только именованный |
| `response_class` | `type[Response]` | `Default(JSONResponse)` | только именованный |
| `name` | `str | None` | `None` | только именованный |
| `callbacks` | `list[BaseRoute] | None` | `None` | только именованный |
| `openapi_extra` | `dict[str, Any] | None` | `None` | только именованный |
| `generate_unique_id_function` | `Callable[[routing.APIRoute], str]` | `Default(generate_unique_id)` | только именованный |

**Возвращаемое значение:** `Callable[[DecoratedCallable], DecoratedCallable]`

**Исключения:**

- явные исключения не обнаружены

**Пример использования:**

```python
obj = FastAPI()
result = obj.trace('output.json', response_model=Default(None), status_code=None, tags=None, dependencies=None, summary=None, description=None, response_description='Successful Response', responses=None, deprecated=None, operation_id=None, response_model_include=None, response_model_exclude=None, response_model_by_alias=True, response_model_exclude_unset=False, response_model_exclude_defaults=False, response_model_exclude_none=False, include_in_schema=True, response_class=Default(JSONResponse), name='Alice', callbacks=None, openapi_extra=None, generate_unique_id_function=Default(generate_unique_id))
```

##### 2.3.1.17. Метод `websocket_route`

**Полное имя:** `fastapi_app.FastAPI.websocket_route`

**Сигнатура:** `def websocket_route(self, path: str, name: str | None = None) -> Callable[[DecoratedCallable], DecoratedCallable]`

**Расположение:** `work/fastapi_app.py:4562-4569`

**Назначение:** Эта функция служит декоратором для определения WebSocket-маршрутов в приложении FastAPI.

**Логика работы:** Функция принимает путь и необязательное имя для WebSocket-маршрута. Она возвращает декоратор, который при применении к функции-обработчику WebSocket регистрирует этот маршрут через `self.router.add_websocket_route`, передавая указанные путь и имя.

**Параметры:**

| Параметр | Тип | По умолчанию | Вид |
|---|---|---|---|
| `path` | `str` | обязательный | позиционный или именованный |
| `name` | `str | None` | `None` | позиционный или именованный |

**Возвращаемое значение:** `Callable[[DecoratedCallable], DecoratedCallable]`

**Исключения:**

- явные исключения не обнаружены

**Пример использования:**

```python
obj = FastAPI()
result = obj.websocket_route('output.json', 'Alice')
```

##### 2.3.1.18. Метод `on_event`

**Полное имя:** `fastapi_app.FastAPI.on_event`

**Сигнатура:** `def on_event(self, event_type: str) -> Callable[[DecoratedCallable], DecoratedCallable]`

**Расположение:** `work/fastapi_app.py:4579-4598`

**Назначение:** Add an event handler for the application.

`on_event` is Устарело, use `lifespan` event handlers instead.

Read more about it in the
[FastAPI docs for Lifespan Events](https://fastapi.tiangolo.com/advanced/events/#alternative-events-deprecated).

**Декораторы:** `deprecated('\n        on_event is deprecated, use lifespan event handlers instead.\n\n        Read more about it in the\n        [FastAPI docs for Lifespan Events](https://fastapi.tiangolo.com/advanced/events/).\n        ')`

**Параметры:**

| Параметр | Тип | По умолчанию | Вид |
|---|---|---|---|
| `event_type` | `str` | обязательный | позиционный или именованный |

**Возвращаемое значение:** `Callable[[DecoratedCallable], DecoratedCallable]`

**Исключения:**

- явные исключения не обнаружены

**Пример использования:**

```python
obj = FastAPI()
result = obj.on_event('example')
```

##### 2.3.1.19. Метод `middleware`

**Полное имя:** `fastapi_app.FastAPI.middleware`

**Сигнатура:** `def middleware(self, middleware_type: str) -> Callable[[DecoratedCallable], DecoratedCallable]`

**Расположение:** `work/fastapi_app.py:4600-4644`

**Назначение:** Add a middleware to the application.

**Параметры:**

| Параметр | Тип | По умолчанию | Вид |
|---|---|---|---|
| `middleware_type` | `str` | обязательный | позиционный или именованный |

**Возвращаемое значение:** `Callable[[DecoratedCallable], DecoratedCallable]`

**Исключения:**

- явные исключения не обнаружены

**Пример использования:**

```python
obj = FastAPI()
result = obj.middleware('example')
```

##### 2.3.1.20. Метод `exception_handler`

**Полное имя:** `fastapi_app.FastAPI.exception_handler`

**Сигнатура:** `def exception_handler(self, exc_class_or_status_code: int | type[Exception]) -> Callable[[DecoratedCallable], DecoratedCallable]`

**Расположение:** `work/fastapi_app.py:4646-4691`

**Назначение:** Add an exception handler to the app.

**Параметры:**

| Параметр | Тип | По умолчанию | Вид |
|---|---|---|---|
| `exc_class_or_status_code` | `int | type[Exception]` | обязательный | позиционный или именованный |

**Возвращаемое значение:** `Callable[[DecoratedCallable], DecoratedCallable]`

**Исключения:**

- явные исключения не обнаружены

**Пример использования:**

```python
obj = FastAPI()
result = obj.exception_handler(1)
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

### А.1 `fastapi_app.FastAPI.build_middleware_stack`

```python
obj = FastAPI()
result = obj.build_middleware_stack()
```

### А.2 `fastapi_app.FastAPI.openapi`

```python
obj = FastAPI()
result = obj.openapi()
```

### А.3 `fastapi_app.FastAPI.setup`

```python
obj = FastAPI()
result = obj.setup()
```

### А.4 `fastapi_app.FastAPI.add_api_route`

```python
obj = FastAPI()
result = obj.add_api_route('output.json', 'http://example.com', response_model=Default(None), status_code=None, tags=None, dependencies=None, summary=None, description=None, response_description='Successful Response', responses=None, deprecated=None, methods=None, operation_id=None, response_model_include=None, response_model_exclude=None, response_model_by_alias=True, response_model_exclude_unset=False, response_model_exclude_defaults=False, response_model_exclude_none=False, include_in_schema=True, response_class=Default(JSONResponse), name='Alice', openapi_extra=None, generate_unique_id_function=Default(generate_unique_id))
```

### А.5 `fastapi_app.FastAPI.api_route`

```python
obj = FastAPI()
result = obj.api_route('output.json', response_model=Default(None), status_code=None, tags=None, dependencies=None, summary=None, description=None, response_description='Successful Response', responses=None, deprecated=None, methods=None, operation_id=None, response_model_include=None, response_model_exclude=None, response_model_by_alias=True, response_model_exclude_unset=False, response_model_exclude_defaults=False, response_model_exclude_none=False, include_in_schema=True, response_class=Default(JSONResponse), name='Alice', openapi_extra=None, generate_unique_id_function=Default(generate_unique_id))
```

### А.6 `fastapi_app.FastAPI.add_api_websocket_route`

```python
obj = FastAPI()
result = obj.add_api_websocket_route('output.json', 'http://example.com', 'Alice', dependencies=None)
```

### А.7 `fastapi_app.FastAPI.websocket`

```python
obj = FastAPI()
result = obj.websocket('output.json', 'Alice', dependencies=None)
```

### А.8 `fastapi_app.FastAPI.include_router`

```python
# router: создайте объект типа routing.APIRouter
obj = FastAPI()
result = obj.include_router(router, prefix='', tags=None, dependencies=None, responses=None, deprecated=None, include_in_schema=True, default_response_class=Default(JSONResponse), callbacks=None, generate_unique_id_function=Default(generate_unique_id))
```

### А.9 `fastapi_app.FastAPI.get`

```python
obj = FastAPI()
result = obj.get('output.json', response_model=Default(None), status_code=None, tags=None, dependencies=None, summary=None, description=None, response_description='Successful Response', responses=None, deprecated=None, operation_id=None, response_model_include=None, response_model_exclude=None, response_model_by_alias=True, response_model_exclude_unset=False, response_model_exclude_defaults=False, response_model_exclude_none=False, include_in_schema=True, response_class=Default(JSONResponse), name='Alice', callbacks=None, openapi_extra=None, generate_unique_id_function=Default(generate_unique_id))
```

### А.10 `fastapi_app.FastAPI.put`

```python
obj = FastAPI()
result = obj.put('output.json', response_model=Default(None), status_code=None, tags=None, dependencies=None, summary=None, description=None, response_description='Successful Response', responses=None, deprecated=None, operation_id=None, response_model_include=None, response_model_exclude=None, response_model_by_alias=True, response_model_exclude_unset=False, response_model_exclude_defaults=False, response_model_exclude_none=False, include_in_schema=True, response_class=Default(JSONResponse), name='Alice', callbacks=None, openapi_extra=None, generate_unique_id_function=Default(generate_unique_id))
```

### А.11 `fastapi_app.FastAPI.post`

```python
obj = FastAPI()
result = obj.post('output.json', response_model=Default(None), status_code=None, tags=None, dependencies=None, summary=None, description=None, response_description='Successful Response', responses=None, deprecated=None, operation_id=None, response_model_include=None, response_model_exclude=None, response_model_by_alias=True, response_model_exclude_unset=False, response_model_exclude_defaults=False, response_model_exclude_none=False, include_in_schema=True, response_class=Default(JSONResponse), name='Alice', callbacks=None, openapi_extra=None, generate_unique_id_function=Default(generate_unique_id))
```

### А.12 `fastapi_app.FastAPI.delete`

```python
obj = FastAPI()
result = obj.delete('output.json', response_model=Default(None), status_code=None, tags=None, dependencies=None, summary=None, description=None, response_description='Successful Response', responses=None, deprecated=None, operation_id=None, response_model_include=None, response_model_exclude=None, response_model_by_alias=True, response_model_exclude_unset=False, response_model_exclude_defaults=False, response_model_exclude_none=False, include_in_schema=True, response_class=Default(JSONResponse), name='Alice', callbacks=None, openapi_extra=None, generate_unique_id_function=Default(generate_unique_id))
```

### А.13 `fastapi_app.FastAPI.options`

```python
obj = FastAPI()
result = obj.options('output.json', response_model=Default(None), status_code=None, tags=None, dependencies=None, summary=None, description=None, response_description='Successful Response', responses=None, deprecated=None, operation_id=None, response_model_include=None, response_model_exclude=None, response_model_by_alias=True, response_model_exclude_unset=False, response_model_exclude_defaults=False, response_model_exclude_none=False, include_in_schema=True, response_class=Default(JSONResponse), name='Alice', callbacks=None, openapi_extra=None, generate_unique_id_function=Default(generate_unique_id))
```

### А.14 `fastapi_app.FastAPI.head`

```python
obj = FastAPI()
result = obj.head('output.json', response_model=Default(None), status_code=None, tags=None, dependencies=None, summary=None, description=None, response_description='Successful Response', responses=None, deprecated=None, operation_id=None, response_model_include=None, response_model_exclude=None, response_model_by_alias=True, response_model_exclude_unset=False, response_model_exclude_defaults=False, response_model_exclude_none=False, include_in_schema=True, response_class=Default(JSONResponse), name='Alice', callbacks=None, openapi_extra=None, generate_unique_id_function=Default(generate_unique_id))
```

### А.15 `fastapi_app.FastAPI.patch`

```python
obj = FastAPI()
result = obj.patch('output.json', response_model=Default(None), status_code=None, tags=None, dependencies=None, summary=None, description=None, response_description='Successful Response', responses=None, deprecated=None, operation_id=None, response_model_include=None, response_model_exclude=None, response_model_by_alias=True, response_model_exclude_unset=False, response_model_exclude_defaults=False, response_model_exclude_none=False, include_in_schema=True, response_class=Default(JSONResponse), name='Alice', callbacks=None, openapi_extra=None, generate_unique_id_function=Default(generate_unique_id))
```

### А.16 `fastapi_app.FastAPI.trace`

```python
obj = FastAPI()
result = obj.trace('output.json', response_model=Default(None), status_code=None, tags=None, dependencies=None, summary=None, description=None, response_description='Successful Response', responses=None, deprecated=None, operation_id=None, response_model_include=None, response_model_exclude=None, response_model_by_alias=True, response_model_exclude_unset=False, response_model_exclude_defaults=False, response_model_exclude_none=False, include_in_schema=True, response_class=Default(JSONResponse), name='Alice', callbacks=None, openapi_extra=None, generate_unique_id_function=Default(generate_unique_id))
```

### А.17 `fastapi_app.FastAPI.websocket_route`

```python
obj = FastAPI()
result = obj.websocket_route('output.json', 'Alice')
```

### А.18 `fastapi_app.FastAPI.on_event`

```python
obj = FastAPI()
result = obj.on_event('example')
```

### А.19 `fastapi_app.FastAPI.middleware`

```python
obj = FastAPI()
result = obj.middleware('example')
```

### А.20 `fastapi_app.FastAPI.exception_handler`

```python
obj = FastAPI()
result = obj.exception_handler(1)
```