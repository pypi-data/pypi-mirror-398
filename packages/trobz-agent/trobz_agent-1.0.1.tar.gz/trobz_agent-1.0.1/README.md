# agent.py

This is to run different AI agents.

# Installation

```bash
uv pip install git+https://github.com/trobz/agent.py
```

# Usage

```bash
agent <instructions>
```

Run the above command to run the agent with instructions and default `codex` agent.

```bash
agent --instructions-file <instructions file name>
agent -f <instructions file name>
```

Alternatively run one of the above commands to run the agent with instructions in the file name.

```bash
agent --workflow <workflow file name>
agent -w <workflow file name>
```

Or one of the above command can be ran to run the agent with multiple instructions in workflow file name. The format of the workflow file is as follows:

```yaml
- name: name of the work flow
  code: code of the work flow
  steps:
    - name: name of the step
      original: original instruction
      work_dir: optional work directory
      command: bash command to run
    - name: name of other step
      original: original instruction
      condition: optional bash command to run and check the return code
      instruction: instruction to run the agent
    - name: name of other step
      original: original instruction
      ignore: true
      notes: notes
```

step can have `files` set to a list of files to include in the instruction for the agent to consult.

step can have `commit_if_change` set to either `true` or a string to commit the changes. If set to true, the step name is used as the commit message. If set to a string, the string is used instead.

```bash
--backend <agent name>
```

Add the above option to run the agent with agent name. Available agents: `codex`, `opencode`, and `gemini`.

```bash
--mode <mode>
```

Add the above option to run the agent with the mode. Available modes: `normal`, `yolo`. Mode `yolo` is to run `codex` with `--dangerously-bypass-approvals-and-sandbox` option and run `gemini` with `--yolo` option.

```bash
--model
```

Add the above option to use a different model.
