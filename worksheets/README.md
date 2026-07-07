# QEDesk Worksheets

Worksheets are independent problem notebooks.

Each worksheet directory should contain:

```text
worksheets/<slug>/
|-- main.tex
`-- Proof.lean
```

Create one with:

```bash
./bin/qedesk new number-theory/fermat-little --title "Fermat's Little Theorem"
```

Then use the worksheet path as the command target:

```bash
./bin/qedesk lean worksheets/number-theory/fermat-little
./bin/qedesk sync worksheets/number-theory/fermat-little
./bin/qedesk pdf worksheets/number-theory/fermat-little
./bin/qedesk blueprint worksheets/number-theory/fermat-little
./bin/qedesk audit --dry-run worksheets/number-theory/fermat-little
```

Generated worksheet artifacts such as `build/` and `blueprint/web/` are ignored.
Commit the worksheet source files, not generated outputs.
