# signs/

The road-sign images used by `question_type: sign`, `marking` and `signal` questions.

One SVG per file, named by its 標識令 catalogue number (`301.svg`), with the variant
appended where one number has several drawings (`323-40.svg` is 最高速度 showing 40).
`index.csv` is the only index — there is no `index.json` — and carries one row per
file:

| column | what it is |
|---|---|
| `file` | the SVG in this folder, and the name a question references |
| `sign_no` | the 標識令 catalogue number |
| `name_ja` / `variant` | the Japanese name, and which drawing of that number this is |
| `category` | the sign class (規制標識 / 警戒標識 / 指示標識 …) |
| `source` | `commons` or `self-drawn` — who drew this rendering |
| `source_file` | the file it was taken from, under its original name |
| `license` | the licence the artwork is under |
| `source_url` | where that claim can be checked: the Commons file page, or this repository for a rendering drawn here |

The signs themselves are the 標識令 catalogue — Japanese government works, excluded
from copyright by Article 13 of the Copyright Act — so every row carries the same
`license`, `PD-Japan-exempt (標識令 catalogue reproduction)`, and the same string
appears in each question's `image.license`. Who drew a rendering is provenance, not
licence: `source`, `source_file` and `source_url` record that, per file, so a reader
can check one file at a time rather than trust a paragraph. The 129 Commons rows were
confirmed against the live file pages when the column was written.

A question references a file through its `image` object:

```json
"image": {
  "sign_no": "301",
  "file": "301.svg",
  "license": "PD-Japan-exempt (標識令 catalogue reproduction)",
  "file_verified": true
}
```

`tools/validate.py` fails if a referenced file is missing, if a file here has no row
or a row no file, if a row is missing its `license` or `source_url`, or if a question's
`image.license` is not the one its row carries.
