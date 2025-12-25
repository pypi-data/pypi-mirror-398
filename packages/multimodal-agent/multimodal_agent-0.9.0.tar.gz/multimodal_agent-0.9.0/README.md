# **Multimodal-Agent**

*A lightweight, production-ready multimodal wrapper for Google Gemini with RAG, image input, JSON mode, project learning, session memory, and a clean CLI & server.*


If you are using the **free tier**, you may encounter temporary errors such as:

- `429 RESOURCE_EXHAUSTED`
- `Quota exceeded`
- Requests failing after several generations

This is **expected behavior** and **not a bug** in Multimodal Agent.

---

## Features

### **Core LLM Capabilities**

* Flutter code generation (widgets, screens, models)
* Unified agent for **text, image, and chat** interactions
* Clean  **CLI** : `agent ask`, `agent image`, `agent chat`, `agent history`, `agent learn-project`
* Supports  **Gemini 2.5-flash** ,  **1.5-flash** , and any future model (configurable)
* Automatic **retry logic with exponential backoff**
* Full offline mode support (`FAKE_RESPONSE`) when no API key is available
* Detailed  **usage logging** : prompt, response, and total token counts

### **RAG + Memory**

* Local SQLite **RAGStore** (no cloud dependency)
* Automatic memory saving of past chats
* Project learning: let the agent read source code & architecture
* Project introspection commands: `learn-project`, `show-project`, `inspect-project`

### **Configuration System**

* User config stored at: `~/.multimodal_agent/config.yaml`
* Configure models individually:
  * `chat_model`
  * `image_model`
  * `embedding_model`
* New CLI commands:
  * `agent config set-model <model>`
  * `agent config set-image-model <model>`
  * `agent config set-embed-model <model>`
  * `agent config set-key <API_KEY>`

### **Developer Experience**

* pytest fixtures for offline/fake mode
* High test coverage rate
* Type-safe `AgentResponse`
* Extensible architecture
* Easy to embed into apps or scripts

---

## Installation

### Install with pip
```bash
pip install multimodal-agent
```

Or local:

```bash
git clone https://github.com/horam/multimodal-agent.git
cd multimodal-agent
pip install -e .
```

---

# Configuration
Multimodal Agent uses a **single source of truth** for model selection via
`~/.multimodal_agent/config.yaml`.

### Show current configuration:
```bash
agent config show
```

### Set API key:

```bash
agent config set-key YOUR_KEY
```

### Set chat model:

```bash
agent config set-model gemini-2.5-flash
```

### Set image model:

```bash
agent config set-image-model gemini-1.5-flash
```

### Set embedding model:

```bash
agent config set-embed-model text-embedding-004
```

Your config file after updates:

```bash
local_learning: true
chat_model: gemini-2.5-flash
image_model: gemini-2.0-flash
embedding_model: text-embedding-004
api_key: YOUR_KEY
```

### Default configuration

```yaml
chat_model: gemini-2.0-flash
image_model: gemini-2.0-flash
embedding_model: text-embedding-004
```
⚠️ Older models such as gemini-1.5-pro are no longer supported by the Gemini API and will cause 404 NOT_FOUND errors.

Always ensure your configured models exist in:

https://ai.google.dev/gemini-api/docs/models

---


## CLI vs Server vs VS Code Extension

Multimodal Agent has **three execution paths**:

### 1. CLI (`agent chat`, `agent ask`)
- Talks **directly** to Gemini
- May continue working even if the server is failing
- Best for debugging and verification

### 2. HTTP Server (`agent server`)
- Acts as a bridge for the VS Code extension
- Enforces request timeouts
- Returns HTTP errors (400 / 429 / 500)

### 3. VS Code Extension
- Depends on the HTTP server
- Will show errors like:

---
## Quick Start

### **Text Question**

```bash
agent ask "What is the capital of France?"
```

### **Disable RAG**

