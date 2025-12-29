---
id: features
title: Features
sidebar_position: 5
---

# Features

This section covers the key features and functionality provided by the Synapse SDK.

## [Plugin System](../plugins/plugins.md)

Comprehensive plugin framework for building and managing ML workflows.

- **[Plugin Categories](../plugins/plugins.md#plugin-categories)** - Neural networks, export, upload, smart tools, and validation plugins
- **[Execution Methods](../plugins/plugins.md#execution-methods)** - Job, Task, and REST API execution modes
- **[Development Guide](../plugins/plugins.md#creating-plugins)** - Create, test, and deploy custom plugins

## [Pipeline Patterns](./pipelines/index.md)

Powerful workflow orchestration patterns for complex multi-step operations.

- **[Step Orchestration](./pipelines/step-orchestration.md)** - Sequential step-based workflows with progress tracking and rollback
- **Utility Steps** - Built-in logging, timing, and validation step wrappers
- **Action Integration** - Seamless integration with Train, Export, and Upload actions

## [Data Converters](./converters/index.md)

Comprehensive data format conversion utilities for computer vision datasets.

- **[Format Converters](./converters/index.md)** - Convert between DM, COCO, Pascal VOC, and YOLO formats
- **[Version Migration](./converters/index.md#dm-version-converter)** - Migrate DM datasets between versions