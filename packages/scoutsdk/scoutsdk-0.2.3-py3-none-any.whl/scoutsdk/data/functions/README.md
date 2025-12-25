# Scout CLI Package Module

The `pkg_module` functionality in Scout CLI allows you to package your Scout functions project for distribution or upload to a Scout assistant. This tool creates a zip package containing your project files along with a generated `functions.json` that describes the Scout functions in your project.

## Usage

```bash
scout create-project-package -s <src-path> [options]
```

### Required Arguments

- `-s, --src-path`: Path to the source directory containing your Scout functions project

### Optional Arguments

- `-o, --output-path`: Custom output path for the generated package (default: parent directory of source path)
- `-u, --upload`: Upload the package to a Scout assistant after creation
- `-a, --assistant-id`: Assistant ID to upload the package to (overrides any value in .env file)
- `-m, --micro-app`: Create a Micro App project

## Examples

### Basic Usage

Package a project in the current directory:

```bash
scout create-project-package -s .
```

This will create a zip file in the parent directory named after the current folder.

### Custom Output Path

Package a project and save it to a specific location:

```bash
scout create-project-package -s ./my-functions -o ./packages
```

This creates `packages/my-functions.zip`.

### Package and Upload to Assistant

Package a project and upload it to a Scout assistant:

```bash
scout create-project-package -s ./my-functions -u -a assistant_12345
```

If you have already set the `SCOUT_ASSISTANT_ID` in your environment (or .env file), you can omit the `-a` flag:

```bash
scout create-project-package -s ./my-functions -u
```

## Ignoring Files with .pkgignore

You can create a `.pkgignore` file in your project root to exclude files from the package. The format is similar to `.gitignore`:

```
# Example .pkgignore file
*.log
__pycache__/
.env
temp/
```

## Package Contents

The generated package will include:

1. All project files (excluding those matched by .pkgignore patterns)
2. A `functions.json` file containing definitions of all Scout functions in your project. This is generated automatically in the packaging process.

## How it Works

The package module:

1. Scans your source directory for all files
2. Filters out files based on .pkgignore patterns if present
3. Analyzes Python files to find Scout functions (@scout.function decorator)
4. Generates a functions.json with function definitions
5. Creates a zip package with all files and the functions.json
6. Optionally uploads the package to a Scout assistant

## Error Handling

The tool will fail with an error message if:
- The source path doesn't exist
- The output path doesn't exist
- You try to upload without specifying an assistant ID
- There are API errors during upload 