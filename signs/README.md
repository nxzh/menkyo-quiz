# signs/

The road-sign images used by `question_type: sign`, `marking` and `signal` questions.

One SVG per file, named by its 標識令 catalogue number (`301.svg`), with the variant
appended where one number has several drawings (`323-40.svg` is 最高速度 showing 40).
`index.csv` carries, for each file, the catalogue number, the Japanese name, the
variant, the sign class (規制標識 / 警戒標識 / 指示標識 …) and where the artwork came from.

The signs themselves are the 標識令 catalogue — Japanese government works, not
copyrightable under Article 13 of the Copyright Act. The SVG renderings are the
Wikimedia Commons `Japan_road_sign_*` set, which Commons keeps under PD-Japan-exempt,
plus a small number redrawn for this project. `source` and `source_file` in `index.csv`
record which is which.

A question references a file through its `image` object:

```json
"image": {
  "sign_no": "301",
  "file": "301.svg",
  "license": "PD-Japan-exempt (標識令 catalogue reproduction)",
  "file_verified": true
}
```

`tools/validate.py` fails if a referenced file is missing.
