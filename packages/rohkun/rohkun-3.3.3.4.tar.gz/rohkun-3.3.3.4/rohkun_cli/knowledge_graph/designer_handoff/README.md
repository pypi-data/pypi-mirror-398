# Knowledge Graph - UI Designer Handoff

## Folder Structure
```
designer_handoff/
├── index.html          # Main HTML file (self-contained)
├── example-data.json   # Sample data structure
├── styles.css          # All styles (extracted for easy editing)
├── script.js           # All JavaScript (extracted for easy editing)
├── JSON_SCHEMA.md      # ⭐ COMPLETE JSON structure documentation
└── README.md           # This file
```

## ⭐ IMPORTANT: Read JSON_SCHEMA.md First!

**`JSON_SCHEMA.md`** contains the **complete, detailed documentation** of the JSON report structure that the Knowledge Graph reads from. It includes:
- Every field and its type
- All possible values
- How to handle missing/null data
- Complete examples
- Unknown data handling rules

**Read this before making any changes!**

## How It Works
- **Single HTML file**: Everything is in `index.html` (inline CSS/JS)
- **Data format**: JSON structure in `example-data.json`
- **Unknowns handling**: Unknown/missing data shown in gray (#666666)

## Design Notes
- Dark mode: Background #030303
- Accent color: Purple #7c3aed
- Unknown nodes: Gray #666666
- Font: JetBrains Mono (monospace)

## To Edit
1. Open `index.html` in browser to see it
2. Edit styles in the `<style>` tag
3. Edit JavaScript in the `<script>` tag
4. Test with `example-data.json` data

## Unknown Data Handling
- Unknown method → Gray color (#666666)
- Unknown path → Shows "unknown" label
- Missing file → Shows "unknown" in tooltip
- Missing line → Shows "?" in tooltip

