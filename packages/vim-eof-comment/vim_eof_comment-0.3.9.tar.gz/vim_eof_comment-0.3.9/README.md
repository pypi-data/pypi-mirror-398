# vim-eof-comment

![GitHub Repo stars](https://img.shields.io/github/stars/DrKJeff16/vim-eof-comment?style=flat-square)![GitHub Release](https://img.shields.io/github/v/release/DrKJeff16/vim-eof-comment?include_prereleases&sort=semver&display_name=release&style=flat-square)

[PyPI Package][pypi] | [Source Code][source]

Ensure Vim EOF comments in given files.

---

## About

This tool adds a [Vim modeline comment](https://neovim.io/doc/user/options.html#_2.-automatically-setting-options) at the end of the target files.

---

## Install

```bash
pip install vim-eof-comment
```

---

## Usage

General usage is as follows:

```bash
vim-eof-comment [-h] [-v] [-V] -e EXT1[,EXT2[,EXT3[,...]]] [-i EXT1:INDENT[:Y/N][,...]] [-n] dir1 [dir2 [...]]
```

You can also call it as a module:

```bash
python -m vim_eof_comment [-h] [-v] [-V] -e EXT1[,EXT2[,EXT3[,...]]] [-i EXT1:INDENT[:Y/N][,...]] [-n] dir1 [dir2 [...]]
```

### Example

```bash
vim-eof-comment -e py,md,lua .
```

---

## License

[GNU GPL-v2.0][license]

[license]: https://github.com/DrKJeff16/vim_eof_comment/blob/main/LICENSE
[pypi]: https://pypi.org/project/vim-eof-comment/
[source]: https://github.com/DrKJeff16/vim_eof_comment

<!-- vim: set ts=2 sts=2 sw=2 et ai si sta: -->
