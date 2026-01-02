# Strox - String Approximate

Find strings that matches approximately the given pattern.

## Running as tool

You can run `strox` from the terminal if installed, usually through `pipx install` or `uv tool install`.

Example of querying for the closest matching options, with _weight_ parameter.

```bash
strox "an" "Apple pie" "Indigo", "Banana" --insertion-cost 0.1
# Result: "Banana"
```

**Tip**: Run `strox --help` for more options.

## License

MIT
