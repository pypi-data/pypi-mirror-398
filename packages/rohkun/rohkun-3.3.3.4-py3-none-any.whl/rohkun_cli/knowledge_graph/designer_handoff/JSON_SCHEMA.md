# Rohkun CLI JSON Report Schema

**Complete documentation of the JSON report structure used by the Knowledge Graph generator**

This document describes every field, type, and possible value in the JSON report that the CLI generates. The Knowledge Graph reads from this exact structure.

---

## Root Level Structure

```json
{
  "version": "2.0.0",
  "generated_at": "2025-01-15T10:30:45.123456Z",
  "project": { ... },
  "summary": { ... },
  "endpoints": [ ... ],
  "api_calls": [ ... ],
  "connections": [ ... ],
  "blast_radius": [ ... ],
  "high_impact_nodes": [ ... ],
  "accuracy": { ... },
  "metadata": { ... }
}
```

---

## 1. `version` (string, required)
- **Type**: `string`
- **Format**: Semantic version (e.g., "2.0.0")
- **Description**: Report format version
- **Example**: `"2.0.0"`

---

## 2. `generated_at` (string, required)
- **Type**: `string`
- **Format**: ISO 8601 UTC timestamp with 'Z' suffix
- **Description**: When the report was generated
- **Example**: `"2025-01-15T10:30:45.123456Z"`

---

## 3. `project` (object, required)

```json
{
  "path": "/absolute/path/to/project",
  "name": "project-name"
}
```

### Fields:
- **`path`** (string, required)
  - Absolute file system path to project root
  - Example: `"/Users/john/my-api"` or `"D:\\Projects\\my-api"`
  
- **`name`** (string, required)
  - Project directory name (basename of path)
  - Example: `"my-api"`

---

## 4. `summary` (object, required)

```json
{
  "total_endpoints": 25,
  "total_api_calls": 48,
  "total_connections": 32,
  "files_scanned": 156
}
```

### Fields:
- **`total_endpoints`** (integer, required)
  - Count of unique endpoints found
  - Range: `0` to `infinity`
  
- **`total_api_calls`** (integer, required)
  - Count of unique API calls found
  - Range: `0` to `infinity`
  
- **`total_connections`** (integer, required)
  - Count of matched connections between endpoints and API calls
  - Range: `0` to `infinity`
  
- **`files_scanned`** (integer, required)
  - Number of files analyzed
  - Range: `0` to `infinity`

---

## 5. `endpoints` (array, required)

Array of endpoint objects. Each endpoint represents a backend API route/endpoint.

```json
[
  {
    "method": "GET",
    "path": "/api/users",
    "file": "routes/users.py",
    "line": 42,
    "confidence": "confident"
  }
]
```

### Endpoint Object Fields:

- **`method`** (string, required)
  - HTTP method
  - **Possible values**: `"GET"`, `"POST"`, `"PUT"`, `"DELETE"`, `"PATCH"`, `"OPTIONS"`, `"HEAD"`
  - **Can be**: `null`, empty string `""`, or missing (treated as `"GET"` or `"UNKNOWN"`)
  - **Example**: `"GET"`, `"POST"`, `null`
  
- **`path`** (string, required)
  - API endpoint path/route
  - **Format**: Usually starts with `/` (e.g., `/api/users`)
  - **Can be**: `null`, empty string `""`, or missing (treated as `"unknown"`)
  - **Example**: `"/api/users"`, `"/api/users/:id"`, `"/posts/:postId/comments"`
  
- **`file`** (string, required)
  - Relative file path from project root
  - **Can be**: `null`, empty string `""`, or missing (treated as `"unknown"`)
  - **Example**: `"routes/users.py"`, `"src/api/endpoints.ts"`, `"app/controllers/users_controller.rb"`
  
- **`line`** (integer, optional)
  - Line number where endpoint is defined
  - **Can be**: `null`, `0`, or missing (treated as `0` or `"?"`)
  - **Range**: `1` to `infinity` (if present)
  - **Example**: `42`, `105`, `null`
  
