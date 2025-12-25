# Questra Python Client

**Der offizielle Python Client für die Questra Platform** – vereinfachter Zugriff auf benutzerdefinierte Datenmodelle, Zeitreihen und Automatisierungen.

## Motivation

Die Questra Platform bietet flexible GraphQL- und REST-APIs für Dynamic Objects, TimeSeries und Automatisierungen. Dieses Package bündelt alle spezialisierten Client-Libraries, damit Sie mit einer einzigen Installation sofort produktiv arbeiten können:

- **Schnelle Integration**: Eine Installation, alle APIs verfügbar
- **Typsichere Entwicklung**: Vollständige Type Hints für IDE-Unterstützung
- **High-Level API**: Intuitive Schnittstellen für häufige Operationen
- **Produktionsbereit**: OAuth2-Authentifizierung, Error Handling, Logging

## Installation

```bash
# Standard-Installation
pip install seven2one-questra

# Mit pandas-Unterstützung (empfohlen für Data Science)
pip install seven2one-questra[pandas]
```

Dies installiert automatisch alle Questra-Client-Libraries:

- **[seven2one-questra-authentication](https://pypi.org/project/seven2one-questra-authentication/)** – OAuth2-Authentifizierung
- **[seven2one-questra-data](https://pypi.org/project/seven2one-questra-data/)** – Datenmodell & Datenzugiffe
- **[seven2one-questra-automation](https://pypi.org/project/seven2one-questra-automation/)** – Workflow-Automatisierung

## Schnellstart

### 1. Authentifizierung einrichten

```python
from seven2one.questra.authentication import QuestraAuthentication

auth = QuestraAuthentication(
    url="https://auth.ihr-questra-server.de",
    username="ServiceUser",
    password="IhrPasswort"
)
```

### 2. Daten verwalten

```python
from seven2one.questra.data import QuestraData

# Client initialisieren
client = QuestraData(
    graphql_url="https://ihr-questra-server/data/graphql/",
    auth_client=auth
)

# Inventory Items auflisten
items = client.list_items(
    inventory_name="Stromzaehler",
    namespace_name="Energie",
    properties=["_id", "standort", "seriennummer"]
)

# Neues Item erstellen
new_items = client.create_items(
    inventory_name="Stromzaehler",
    namespace_name="Energie",
    items=[{"standort": "Gebäude A", "seriennummer": "SN-12345"}]
)
```

### 3. Zeitreihen-Daten abrufen

```python
from datetime import datetime

# TimeSeries-Werte laden
result = client.list_timeseries_values(
    inventory_name="Stromzaehler",
    namespace_name="Energie",
    timeseries_properties="messwerte_Verbrauch",
    from_time=datetime(2024, 1, 1),
    to_time=datetime(2024, 1, 31)
)

# Optional: Als pandas DataFrame konvertieren
df = result.to_df()  # Requires pandas installation
```

### 4. Automatisierungen verwalten

```python
from seven2one.questra.automation import QuestraAutomation

# Automation Client initialisieren
automation_client = QuestraAutomation(
    graphql_url="https://api.ihr-questra-server.de/automation/graphql",
    auth_client=auth
)

# Workflows auflisten
workflows = automation_client.list_workflows()
```

## Enthaltene Packages

Dieses Umbrella-Package installiert automatisch:

### [seven2one-questra-authentication](https://pypi.org/project/seven2one-questra-authentication/)

OAuth2-Authentifizierung für alle Questra-APIs.

```python
from seven2one.questra.authentication import QuestraAuthentication

auth = QuestraAuthentication(url="...", username="...", password="...")
```

### [seven2one-questra-data](https://pypi.org/project/seven2one-questra-data/)

High-Level API für Dynamic Objects und TimeSeries. Unterstützt GraphQL und REST, optionale pandas-Integration.

**Features:**

- CRUD-Operationen für benutzerdefinierte Inventare
- Zeitreihen-Verwaltung mit effizientem Batch-Loading
- Typsichere Dataclasses für Inventory-Schemas
- Optional: pandas DataFrames für Analyse-Workflows

```python
from seven2one.questra.data import QuestraData

client = QuestraData(graphql_url="...", auth_client=auth)
items = client.list_items(
    inventory_name="Sensoren",
    namespace_name="IoT",
    properties=["_id", "name"]
)
```

Siehe [Dokumentation auf PyPI](https://pypi.org/project/seven2one-questra-data/) für Details zu GraphQL/REST-Queries, Batch-Operationen und pandas-Integration.

### [seven2one-questra-automation](https://pypi.org/project/seven2one-questra-automation/)

GraphQL-Client für Workflow-Automatisierung und Event-Driven Architectures.

**Features:**

- Workflow-Management (erstellen, starten, überwachen)
- Event-basierte Trigger
- Task-Orchestrierung

```python
from seven2one.questra.automation import QuestraAutomation

automation = QuestraAutomation(graphql_url="...", auth_client=auth)
workflows = automation.list_workflows()
```

Siehe [Dokumentation auf PyPI](https://pypi.org/project/seven2one-questra-automation/) für Workflow-APIs und Event-Handling.

## Weitere Ressourcen

- **Vollständige Dokumentation:** <https://pydocs.[questra-host.domain]>
- **Support:** <support@seven2one.de>

## License

Proprietary - Seven2one Informationssysteme GmbH
