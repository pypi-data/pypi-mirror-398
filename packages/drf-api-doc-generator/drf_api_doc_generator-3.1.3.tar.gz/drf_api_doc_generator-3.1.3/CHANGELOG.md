# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.1.3] - 2025-12-25

### Fixed
- **Nested JSON Support in Docstrings**: Improved the docstring parser to handle nested JSON objects (e.g. `Body: { "data": [ { "id": 1 } ] }`). Previously, nested braces confused the parser. Now it reads the entire block greedily to ensure all fields are captured.

## [3.1.2] - 2025-12-25

### Changed
- **Magic Command Update**: Experience of `complete-project-zip-html` updated to generate all formats (HTML, PDF, JSON) by default, ensuring you get the full package.

## [3.1.1] - 2025-12-25

### Fixed
- **Import Error**: Fixed `NameError: name 'Tuple' is not defined` by adding `Tuple` to imports in `parser.py`. This was causing the docstring parser to fail.

## [3.1.0] - 2025-12-25

### Added
- **Docstring Parameter Parsing**: Major feature! Now parses View docstrings for parameter definitions. If you document your API in the docstring (e.g. `Body: { "phone": "..." }`), the tool will automatically extract these fields and put them in the generated documentation. This is perfect for views with complex logic where serializers are not explicit.

## [3.0.9] - 2025-12-25

### Fixed
- **Manual Response Discovery**: Added support for discovering Response fields in views that don't use serializers. The tool scans the source code for dictionary key usage (e.g. `"contact_id": value`) and adds them to the documentation. This helps document views that return manual dictionaries.

## [3.0.8] - 2025-12-25

### Fixed
- **API Parsing Logic**: Improved Regex for Manual Parameter Discovery (scanning `request.data.get('param')`). Now handles spaces and newlines correctly.
- **Debugging**: Added verbose console logging (`[INFO] Auto-detected...`) during documentation generation to help potential issues with parameter discovery.

## [3.0.7] - 2025-12-25

### Fixed
- **API Parser (No-Serializer Views)**: Added fallback support for views that do not use serializers at all (e.g. `APIView` accessing `request.data`). The tool now scans the source code for manual parameter access like `request.data.get('param')` or `request.data['param']` and adds them to the documentation.

## [3.0.6] - 2025-12-25

### Fixed
- **Advanced Source Code Inspection**: Added a "Sherlock Holmes" feature to `APIParser`. It now scans the python source code of view methods (like `post`, `create`) to find usages of Serializers (e.g. `UserSignupSerializer(data=...)`). This fixes the issue where views inheriting from `APIView` (instead of `GenericAPIView`) with no `serializer_class` attribute were missing their parameters in the documentation.

## [3.0.5] - 2025-12-25

### Fixed
- **Robust Serializer Detection**: Implemented aggressive instantiation of Views to call `get_serializer_class()` with mock requests. This allows the parser to discover serializers in dynamic views (like `dj-rest-auth`) which were previously showing up with missing fields.

## [3.0.4] - 2025-12-25

### Fixed
- **API Parser**: Improved serializer detection logic to better handle views where `serializer_class` is dynamically set or is missing from Class attributes.
- Attempts to instantiate the view safely to uncover hidden `serializer_class` attributes.
- Checks for `input_serializer_class` and `request_serializer_class` as fallbacks.

## [3.0.3] - 2025-12-25

### Fixed
- **Critical**: Fix WebSocket discovery to support singular filename `consumer.py` (previously only `consumers.py` was strictly checked).
- Relaxed file matching to find any file containing "consumer" in its name.

## [3.0.2] - 2025-12-25

### Fixed
- **WebSocket Auto-Discovery**: Significantly improved the discovery logic to find `consumers.py` and files like `*consumers.py` in subdirectories. This fixes the issue where sockets were not detected by the magic command.
- recursive search logic added to `_discover_consumer_files`