- **`confidence`** (string, optional)
  - Detection confidence level
  - **Possible values**: `"confident"`, `"uncertain"`, `"high"`, `"medium"`, `"low"`
  - **Can be**: `null` or missing (treated as `"medium"`)
  - **Example**: `"confident"`, `"uncertain"`

### Unknown/Missing Data Handling:
- If `method` is missing/null/empty → Use `"UNKNOWN"` (display in gray #666666)
- If `path` is missing/null/empty → Use `"unknown"` (display in gray)
- If `file` is missing/null/empty → Use `"unknown"` (display in tooltip)
- If `line` is missing/null/0 → Use `"?"` (display in tooltip)

---

## 6. `api_calls` (array, required)

Array of API call objects. Each represents a frontend call to an API endpoint.

```json
[
  {
    "method": "GET",
    "url": "https://api.example.com/users",
    "file": "src/services/api.js",
    "line": 128,
    "confidence": "confident"
  }
]
```

### API Call Object Fields:

- **`method`** (string, required)
  - HTTP method used in the call
  - **Possible values**: Same as endpoint `method`
  - **Can be**: `null`, empty string, or missing (treated as `"GET"` or `"UNKNOWN"`)
  - **Example**: `"GET"`, `"POST"`, `null`
  
- **`url`** (string, required)
  - Full URL or path being called
  - **Can be**: `null`, empty string, or missing (treated as `"unknown"`)
  - **Example**: `"https://api.example.com/users"`, `"/api/users"`, `"api/users"`
  
- **`file`** (string, required)
  - Relative file path from project root
  - **Can be**: `null`, empty string, or missing (treated as `"unknown"`)
  - **Example**: `"src/services/api.js"`, `"frontend/api/client.ts"`
  
- **`line`** (integer, optional)
  - Line number where API call is made
  - **Can be**: `null`, `0`, or missing (treated as `0` or `"?"`)
  - **Range**: `1` to `infinity` (if present)
  - **Example**: `128`, `45`, `null`
  
- **`confidence`** (string, optional)
  - Detection confidence level
  - **Possible values**: Same as endpoint `confidence`
  - **Can be**: `null` or missing (treated as `"medium"`)
  - **Example**: `"confident"`, `"uncertain"`

### Unknown/Missing Data Handling:
- Same as endpoints (use `"UNKNOWN"`, `"unknown"`, `"?"`)

---

## 7. `connections` (array, required)

Array of connection objects. Each represents a matched relationship between an endpoint and an API call.

```json
[
  {
    "endpoint": { ... },
    "api_call": { ... },
    "confidence": "high",
    "confidence_score": 85,
    "confidence_reasons": ["exact_path_match", "method_match"]
  }
]
```

### Connection Object Fields:

- **`endpoint`** (object, required)
  - **Type**: Endpoint object (same structure as in `endpoints` array)
  - **Description**: The backend endpoint being called
  - **Can contain**: All fields from endpoint object (method, path, file, line, confidence)
  - **Note**: May have missing/null fields (handle as described in endpoints section)
  
- **`api_call`** (object, required)
  - **Type**: API call object (same structure as in `api_calls` array)
  - **Description**: The frontend call that matches this endpoint
  - **Can contain**: All fields from api_call object (method, url, file, line, confidence)
  - **Note**: May have missing/null fields (handle as described in api_calls section)
  
- **`confidence`** (string, optional)
  - Overall confidence of the match
  - **Possible values**: `"high"`, `"medium"`, `"low"`, `"confident"`, `"uncertain"`
  - **Can be**: `null` or missing (treated as `"medium"`)
  - **Example**: `"high"`, `"medium"`, `"low"`
  
- **`confidence_score`** (integer, optional)
  - Numeric confidence score (0-100)
  - **Range**: `0` to `100`
  - **Can be**: `null` or missing (treated as `50`)
  - **Used for**: Edge opacity/width in graph visualization
  - **Example**: `85`, `50`, `30`
  
- **`confidence_reasons`** (array, optional)
  - List of reasons why this connection was matched
  - **Type**: Array of strings
  - **Can be**: `null`, empty array `[]`, or missing (treated as `[]`)
  - **Possible values**: 
    - `"exact_path_match"` - Path matches exactly
    - `"method_match"` - HTTP method matches
    - `"partial_path_match"` - Path partially matches
    - `"same_file"` - Endpoint and call in same file
    - `"similar_naming"` - Similar naming patterns
  - **Example**: `["exact_path_match", "method_match"]`, `["partial_path_match"]`, `[]`

### Unknown/Missing Data Handling:
- If `confidence_score` is missing/null → Use `50` (medium opacity)
- If `confidence_reasons` is missing/null → Use empty array `[]`
- Handle nested `endpoint` and `api_call` objects as described in their respective sections

---

## 8. `blast_radius` (array, optional)

Array of blast radius objects. Represents nodes with high impact (many dependents).

```json
[
  {
    "target": "/api/users",
    "severity": "high",
    "affected_files": 15,
    "affected_endpoints": 8,
    "impact_description": "Changes to this endpoint would affect 8 other endpoints"
  }
]
```

### Blast Radius Object Fields:

- **`target`** (string, required)
  - The endpoint/path/file that has high impact
  - **Can be**: `null`, empty string, or missing
  - **Example**: `"/api/users"`, `"routes/users.py"`, `"UserService"`
  
- **`severity`** (string, required)
  - Impact severity level
  - **Possible values**: `"critical"`, `"high"`, `"medium"`, `"low"`
  - **Can be**: `null` or missing (treated as `"medium"`)
  - **Example**: `"critical"`, `"high"`
  
- **`affected_files`** (integer, optional)
  - Number of files that would be affected
  - **Range**: `0` to `infinity`
  - **Can be**: `null` or missing (treated as `0`)
  - **Example**: `15`, `8`
  
- **`affected_endpoints`** (integer, optional)
  - Number of endpoints that would be affected
  - **Range**: `0` to `infinity`
  - **Can be**: `null` or missing (treated as `0`)
  - **Example**: `8`, `12`
  
- **`impact_description`** (string, optional)
  - Human-readable description of impact
  - **Can be**: `null`, empty string, or missing (treated as `""`)
  - **Example**: `"Changes to this endpoint would affect 8 other endpoints"`

---

## 9. `high_impact_nodes` (array, optional)

Array of high impact node objects. Similar to blast_radius but different structure.

```json
[
  {
    "target": "/api/users",
    "severity": "high",
    "impact_description": "High impact node with many connections"
  }
]
```

### High Impact Node Object Fields:

- **`target`** (string, required)
  - The endpoint/path/file that is high impact
  - **Can be**: `null`, empty string, or missing
  - **Example**: `"/api/users"`, `"routes/users.py"`
  
- **`severity`** (string, required)
  - Impact severity level
  - **Possible values**: `"critical"`, `"high"`, `"medium"`, `"low"`
  - **Can be**: `null` or missing (treated as `"medium"`)
  - **Example**: `"critical"`, `"high"`
  
- **`impact_description`** (string, optional)
  - Human-readable description
  - **Can be**: `null`, empty string, or missing (treated as `""`)
  - **Example**: `"High impact node with many connections"`

**Note**: Used to mark nodes in graph as "high impact" (display in red #ff3333)

---

## 10. `accuracy` (object, optional)

Accuracy metrics and confidence distribution.

```json
{
  "estimated_accuracy": "92.5%",
  "high_confidence": 28,
  "medium_confidence": 12,
  "low_confidence": 3
}
```

### Accuracy Object Fields:

- **`estimated_accuracy`** (string, optional)
  - Overall accuracy estimate
  - **Format**: Percentage string (e.g., "92.5%")
  - **Can be**: `null` or missing (treated as `"N/A"`)
  - **Example**: `"92.5%"`, `"85.0%"`
  
- **`high_confidence`** (integer, optional)
  - Count of high confidence detections
  - **Range**: `0` to `infinity`
  - **Can be**: `null` or missing (treated as `0`)
  - **Example**: `28`, `15`
  
- **`medium_confidence`** (integer, optional)
  - Count of medium confidence detections
  - **Range**: `0` to `infinity`
  - **Can be**: `null` or missing (treated as `0`)
  - **Example**: `12`, `8`
  
- **`low_confidence`** (integer, optional)
  - Count of low confidence detections
  - **Range**: `0` to `infinity`
  - **Can be**: `null` or missing (treated as `0`)
  - **Example**: `3`, `5`

---

## 11. `metadata` (object, required)

Additional metadata about the scan.

```json
{
  "files_scanned": 156
}
```

### Metadata Object Fields:

- **`files_scanned`** (integer, required)
  - Number of files analyzed
  - **Range**: `0` to `infinity`
  - **Example**: `156`, `42`

---

## Complete Example JSON

```json
{
  "version": "2.0.0",
  "generated_at": "2025-01-15T10:30:45.123456Z",
  "project": {
    "path": "/Users/john/my-api",
    "name": "my-api"
  },
  "summary": {
    "total_endpoints": 25,
    "total_api_calls": 48,
    "total_connections": 32,
    "files_scanned": 156
  },
  "endpoints": [
    {
      "method": "GET",
      "path": "/api/users",
      "file": "routes/users.py",
      "line": 42,
      "confidence": "confident"
    },
    {
      "method": "POST",
      "path": "/api/users",
      "file": "routes/users.py",
      "line": 58,
      "confidence": "confident"
    },
    {
      "method": null,
      "path": "/api/unknown",
      "file": null,
      "line": null,
      "confidence": "uncertain"
    }
  ],
  "api_calls": [
    {
      "method": "GET",
      "url": "https://api.example.com/users",
      "file": "src/services/api.js",
      "line": 128,
      "confidence": "confident"
    }
  ],
  "connections": [
    {
      "endpoint": {
        "method": "GET",
        "path": "/api/users",
        "file": "routes/users.py",
        "line": 42,
        "confidence": "confident"
      },
      "api_call": {
        "method": "GET",
        "url": "https://api.example.com/users",
        "file": "src/services/api.js",
        "line": 128,
        "confidence": "confident"
      },
      "confidence": "high",
      "confidence_score": 85,
      "confidence_reasons": ["exact_path_match", "method_match"]
    }
  ],
  "blast_radius": [
    {
      "target": "/api/users",
      "severity": "high",
      "affected_files": 15,
      "affected_endpoints": 8,
      "impact_description": "Changes to this endpoint would affect 8 other endpoints"
    }
  ],
  "high_impact_nodes": [
    {
      "target": "/api/users",
      "severity": "high",
      "impact_description": "High impact node with many connections"
    }
  ],
  "accuracy": {
    "estimated_accuracy": "92.5%",
    "high_confidence": 28,
    "medium_confidence": 12,
    "low_confidence": 3
  },
  "metadata": {
    "files_scanned": 156
  }
}
```

---

## Knowledge Graph Usage

The Knowledge Graph generator (`generator.py`) uses this JSON structure as follows:

1. **Nodes**: Created from `endpoints` array
   - One node per unique endpoint (key: `method:path`)
   - Node size based on connection count
   - Node color based on HTTP method
   - High impact nodes (from `high_impact_nodes`) shown in red

2. **Edges**: Created from `connections` array
   - Edge from endpoint to matched API call endpoint
   - Edge opacity based on `confidence_score`
   - Edge width based on `confidence_score`

3. **Unknown Handling**:
   - Missing/null `method` → `"UNKNOWN"` (gray #666666)
   - Missing/null `path` → `"unknown"` (gray)
   - Missing/null `file` → `"unknown"` (tooltip)
   - Missing/null `line` → `"?"` (tooltip)

---

## Notes for UI Designer

1. **Always handle null/empty values** - The JSON may have missing fields
2. **Use fallback values** - Default to `"unknown"`, `"?"`, or `0` when data is missing
3. **Color coding**:
   - GET: Purple (#7c3aed)
   - POST: Green (#00ff41)
   - PUT: Orange (#ff9500)
   - DELETE: Red (#ff3333)
   - UNKNOWN: Gray (#666666)
4. **High impact nodes**: Check `high_impact_nodes` array to mark nodes as high impact (red)
5. **Edge styling**: Use `confidence_score` (0-100) for opacity and width














