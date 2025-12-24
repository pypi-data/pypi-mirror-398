# Sleet
**A configuration driven project initializer without boilerplates**

## What is this?
Sleet is a project initializer, but unlike similar already existing tools like cookiecutter, sleet doesnt depend on boilerplates. Instead sleet builds upon real time command execution and a config-driven workflow. Sleet has integration with modern tools such as git and uv built in with letting you code your own integrations coming soon.

## Preview!
Heres a config snippet showing how sleet works:
```yaml
meta:
  desc: "My cool setup script"
  author: "Cool developer dude"

exec:
  - uv-init:
      type: "uv-init"

  - install-venv:
      type: "uv-venv"
      version: "3.14"

  - install-tools:
      type: "uv-install"
      names: ["pytest", "ruff", "pre-commit"]
      dev: True

  - commit:
      type: "git-commit"
```
But sleet can do so much more! It has support for executing custom commands and creating/editing files.

## Roadmap
* [x] Core module functionality
* [x] Working CLI
* [ ] Loading custom modules
* [ ] Better error handling / logging
* [ ] Builtin configs

## Installation
The tool can be installed in multiple ways, but we recommend you use `uv tool` to install it globally in your system:
```bash
uv tool install sleet
```
But if you dont have uv installed, dont worry! You can also install using `pip`/`pipx`:
```bash
pipx install sleet
```

## Getting Started
### Getting the config path
Sleet reads configs from a set config path, which is varied between operating systems but you can find out what it is for you with the `sleet listdata` command where you can look for the "Config Path" data entry.

For example, here is where my configs will be stored as i am on linux: `/home/cheetah/.config/sleet/configs`

### Writing your first config
Alright, now you finally know where to store your configs, but what now? Lets start by creating a tiny config, create a file inside the config directory (create the directory if needed) called `myconfig.yaml` and paste in the following:
```yaml
meta:
  desc: "My cool setup script"
  author: "Cool developer dude"

exec:
  - initalize-git:
      type: "git-init"

  - initial-commit:
      type: "git-commit"
      message: "my first commit!"
```
congratulations, you have created your first config! Now you can navigate to a new directory and run `sleet run myconfig` in the terminal to execute your config!

If you havent noticed already this config initializes a new repo and makes an initial commit.

### Explanation
Lets go over everything we just wrote step by step:
* the name (`myconfig.yaml`) - what you call your config, remove the `.yaml` and you have the name youll use when running the config.
* Metadata (`desc` and `author`) - Currently has no purpouse but is recommended as it will be used for planned features (that are coming really soon).
* exec tasks (in this example: the initialize git and commit steps) - Each part of a setup config is called a task, well dig a bit deeper into one of them, the `initial-commit` task:
  * `- initial-commit:` - the label of the task, can be anything and will be used in logging when running the config
  * `type: "git-commit"` - the type of task, for a full list of tasks please refer to the [Task Type List](/docs/tasks.md)
  * `message: "my first commit!"` - A type specific argument, some tasks dont have an argument, some have multiple. For information about each types arguments, please refer to the [Task Type List](/docs/tasks.md)

### Adding more
Lets extend this config to also write an .gitignore before commiting, we can do this by adding another task, specifically with the "file-write" type:
```yaml
  - configure-precommit:
      type: "file-write"
      path: ".gitignore"
      contents: |
      __pycache__/
      .venv
      .ruff_cache
```
Note that this contains multiline strings, i will not go over those in this guide.

Lets add this step before we commit our changes:
```yaml
meta:
  desc: "My cool setup script"
  author: "Cool developer dude"

exec:
  - initalize-git:
      type: "git-init"

  - configure-precommit:
      type: "file-write"
      path: ".gitignore"
      contents: |
      __pycache__/
      .venv
      .ruff_cache

  - initial-commit:
      type: "git-commit"
      message: "my first commit!"
```
That is the basics! To learn about all the different task types you can refer to the [Task Type List](/docs/tasks.md).

## Contributing
Note that before contributing all your changes should go through the pre-commit config, further contribution / developement documentation is coming soon!

For now, use pre-commit, dependencies are in the "dev" dependency group, also explain every change you make in the pr so i can better understand why they should be added.