```bash
agent ask "What is the capital of France?" --no-rag
```

### **JSON mode**

```bash
agent ask "give me json" --json
```

### **Image + Text**

```bash
agent image test.jpg "describe this"
```

### **Chat (with persistent memory)**

```bash
agent chat
```
---

### History / Memory

Your memory DB lives at:

```bash
~/.multimodal_agent/memory.db
```

Show memory:

```bash
agent history show
```

Clear memory:

```bash
agent history clear
```

Summarize memory:

```bash
agent history summary
```

---

## Learning a Project

Let the agent scan and store a project summary:

```bash
agent learn-project my_app/
```

List learned projects:

```bash
agent list-projects
```

Show a specific project:

```bash
agent show-project project:my_app
```

Inspect project without saving:

```bash
agent inspect-project my_app/
```

---

## VS Code Extension (Pre-Release)

Until v1.0.0, the VS Code extension is available via manual install.

### Install from source

```bash
git clone https://github.com/horam/multimodal-agent.git
cd multimodal-agent/vscode-extension
npm install
npm run build
code --install-extension multimodal-agent-*.vsix
```

### Python API Example

```python
from multimodal_agent.core.agent_core import MultiModalAgent

agent = MultiModalAgent()

resp = agent.ask("Explain quantum computing")
print(resp.text)
print(resp.usage)

```

Image example:

```python
from multimodal_agent.utils import load_image_as_part

img = load_image_as_part("cat.jpg")
resp = agent.ask_with_image("describe this", img)
print(resp.text)
```

---

### Server Mode

Start:

```bash
agent server
```

Runs at:

```
http://127.0.0.1:8000
```

## API Reference (v0.6.0)

## **POST /ask**

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"prompt": "hello"}'
```

Response:

```json
{
  "text": "hello",
  "data": null,
  "usage": { "prompt_tokens": 44, "response_tokens": 3, "total_tokens": 553 }
}
```

## **POST /ask_with_image**

```bash
curl -X POST http://127.0.0.1:8000/ask_with_image \
  -F "file=@test.jpg" \
  -F "prompt=describe this"
```

### v0.6.0 Better Error Handling

Failures now return:

```json
{
  "text": "Image processing failed: 429 RESOURCE_EXHAUSTED ...",
  "data": null,
  "usage": {},
  "error": true
}
```

Never returns `text: null`.

---

## **POST /generate**

```bash
curl -X POST http://127.0.0.1:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "give me json", "json": true}'
```

---

## **POST /memory/search**

```bash
curl -X POST http://127.0.0.1:8000/memory/search \
  -H "Content-Type: application/json" \
  -d '{"query": "hello"}'
```

Response:

```json
{
  "results": [
    [0.98, { "id": 1, "content": "hello", "role": "user" }]
  ]
}
```

---

## **POST /learn/project**

Returns a structured project profile:

```json
{
  "status": "ok",
  "project_id": "project:rope_simulation_using_flutter",
  "profile": {
    "package_name": "rope_simulation_using_flutter",
    "architecture": {
      "patterns": ["feature_first"],
      "state_management": []
    },
    "dart_files_count": 3,
    "widget_files_count": 2
  }
}
```

---

## Architecture Overview

```bash
multimodal_agent/
    core/          # Main agent logic
    rag/           # SQLite vector store
    cli/           # CLI commands (`agent`)
    server/        # FastAPI server implementation
    utils/         # helpers
```

### Memory schema:

```bash
sessions      # chat sessions
chunks        # tokenized fragments
embeddings    # vector embeddings
projects      # project profiles (v0.6.0)
```

---

### Flutter Code Generation (v0.8.0)
The agent can generate fully functional Flutter files directly inside your project.

You must run commands from within a Flutter project (containing `pubspec.yaml`).

Generated files are written to:

```bash
lib/widgets/
lib/screens/
lib/models/
```

### Generate a Flutter Widget
**Stateless widget**
```bash
agent gen widget HomeCard
```
**Stateful widget**
```bash
agent gen widget CoolCounter --stateful
```
**Example output**
```dart
import 'package:flutter/material.dart';