## [3.0.1] - 2025-12-25

### Fixed
- Corrected proper installed app name in `README.md` documentation (`api_docs_generator` instead of `drf_api_doc_generator`)
- Updated installation instructions to prevent `ModuleNotFoundError`

## [3.0.0] - 2025-12-25

### 🚀 Major Features

#### Magic Command (`complete-project-zip-html`)
- Introduced a powerful new command to automate the entire documentation process in one step:
  ```bash
  python manage.py generate_api_docs complete-project-zip-html
  ```
- **Auto-Discovery**: Automatically finds all installed Django Apps (REST APIs)
- **WebSocket Detection**: Automatically searches for and parses all `consumers.py` files in every app
- **One-Click Export**: Generates HTML documentation and immediately packages it into a ZIP file
- **Zero Configuration**: No need to manually specify app names or file paths anymore

### Added
- Auto-discovery logic for `consumers.py` files across the entire project
- New `commands.txt` file with Malayalam instructions for easy usage
- Helper method `_discover_consumer_files` in management command

### Changed
- Improved CLI experience with "Magic Command" shortcut
- Updated project to Version 3.0.0

---

## [2.0.0] - 2025-12-25

### 🚀 Major New Features

#### WebSocket Documentation Support
- **New WebSocket Parser**: Automatically parses Django Channels consumers
- **Action Handlers**: Documents all `handle_*` methods as client-to-server actions
- **Server Events**: Documents broadcast events (`chat_message`, `user_typing`, etc.)
- **Connection Lifecycle**: Full documentation of connect/disconnect flow with error codes
- **Auto-generated Examples**: Creates example JSON for requests and responses
- **Smart URL Detection**: Automatically generates WebSocket URLs from consumer class names

#### ZIP Package Export
- **New `--zip` option**: Creates a shareable ZIP package containing all documentation
- **README included**: Auto-generated instructions for frontend developers
- **Offline-ready**: HTML works without any server

#### Improved PDF Design
- **Clean, Modern Layout**: Matches professional API documentation standards
- **Syntax Highlighting**: JSON and JavaScript code blocks with proper colors
- **Better Typography**: Improved fonts and spacing for readability
- **Code Boxes**: Styled code blocks with language labels

#### Improved HTML Design
- **Light Theme**: Clean white background with professional styling
- **Sidebar Navigation**: Quick access to all endpoints
- **Method Badges**: Color-coded badges for HTTP methods and WebSocket
- **Responsive Design**: Works on mobile devices

### Added
- `--websocket` / `-ws` option to specify consumer files
- `--zip` option to create shareable documentation package
- `--ws-base-url` option to set WebSocket base URL
- `WebSocketParser` class for parsing Django Channels consumers
- `WebSocketAction`, `WebSocketEndpoint`, `WebSocketAppInfo` dataclasses
- Support for multiple consumers in a single file
- Auto-detection of consumer classes by name pattern

### Changed
- PDF generator completely redesigned with clean layout
- HTML generator updated to support WebSocket documentation
- Default description updated to include WebSocket
- Version bumped to 2.0.0

### Fixed
- Duplicate action detection in WebSocket parser
- Unicode encoding issues on Windows console
- Style naming conflicts in PDF generator

---

## [1.0.0] - 2025-12-06

### Initial Release

#### Features
- Auto-discovery of DRF API endpoints
- PDF documentation with cover page and table of contents
- Interactive HTML documentation with sidebar navigation
- OpenAPI 3.0 JSON specification generation
- Serializer field extraction (types, validations, help text)
- Authentication and permission detection
- Query parameter documentation from filter backends
- Custom styling with theme colors
- Command line options for customization

---

## Links

- [PyPI Package](https://pypi.org/project/drf-api-doc-generator/)
- [GitHub Repository](https://github.com/yourusername/drf-api-doc-generator)
- [Documentation](https://github.com/yourusername/drf-api-doc-generator#readme)
