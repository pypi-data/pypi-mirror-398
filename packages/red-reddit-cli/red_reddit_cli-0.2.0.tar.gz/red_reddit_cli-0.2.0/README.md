# Red - a Reddit CLI (under construction)

Uses [PRAW](https://praw.readthedocs.io/en/stable/index.html), so need to [set up configuration according to the docs](https://praw.readthedocs.io/en/stable/getting_started/configuration.html)

- Lists all subscribed subs via

  ```bash
  $ red subs ls
  ```

- And declaratively manages Multireddits (custom feeds):
  - Generate existing custom feeds YAML:
    ```bash
    $ red multis genconf
    wrote /Users/george/.config/red.yaml
    ```

- Edit YAML

- Apply updates:

  ```bash
  $ red multis apply
  ```

  With this command the YAML file is the source of truth:
  - If a multireddit doesn't exist, create it and add subs declared under it
    - subscribe to subs too

  - If a multireddit exists online but not in the file, delete it
    - member subs stay subscribed

  - If a multireddit exists, update it with subs declared under in the file

# License

[MIT](LICENSE)

# Copyright

2025 George Kontridze
