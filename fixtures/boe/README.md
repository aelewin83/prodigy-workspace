# BOE Workbook Fixture

The BOE parity gate expects the Excel template workbook at:

`fixtures/boe/BOE_MF_Template_NYC.xlsx`

If your local copy is stored elsewhere, set:

`BOE_WORKBOOK_PATH=/absolute/path/to/BOE\ MF\ Template\ NYC.xlsx`

Example:

```bash
export BOE_WORKBOOK_PATH="/Users/adamlewin/Library/CloudStorage/Dropbox/Shared with Adam/Templates/BOE MF Template NYC.xlsx"
```

This workbook is not committed by default. Place your local copy in this folder or set the env var.

The parity runner fails with a clear error if the workbook is missing.
