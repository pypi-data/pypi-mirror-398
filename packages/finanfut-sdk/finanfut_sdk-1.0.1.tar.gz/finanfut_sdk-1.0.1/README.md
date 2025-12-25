# FinanFut Intelligence Python SDK

Official Python SDK for **FinanFut Intelligence**, a modular AI platform for agents, memory and orchestration.

This package provides a high-level client to interact with FinanFut Intelligence:
- Unified `interact` API for chat and actions
- Application and agent management
- Memory (settings + records)
- Contexts (documents & sessions)
- Billing & usage
- Async requests and developer analytics
- Optional CLI tool: `finanfut`

---

## Installation

```bash
pip install finanfut-sdk
```

Requires **Python >= 3.12**.

---

## Quickstart

```python
from finanfut_sdk import FinanFutClient

client = FinanFutClient(
    api_key="YOUR_API_KEY",
    application_id="YOUR_APPLICATION_ID",
)

response = client.interact.query("Hello! Schedule a meeting tomorrow at 10.")
print(response.answer)
```

---

## Configuration (optional)

### Local config file

```bash
mkdir -p ~/.finanfut
```

Create `~/.finanfut/config.json`:

```json
{
  "api_key": "YOUR_API_KEY",
  "application_id": "YOUR_APPLICATION_ID",
  "api_url": "https://finanfut-intelligence.onrender.com"
}
```

Then:

```python
client = FinanFutClient()  # reads from config/env
```

### Environment variables supported

- `FINANFUT_API_KEY`
- `FINANFUT_APPLICATION_ID`
- `FINANFUT_API_URL`

`FINANFUT_API_URL` accepts either the bare host or a URL that already
includes `/api` or `/api/v1`; the SDK normalitza l'adreça perquè no s'hi
afegeixin segments duplicats.

---

## Using agents and intents

```python
# List agents
agents = client.agents.list()

for agent in agents:
    print(agent.name, agent.ai_model_id or "default model")

# Use a specific application agent and intent
response = client.interact.query(
    query="Add an event to my calendar.",
    application_agent_id="UUID_OF_APPLICATION_AGENT",
    intent_id="UUID_OF_INTENT",
)
print(response.answer)
```

`ai_model_id` reflects the catalog entry resolved by the backend and should be
used whenever you need to persist or audit the concrete model tied to an
agent.

---

## Memory API

```python
settings = client.memory.settings.get(application_id="APP_UUID")

records = client.memory.records.query(
    application_id="APP_UUID",
    application_agent_id="AGENT_UUID",
    query="What was the last scheduled event?"
)
```

---

## Billing & usage

```python
usage = client.billing.get_usage()
print("Total tokens used:", usage.tokens_used)
```

---

## CLI usage

```bash
finanfut init
finanfut interact "Hi!"
finanfut usage
```

---

## Document QA uploads

Use `client.documents.upload` to ingest files or free text for the document QA
agent. You can optionally set `document_type` to bypass automatic
classification and force the backend to tag the file with a known type such as
`context_general`, `examples_set`, `action_definition`, or `schema_contract`.

```python
from pathlib import Path
from finanfut_sdk import FinanFutClient

client = FinanFutClient(api_key="YOUR_API_KEY", application_id="APP_ID")

# Upload a PDF as contextual knowledge
detail = client.documents.upload(
    file_path=Path("knowledge.pdf"),
    document_type="context_general",
)
print(detail.document_type, detail.document_type_label)

# Upload pasted text with a strict contract type
schema_doc = client.documents.upload(
    text="{\"name\": \"Ada\", \"role\": \"engineer\"}",
    file_name="profile.json",
    mime_type="application/json",
    document_type="schema_contract",
)
print(schema_doc.document_type_version)

# Override classification for a curated examples set
client.documents.upload(
    content="Example A -> Response A", file_name="examples.md", document_type="examples_set"
)
```

---

## Ingesta de CSV a contractes JSON

L'SDK incorpora utilitats per replicar el flux del *playground* de
`data_transformer_agent`: carregar un CSV efímer, previsualitzar-lo i transformar-lo
segons un contracte JSON existent.

```python
from finanfut_sdk import FinanFutClient

client = FinanFutClient(api_key="YOUR_API_KEY", application_id="APP_ID")

# 1) Pujar el CSV de forma efímera i obtenir previsualització
preview = client.data_import.upload_transient_csv(file_path="ingesta.csv")
print("Cols", preview.preview.columns)
print("Rows", preview.preview.row_count)

# 2) Executar l'intent transform_data amb el contracte desitjat
result = client.data_import.transform_data(
    application_id=client.application_id,
    intent_id="UUID_INTENT_TRANSFORM_DATA",
    transient_csv=preview,
    contract_document_id="UUID_DATA_IMPORT_CONTRACT",
)
print("Primer registre", result.items[0] if result.items else result.response)
```

El client elimina automàticament `content_base64` i retalla la mostra de files
(`rows_sample`) abans d'enviar la petició a `/api/v1/public/requests`, tal i com
espera l'orquestrador. També pots passar `contract_name` (nom del contracte)
en comptes de `contract_document_id` si el teu agent el resol pel nom.

---

## License

This project is licensed under the MIT License.
