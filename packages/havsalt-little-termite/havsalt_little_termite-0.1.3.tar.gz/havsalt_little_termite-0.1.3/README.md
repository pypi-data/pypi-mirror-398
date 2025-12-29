# Little Termite

Terminate command output, by controlling this little hungry and human-looking termite.

![One of the commands to run the game](./images/command.png)
![Image of how the game looks](./images/in_game.png)

## Installation

Before installing `little-termite`, make sure to have a `Rust compiler` available.
You can use `rustc` through [Cargo](https://doc.rust-lang.org/cargo/getting-started/installation.html). This is for compiling `charz-rust`, which results in faster rendering.

### Using [pipx](https://github.com/pypa/pipx)

The easist way to start terminating command output, is to install using `pipx`:

```console
pipx install havsalt-little-termite
```

Then, feed `little-termite` the output of your favorite command!

```console
ipconfig | little-termite
```

You can also try using other commands like `ls`, `grep` and `cat`.
It is *more fun* when the output contains **many lines**.

### Using [git clone](https://git-scm.com/downloads) and [rye](https://rye.astral.sh/guide/installation)

Make sure you have `git` and `rye` installed.

Then, run the following steps.

```console
git clone https://github.com/havsalt/little-termite.git
cd little-termite
rye sync
ipconfig | rye run little-termite
```

You can use a different command other than `ipconfig` if you wish. Again, it should output a decent amount of lines, so it's more lines to terminate.

## Controls

Keyboard controls for moving the little human-looking termite.

- Move sideways using `a` and `d`.
- Eat using `f`.
- Jump using `spacebar`.
  - Super jump by using `shift`+`spacebar`.

To exit the game, use `escape`.

## Rational

This small little command line game was made with my cousin, using `charz`. [charz](https://pypi.org/project/charz) is my Python library that I made for terminal games. It reached release `0.1.0` on **Jun 1, 2025**, and we made `little-termite` to stress test the library, check its capabilities, and uncover some bugs.

## License

MIT
