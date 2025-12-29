# Buz

[![PyPI version](https://badge.fury.io/py/buz.svg)](https://badge.fury.io/py/buz)
[![Python Support](https://img.shields.io/pypi/pyversions/buz.svg)](https://pypi.org/project/buz/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Buz** is a lightweight, simple, and extensible Python library that provides implementations of **Event**, **Command**, and **Query** buses following CQRS and Event-Driven Architecture patterns.

## 📋 Table of Contents

- [Buz](#buz)
  - [📋 Table of Contents](#-table-of-contents)
  - [✨ Key Features](#-key-features)
  - [🚀 Quick Start](#-quick-start)
    - [Installation](#installation)
    - [Basic Usage](#basic-usage)
      - [Event Bus Example](#event-bus-example)
      - [Command Bus Example](#command-bus-example)
      - [Query Bus Example](#query-bus-example)
  - [🏗️ Architecture](#️-architecture)
    - [Event Bus](#event-bus)
    - [Command Bus](#command-bus)
    - [Query Bus](#query-bus)
  - [🔧 Advanced Features](#-advanced-features)
    - [Middleware System](#middleware-system)
    - [Transactional Outbox Pattern](#transactional-outbox-pattern)
    - [RabbitMQ](#rabbitmq)
    - [Kafka Integration](#kafka-integration)
    - [Async Support](#async-support)
  - [📦 Message Brokers](#-message-brokers)
    - [Supported Brokers](#supported-brokers)
  - [🧪 Testing](#-testing)
  - [🔗 Related Projects](#-related-projects)
  - [📋 Requirements](#-requirements)
  - [🤝 Contributing](#-contributing)
    - [Development Setup](#development-setup)
  - [📄 License](#-license)
  - [📚 Documentation](#-documentation)
  - [🙋‍♀️ Support](#️-support)

## ✨ Key Features

- 🚌 **Bus Types**: Event, Command, and Query buses for clean architecture
- 🔄 **Sync & Async Support**: Both synchronous and asynchronous implementations
- 🔧 **Middleware System**: Extensible middleware for cross-cutting concerns
- 📦 **Message Brokers**: Support for Kafka, RabbitMQ (via Kombu), and in-memory
- 🔒 **Transactional Outbox**: Reliable event publishing with transactional guarantees
- 🎯 **Dependency Injection**: Built-in locator pattern for handler resolution
- 📝 **Type Safety**: Fully typed with mypy support
- 🪶 **Lightweight**: Minimal dependencies, maximum flexibility

## 🚀 Quick Start

### Installation

```bash
# Basic installation
pip install buz

# With Kafka support
pip install buz[aiokafka]

# With RabbitMQ support
pip install buz[kombu]

# With dependency injection
pip install buz[pypendency]
```

### Basic Usage

#### Event Bus Example

```python
from dataclasses import dataclass
from buz import Message
from buz.event import Event, BaseSubscriber
from buz.event.sync import SyncEventBus
from buz.locator.sync import InstanceLocator

@dataclass(frozen=True)
class UserCreated(Event):
    user_id: str
    email: str

class EmailSubscriber(BaseSubscriber):
    def consume(self, event: UserCreated) -> None:
        print(f"Sending welcome email to {event.email}")

class AnalyticsSubscriber(BaseSubscriber):
    def consume(self, event: UserCreated) -> None:
        print(f"Tracking user creation: {event.user_id}")

# Setup
locator: InstanceLocator = InstanceLocator()
locator.register(EmailSubscriber())
locator.register(AnalyticsSubscriber())

event_bus = SyncEventBus(locator)

# Usage
event = UserCreated(user_id="123", email="user@example.com")
event_bus.publish(event)
```

#### Command Bus Example

```python
from dataclasses import dataclass
from buz.command import Command
from buz.command.synchronous import BaseCommandHandler
from buz.command.synchronous.self_process import SelfProcessCommandBus
from buz.locator.sync import InstanceLocator

@dataclass(frozen=True)
class CreateUser(Command):
    email: str
    name: str

class CreateUserCommandHandler(BaseCommandHandler):
    def handle(self, command: CreateUser) -> None:
        # Business logic here
        print(f"Creating user: {command.name} ({command.email})")

# Setup
locator = InstanceLocator()
locator.register(CreateUserCommandHandler())

command_bus = SelfProcessCommandBus(locator)

# Usage
command = CreateUser(email="user@example.com", name="John Doe")
command_bus.handle(command)
```

#### Query Bus Example

```python
from dataclasses import dataclass
from buz.query import Query, QueryResponse
from buz.query.synchronous import BaseQueryHandler
from buz.query.synchronous.self_process import SelfProcessQueryBus
from buz.locator.sync import InstanceLocator

@dataclass(frozen=True)
class GetUser(Query):
    user_id: str

@dataclass(frozen=True)
class User:
    user_id: str
    name: str
    email: str

class GetUserQueryHandler(BaseQueryHandler):
    def handle(self, query: GetUser) -> QueryResponse:
        # Business logic here
        return QueryResponse(
            content=User(
                user_id=query.user_id,
                name="John Doe",
                email="john@example.com"
            )
        )

# Setup
locator = InstanceLocator()
locator.register(GetUserQueryHandler())

query_bus = SelfProcessQueryBus(locator)

# Usage
query = GetUser(user_id="123")
query_response = query_bus.handle(query)
user = query_response.content
print(f"User: {user.name}")
```

## 🏗️ Architecture

Buz implements the **Command Query Responsibility Segregation (CQRS)** pattern with distinct buses:

### Event Bus

- **Purpose**: Publish domain events and notify multiple subscribers
- **Pattern**: Pub/Sub with multiple handlers per event
- **Use Cases**: Domain event broadcasting, eventual consistency, integration events

### Command Bus

- **Purpose**: Execute business operations and commands
- **Pattern**: Single handler per command
- **Use Cases**: Business logic execution, write operations, state changes

### Query Bus

- **Purpose**: Retrieve data and execute queries
- **Pattern**: Single handler per query with typed responses
- **Use Cases**: Data retrieval, read operations, projections

## 🔧 Advanced Features

### Middleware System

Add cross-cutting concerns like logging, validation, and metrics:

```python
from datetime import datetime
from buz.event import Event, Subscriber
from buz.event.middleware import BasePublishMiddleware, BaseConsumeMiddleware
from buz.event.infrastructure.models.execution_context import ExecutionContext

class LoggingPublishMiddleware(BasePublishMiddleware):
    def _before_on_publish(self, event: Event) -> None:
        print(f"Publishing event {event}")

    def _after_on_publish(self, event: Event) -> None:
        return

class MetricsConsumeMiddleware(BaseConsumeMiddleware):
    def __init__(self) -> None:
        self.__consumption_start_time: datetime = datetime.now()

    def _before_on_consume(
        self,
        event: Event,
        subscriber: Subscriber,
        execution_context: ExecutionContext,
    ) -> None:
        self.__consumption_start_time = datetime.now()

    def _after_on_consume(
        self,
        event: Event,
        subscriber: Subscriber,
        execution_context: ExecutionContext,
    ) -> None:
        consumption_time_ms = int((datetime.now() - self.__consumption_start_time).total_seconds() * 1000)
        print(
            f"Subscriber {subscriber.fqn()} consumed event {event.id} successfully in {consumption_time_ms} ms"
        )

# Apply middleware
event_bus = SyncEventBus(
    locator=locator,
    publish_middlewares=[LoggingPublishMiddleware()],
    consume_middlewares=[MetricsConsumeMiddleware()]
)

# Usage
event = UserCreated(user_id="123", email="user@example.com")
event_bus.publish(event)
```

### Transactional Outbox Pattern

Ensure reliable event publishing with database transactions:

```python
from buz.event.transactional_outbox import TransactionalOutboxEventBus

# Configure with your database and event bus
transactional_outbox_bus = TransactionalOutboxEventBus(
    outbox_repository=your_outbox_repository,
    event_to_outbox_record_translator=your_outbox_record_translator,
    ...
)

# Events are stored in database, published later by worker
transactional_outbox_bus.publish(event)
```

### RabbitMQ

```python
from buz.event.infrastructure.kombu.kombu_event_bus import KombuEventBus

kombu_event_bus = KombuEventBus(
    connection=your_connection,
    publish_strategy=your_publish_strategy,
    publish_retry_policy=you_publish_retry_policy,
    ...
)

# Published and consumed in RabbitMQ
kombu_event_bus.publish(event)
```

### Kafka Integration

```python
from buz.kafka import BuzKafkaEventBus

kafka_bus = KafkaEventBus(
    publish_strategy=your_publish_strategy,
    producer=your_producer,
    logger=your_logger,
    ...
)

# Published and consumed in Kafka
kafka_bus.publish(event)
```

### Async Support

```python
from buz.event.async_event_bus import AsyncEventBus
from buz.query.asynchronous import QueryBus as AsyncQueryBus
from buz.command.asynchronous import CommandHandler as AsyncCommandHandler


# Async event bus
async_event_bus = AsyncEventBus(locator)
await async_event_bus.publish(event)

# Async query bus
async_query_bus = AsyncQueryBus(locator)
await async_query_bus.handle(event)

# Async command bus
async_command_bus = AsyncCommandBus(locator)
await async_command_bus.handle(command)
```

## 📦 Message Brokers

### Supported Brokers

| Broker    | Sync | Async | Installation                |
| --------- | ---- | ----- | --------------------------- |
| In-Memory | ✅   | ✅    | Built-in                    |
| Kafka     | ✅   | ✅    | `pip install buz[aiokafka]` |
| RabbitMQ  | ✅   | ❌    | `pip install buz[kombu]`    |

## 🧪 Testing

Buz includes testing utilities for unit and integration tests:

```python
from buz.event.sync import SyncEventBus
from buz.locator.sync import InstanceLocator

test_locator = InstanceLocator()
test_bus = SyncEventBus(test_locator)

test_locator.register(EmailSubscriber())
test_bus.publish(UserCreated(user_id="123", email="test@example.com"))
```

## 🔗 Related Projects

- **[buz-fever-shared](https://github.com/Feverup/buz-fever-shared)**: Opinionated utilities and standards for Buz
- **[buz-basic-example](https://github.com/Feverup/buz-basic-example)**: Complete example project with Docker setup

## 📋 Requirements

- Python 3.9+
- Optional dependencies based on features used

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/Feverup/buz.git
cd buz

# Install with development dependencies
make build

# Run tests
make test

# Run linting
make lint

# Format code
make format
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📚 Documentation

- [Changelog](CHANGELOG.md) - Release notes and version history

## 🙋‍♀️ Support

- Create an [Issue](https://github.com/Feverup/buz/issues) for bug reports or feature requests

---

Made with ❤️ by the [Fever Platform Team](platform@feverup.com)
