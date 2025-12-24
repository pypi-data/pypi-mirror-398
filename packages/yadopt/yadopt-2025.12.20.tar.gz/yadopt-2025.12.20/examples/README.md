Examples
================================================================================

### 01\_type\_hint.py

```console
$ python3 01_type_hint.py config.toml --epochs 10 --model cnn --lr 0.01
YadOptArgs(config_path=config.toml, epochs=10, model=cnn, lr=0.01, help=False)
```

### 02\_decorator.py

```console
$ python3 02_decorator.py config.toml --epochs 10 --model cnn --lr 0.01
YadOptArgs(config_path=config.toml, epochs=10, model=cnn, lr=0.01, help=False)
```

### 03\_sub\_command.py

```console
$ python3 03_subcommand.py foo --foo_opt 10
YadOptArgs(foo_opt=0, bar_opt=0, help=False, foo=True)
```

### 04\_save\_and\_load.py

```console
$ python3 04_save_and_load.py --restore 04_saved_arguments.json
YadOptArgs(train=True, test=False, epochs=100, model=cnn, optimizer=radam, lr=0.001, weight_decay=0.0005, batch_size=64, restore=None, help=False)
```
