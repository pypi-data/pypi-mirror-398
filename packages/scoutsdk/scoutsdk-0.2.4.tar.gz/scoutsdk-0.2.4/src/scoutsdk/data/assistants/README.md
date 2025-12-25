# Scout CLI - Synchronize Assistants

This guide explains how to use the `synchronize-assistants` command from Scout CLI to manage your Scout assistants through configuration files.

## Overview

The `synchronize-assistants` command allows you to:

- Create and update assistants from a JSON configuration file
- Manage assistant properties (name, description, instructions, etc.)
- Upload and manage files associated with assistants
- Define prompt starters and allowed functions

## Prerequisites

- Scout SDK installed
- Valid Scout API credentials configured

## Usage

Basic command structure:

```bash
scoutcli synchronize-assistants -c <path_to_config_file> [options]
```

### Command Options

- `-c, --config`: Path to the JSON configuration file (required)
- `-o, --overwrite`: Overwrite the config file with new assistant IDs (useful for first-time creation)
- `-f, --force`: Force overwrite of assistant files (replaces existing files)

## Configuration File Format

The configuration file should be a JSON file with the following structure:

```json
{
  "assistants": [
    {
      "name": "Assistant Name",
      "id": "Assistant_Unique_Identifier",
      "description": "Assistant Description",
      "instructions_text": "Inline instructions for the assistant",
      "instructions_path": "path/to/instructions.md",
      "allowed_functions": ["function1", "function2"],
      "use_system_prompt": true,
      "prompt_starters_text": ["Starter prompt 1", "Starter prompt 2"],
      "prompt_starters_path": ["path/to/prompt1.md", "path/to/prompt2.md"],
      "assistant_files": [
        {
          "filepath": "path/to/file1.txt",
          "description": "Description of file1"
        },
        {
          "filepath": "path/to/file2.txt"
        }
      ],
      "avatar_path": "path/to/avatar.png",
      "variables": {
        "key1": "value1"
      },
      "secrets": {
        "SECRET_KEY": "value"
      },
      "secrets_path": "path/to/secrets.json",
      "package_info" : {
        "package_path": "../functions/",
        "package_file_name": "custom_functions_package.zip"
      },
      "ui_info" : {
        "ui_path": "../micro-app/dist",
        "ui_package_file_name": "ui_package.zip",
        "ui_build_cmd": "cd ../micro-app && make dependencies build"
      }
    }
  ]
}
```

### Configuration Properties

| Property                 | Type    | Description                                                                             |
| ------------------------ | ------- | --------------------------------------------------------------------------------------- |
| `name`                 | string  | Name of the assistant (required)                                                        |
| `id`                   | string  | Unique identifier used to track this assistant versus the UUID that is created by scout |
| `description`          | string  | Description of the assistant (required)                                                 |
| `instructions_text`    | string  | Inline instructions text                                                                |
| `instructions_path`    | string  | Path to file containing instructions                                                    |
| `allowed_functions`    | array   | List of allowed function names, or ["all"] to allow all                                 |
| `use_system_prompt`    | boolean | Whether to use system prompt (default: false)                                           |
| `prompt_starters_text` | array   | List of prompt starter texts                                                            |
| `prompt_starters_path` | array   | List of paths to files containing prompt starters                                       |
| `assistant_files`      | array   | List of files to attach to the assistant. Each can have a `description`.              |
| `avatar_path`          | string  | Path to an image file to use as the assistant's avatar                                  |
| `variables`            | object  | Dictionary of variables to pass to the assistant                                        |
| `secrets`              | object  | Dictionary of secrets to pass to the assistant                                          |
| `secrets_path`         | string  | Path to a JSON file containing secrets                                                  |
| `package_info`         | object  | Object with `package_path` and `package_file_name` for uploading a package          |
| `ui_info`              | object  | Configuration for custom UI deployment (see UI Configuration section)                   |

> Note: You can use either `instructions_text` or `instructions_path`, but not both.
> You can use both `prompt_starters_text` and `prompt_starters_path` together.
> If both `secrets` and `secrets_path` are provided, `secrets` takes precedence.

### UI Configuration

The `ui_info` property allows you to configure a custom UI for your assistant. It supports the following properties:

```json

{

"ui_path":"path/to/ui/build",

"ui_package_file_name":"ui-package.zip",

"ui_build_cmd":"npm run build"// Optional

}

```

| Property                 | Type   | Description                                         |
| ------------------------ | ------ | --------------------------------------------------- |
| `ui_path`              | string | Path to the UI build directory                      |
| `ui_package_file_name` | string | Name of the zip file that will contain the built UI |
| `ui_build_cmd`         | string | Optional command to build the UI before packaging   |

## Examples

### Creating a New Assistant

1. Create a config file `assistants.json`:

```json
{
  "assistants": [
    {
      "name": "Code Helper",
      "id": "Code_helper_Assistant",
      "description": "Assistant for helping with coding tasks",
      "instructions_path": "instructions/code_helper.md",
      "allowed_functions": ["all"],
      "use_system_prompt": true,
      "prompt_starters_text": [
        "Help me understand this code",
        "Debug this function"
      ],
      "assistant_files": [
        {
          "filepath": "resources/coding_guidelines.md",
          "description": "Coding guidelines reference"
        }
      ],
      "avatar_path": "avatars/code_helper.png",
      "variables": {
        "LANGUAGE": "python"
      },
      "secrets_path": "secrets/code_helper_secrets.json",
      "package_info" : {
        "package_path": "../functions/",
        "package_file_name": "custom_functions_package.zip"
      },
      "ui_info" : {
        "ui_path": "../micro-app/dist",
        "ui_package_file_name": "ui_package.zip",
        "ui_build_cmd": "cd ../micro-app && make dependencies build"
      }
    }
  ]
}
```

2. Run the command with the overwrite flag to save the new assistant ID back to the config file:

```bash
scoutcli synchronize-assistants -c assistants.json -o
```

### Updating an Existing Assistant

Once you've created an assistant, the ID will be saved in your config file. You can modify other properties and run:

```bash
scoutcli synchronize-assistants -c assistants.json
```

### Forcing File Updates

To force update assistant files (replacing existing ones with the same name):

```bash
scoutcli synchronize-assistants -c assistants.json -f
```

## Best Practices

1. Keep instructions and larger prompt starters in separate files
2. Use the `-o` flag when creating assistants for the first time to save IDs
3. Organize related assistants in the same config file
4. Use descriptive names and descriptions for files
5. Store your configuration files in version control

## Troubleshooting

- If you encounter permission errors, ensure your Scout API credentials are correctly configured
- Make sure all file paths in the config are valid and accessible
- Use the verbose flag `-v` with the command for detailed error information

```bash
scoutcli synchronize-assistants -c assistants.json -v
```