class CoolCounter extends StatefulWidget {
  const CoolCounter({super.key});

  @override
  State<CoolCounter> createState() => _CoolCounterState();
}

class _CoolCounterState extends State<CoolCounter> {
  int _counter = 0;

  void _incrementCounter() {
    setState(() => _counter++);
  }

  @override
  Widget build(BuildContext context) {
    return Text('$_counter');
  }
}
```
## Generate a Screen
```bash
agent gen screen SettingsScreen
```
Every screen is a `StatelessWidget` with:

- Scaffold
- AppBar
- Centered placeholder body

## Generate a Dart Model
```bash
agent gen model UserProfile
```
Generated model includes:

- final fields
- const constructor
- copyWith
- fromJson / toJson
- toString

**Example**
```dart
class UserProfile {
  final String name;
  final int age;

  const UserProfile({required this.name, required this.age});

  UserProfile copyWith({String? name, int? age}) =>
      UserProfile(name: name ?? this.name, age: age ?? this.age);

  factory UserProfile.fromJson(Map<String, dynamic> json) =>
      UserProfile(name: json['name'], age: json['age']);

  Map<String, dynamic> toJson() => {'name': name, 'age': age};
}
```
## Naming Rules (Class + File Names)
**sanitize_class_name()**

Input → Class Name

| Input |	Output |
|--------|----------|
| my widget |	MyWidget |
| my-widget	| MyWidget |
| my_widget	| MyWidget |
| 123widget	| W123widget |
| my@bad#name	| MyBadName |

**to_snake_case()**
Input → snake_case

|Input  |	Output  |
|-------|----------|
|MyWidget |	my_widget |
|MyWidgetScreen |	my_widget_screen  |
|my widget  |	my_widget |
|my@invalid-name  |	myinvalid_name  |


**Offline Mode (No API Key)**

If no API key is configured:

### **Text mode**
```javascript
FAKE_RESPONSE: <your prompt>
```
### **JSON mode**
```javascript
text contains JSON string
```

data is None (tests enforce this)

Example:

```json
{"message": "hello"}
```

This is intended for CI and local testing.

## Config
Show config:

```bash
agent config show
```
Set models:

```bash
agent config set-model gemini-2.5-flash
agent config set-image-model gemini-vision
agent config set-embed-model gemini-embed
```
## **Formatting Engine (v0.4.0+)**

* Detects JSON, XML, HTML, code, python, kotlin, dart, js, swift …
* Pretty-prints output
* Auto-wraps in fenced code blocks
* Optional in `agent.ask(formatted=True)`

---

## Running Tests

```bash
make test
make coverage
```

This includes:

* RAG tests
* CLI tests
* JSON mode tests
* Fake mode (offline)
* Config isolation
* SQLite operations
* Code generation


## Troubleshooting

### Error: `429 RESOURCE_EXHAUSTED`

Cause:
- Gemini API free-tier quota exceeded

Solution:
- Wait for quota reset (usually within 24 hours)
- Or upgrade your Gemini API plan

---

### Error: `404 NOT_FOUND (model)`

Cause:
- Using a deprecated or unsupported Gemini model

Solution:
- Update `chat_model` in `config.yaml`
- Restart the agent server

---

### CLI works but VS Code extension fails

Cause:
- Server timeout or quota exhaustion

Solution:
- Check server logs
- Prefer CLI while quota resets


## Roadmap

- Local LLM mode

- Plugin architecture for custom code generators

- Automatic quota detection

- Model failover (Flash → Flash Lite → Local)

- Graceful server fallback when quota is exhausted

- Extension-side retry & clearer diagnostics

# License

MIT License.

If you enjoy this project, ⭐ star the repo!
