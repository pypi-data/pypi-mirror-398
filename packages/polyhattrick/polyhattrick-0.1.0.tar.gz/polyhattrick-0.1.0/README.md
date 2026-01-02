# polyhattrick

`polyhattrick` is a simple command-line utility for fetching live match scores from [Hattrick](https://www.hattrick.org). It can be easily integrated into `polybar`, allowing you to see how your team is performing live directly on your desktop.

---

## Installation

Install `polyhattrick` using `pip`:

```bash
pip install polyhattrick
```

## Authentication

Before you can display match results in your terminal or in polybar, you need to authorize polyhattrick to access your match data on Hattrick.

First, start the authentication process:

```bash
polyhattrick login authenticate
```

This command will generate a login link. Open it in your browser to log in to Hattrick and authorize polyhattrick. Once authorized, Hattrick will display a token. Copy this token and complete the authorization process:

```bash
polyhattrick login exchange [TOKEN]
```

## Usage

After authentication, you can start fetching live match results.

To display the score of the first match in your live ticker on Hattrick, run:

```bash
polyhattrick match live watch
```

If you want to see the result of a different match, reorder your live ticker on the Hattrick website so that the desired match appears first.

## Integration with polybar

To display live match results in polybar, add the following module to your polybar configuration:

```
[module/hattrick]
type = custom/script
exec = polyhattrick match live watch
```

Then place the module wherever you want it to appear in your bar.

## Notes

- This tool is intended for Linux systems.

- Make sure polyhattrick is available in your PATH when used with polybar.
