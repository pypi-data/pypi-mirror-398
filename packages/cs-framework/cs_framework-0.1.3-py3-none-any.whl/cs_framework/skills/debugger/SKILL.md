---
description: Tools for debugging C-S Framework execution logs (RDF).
---

# Debugger Workflow

Query and visualize execution logs (RDF/Turtle format) to understand system behavior.

## Use Cases

- Investigate why an event didn't trigger an action
- Trace the sequence of events leading to a state
- View the state of concepts at a specific point in time

## CLI Command

// turbo-all

### Launch GUI

```bash
csfw gui --log <path_to_ttl_file>
```

Opens a web-based debugger GUI at `http://localhost:8080`.

### Example

```bash
csfw gui --log execution.ttl
```

## Common SPARQL Queries

The execution logs are stored in RDF format. You can query them using SPARQL.

### List All Events

```sparql
PREFIX cs: <http://cs-framework.org/schema/>
SELECT ?name ?timestamp WHERE {
  ?event a cs:Event ;
         cs:hasName ?name .
}
```

### Find Actions Triggered by Event

```sparql
PREFIX cs: <http://cs-framework.org/schema/>
SELECT ?actionName WHERE {
  ?action a cs:Action ;
          cs:hasName ?actionName ;
          cs:triggeredBy ?event .
  ?event cs:hasName "moved" .
}
```

### Trace Causal Chain

```sparql
PREFIX cs: <http://cs-framework.org/schema/>
SELECT ?event ?action WHERE {
  ?action cs:triggeredBy ?event .
  ?event cs:hasName ?eventName .
  ?action cs:hasName ?actionName .
}
```
