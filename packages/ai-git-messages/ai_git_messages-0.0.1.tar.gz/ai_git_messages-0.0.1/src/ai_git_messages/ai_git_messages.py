#!/usr/bin/env python3

import os
import sys
from typing import Literal, Optional
from ollama import chat
from anthropic import Anthropic
from pydantic import BaseModel, ValidationError
import subprocess
from rich.console import Console
from rich.text import Text
from rich.json import JSON
from rich.prompt import Prompt, Confirm
import json
import time
import subprocess
from enum import Enum, auto
import argparse
from argparse import BooleanOptionalAction
import tempfile
import logging
from importlib.metadata import version, PackageNotFoundError
from curvpyutils.logging import configure_rich_root_logger
from curvpyutils.cli_util import VerbosityActionGroupFactory

log = logging.getLogger(__name__)
console = Console(stderr=True)

class AiSource(Enum):
    OLLAMA = "ollama"
    CURSOR = "cursor"
    CLAUDE = "claude"
    DEBUG = "debug"

class OutputType(Enum):
    BRANCH_OFF_FROM_MAIN_ARGUMENTS = "branch_off_main"
    PR_DESCRIPTION = "pr_description"

    @property
    def desc(self) -> str:
        return {
            OutputType.BRANCH_OFF_FROM_MAIN_ARGUMENTS: "branch off from main arguments",
            OutputType.PR_DESCRIPTION: "pull request description",
        }[self]

class PRDescription(BaseModel):
    title: str
    body: str

    def __str__(self) -> str:
        return f"Title:\n{self.title}\nBody:\n{self.body}"

    def __rich__(self) -> Text:
        title_text = Text(self.title, style="bold")
        body_text: list[Text] = []
        for ln in self.body.split("\n"):
          body_text.append(Text('  '))
          body_text.append(Text(ln, style="bold"))
          body_text.append(Text("\n"))
        t = Text.assemble(
          "Title:",
          title_text, 
          "\n", 
          "Body:\n",
          *body_text,
        )
        return t

    def __repr__(self) -> str:
        return f"PRDescription(title={self.title}, body={self.body})"

    def to_json(self) -> str:
        return json.dumps(self.model_dump(), indent=4)

class ChangesOnMainDescription(BaseModel):
    feat_or_fix: Literal["feat", "fix"]
    branch_name: str
    commit_message: str

    def __str__(self) -> str:
        return f"Feature or fix:\n{self.feat_or_fix}\nBranch name:\n{self.branch_name}\nCommit message:\n{self.commit_message}"

    def __rich__(self) -> Text:
        return Text.assemble(
          "Feature or fix:",
          Text(self.feat_or_fix, style="bold"),
          "\n", 
          "Branch name:",
          Text(self.branch_name, style="bold"),
          "\n", 
          "Commit message:",
          Text(self.commit_message, style="bold"),
        )

    def __repr__(self) -> str:
        return f"ChangesOnMainDescription(feat_or_fix={self.feat_or_fix}, branch_name={self.branch_name}, commit_message={self.commit_message})"

    def to_json(self) -> str:
        return json.dumps(self.model_dump(), indent=4)

def get_changes_on_main() -> str:
    ChangeType = Literal["added", "modified", "deleted", "renamed"]
    
    spacer_str = "=" * 80

    class Change(BaseModel):
        file: str
        action: ChangeType
        diff: Optional[str]
        file_contents: Optional[str]
    
        def get_prompt_fragment(self) -> str:
            """
            Returns a string that can be used as part of a prompt to describe the change.
            """
            class SpacerType(Enum):
                BEGIN_DIFF = "BEGIN DIFF"
                END_DIFF = "END DIFF"
                BEGIN_FILE_CONTENTS = "BEGIN FILE CONTENTS"
                END_FILE_CONTENTS = "END FILE CONTENTS"

            get_begin_spacer_line = lambda filename, spacer_type: ("-" * 20)+f" {spacer_type}: {filename} "+("-" * 20)+"\n" # noqa: E731
            get_end_spacer_line = lambda filename, spacer_type: ("-" * 20)+f" {spacer_type}: {filename} "+("-" * 20)+"\n" # noqa: E731
            
            diff_str = f"{get_begin_spacer_line(self.file, SpacerType.BEGIN_DIFF.value)}{self.diff if self.diff else '<diff unavailable>'}\n{get_end_spacer_line(self.file, SpacerType.END_DIFF.value)}\n"
            file_contents_str = f"{get_begin_spacer_line(self.file, SpacerType.BEGIN_FILE_CONTENTS.value)}{self.file_contents if self.file_contents else '<file contents unavailable>'}\n{get_end_spacer_line(self.file, SpacerType.END_FILE_CONTENTS.value)}\n"
            
            s = f"Change: '{self.file}' was {self.action}\n"
            if self.action in ["modified"]:
                s += f"Diff of the {self.action} file '{self.file}':\n"
                s += diff_str
                s += f"Complete contents of the {self.action} file '{self.file}':\n"
                s += file_contents_str
            elif self.action in ["deleted"]:
                s += f"Complete contents of the {self.action} file '{self.file}' in patch format:\n"
                s += diff_str
            elif self.action in ["renamed", "added"]:
                s += f"Complete contents of the {self.action} file '{self.file}':\n"
                s += file_contents_str
            return s
    
    def get_all_changes_on_current_branch() -> list[Change]:
        """
        Returns a list of Change objects that represent the changes on the current branch,
        including files added, modified, deleted, and renamed.
        """

        #
        # Helper function to generate a list of Change objects for a given action.
        #
        def mk_change_list(generate_list_cmd: list[str], diff_cmd: Optional[list[str]], action: ChangeType) -> list[Change]:
            """
            Helper function to generate a list of Change objects representing all changes on the current branch

            Args:
                generate_list_cmd: the command that will generate a list of file paths
                diff_cmd: the command that will generate a diff for each given file path, 
                    or None if the diff is not desired in the Change object
                action: what to set the action field to in the Change object

            Returns:
                a list of Change objects
            """
            ret_list = []
            p = subprocess.run(
                generate_list_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.getcwd(),
            )
            file_names_list = p.stdout.strip().split("\n")
            for f in file_names_list:
                if diff_cmd:
                    p2 = subprocess.run(
                        diff_cmd + [f],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        cwd=os.getcwd(),
                    )
                    diff = p2.stdout.strip()
                else:
                    diff = None
                p3 = subprocess.run(
                    ["cat", f],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=os.getcwd(),
                )
                file_contents = p3.stdout.strip()
                ret_list.append(Change(file=f, action=action, diff=diff, file_contents=file_contents))
            return ret_list

        #
        # generate lists of changes of each type
        #
        untracked_files_added = mk_change_list(
            ["git", "ls-files", "--others", "--exclude-standard"],
            # each file name will be appended to the end of this command
            ["git", "diff", "--"],
            "added",
        )
        tracked_files_modified = mk_change_list(
            ["git", "diff", "--name-only"],
            # each file name will be appended to the end of this command
            ["git", "diff", "--"],
            "modified",
        )
        tracked_files_deleted = mk_change_list(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=D"],
            # each file name will be appended to the end of this command
            ["git", "diff", "--cached", "--diff-filter=D", "--"],
            "deleted",
        )
        tracked_files_renamed = mk_change_list(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=R"],
            None,
            "renamed",
        )
        return untracked_files_added + tracked_files_modified + tracked_files_deleted + tracked_files_renamed

    #
    # get the changes on the current branch which is presumed to be main
    #
    changes: list[Change] = get_all_changes_on_current_branch()
    ret_str = f"{spacer_str}\n"
    for c in changes:
        ret_str += c.get_prompt_fragment() + f"{spacer_str}\n"
    return ret_str

def get_changes_on_branch() -> str:
    ret_str = ""
    for cmd in [
      ["git", "log", "main..HEAD"],
      ["git", "diff", "main..HEAD"],
    ]:
      p = subprocess.run(
          cmd,
          stdout=subprocess.PIPE,
          stderr=subprocess.PIPE,
          text=True,
          cwd=os.getcwd(),
      )
      if p.returncode not in (0, None):
          console.log(f"Error: {p.stderr}", style="red bold", end="\n\n")
          sys.exit(p.returncode)
          #raise subprocess.CalledProcessError(p.returncode, p.args, p.stderr)
      ret_str += p.stdout.strip() + "\n"
    return ret_str

def get_prompt(output_type: OutputType, verbose: bool = False) -> str:
    if output_type == OutputType.BRANCH_OFF_FROM_MAIN_ARGUMENTS:
        prompt = """
You are a helpful assistant that generates git branch names and commit messages based on the provided 
changes that have been made to this branch.  Read through the changes and select the most appropriate 
values for these three fields:
 - "feat_or_fix": this field should be set to "feat" if the changes represent a new feaeture, 
 or "fix" if the changes represent a bug fix. Those are the only two valid values for this field.
 - "branch_name": a short, descriptive name for the new branch that I will checkout with the changes 
 described below. The branch name should be a hyphen-separated string of 5 or fewer words describing the 
 changes.
 - "commit_message": a short, descriptive commit message that describes the changes you'll see below.

Requirements:
- Your final response should be a JSON object with three string fields: "feat_or_fix", "branch_name", and "commit_message".
- Your final response should contain no other text.

Below is a list of every changed files and what has changed. Where possible, the entire contents of the
file plus the diffs are provided to help you understand what change was made.

{changes}
""".format(changes=get_changes_on_main())
    elif output_type == OutputType.PR_DESCRIPTION:
        prompt = """
You are a helpful assistant that generates a pull request description based on the provided changes.

Requirements:
- Your final response should be a JSON object with two string fields: "title" and "body".
- Your final response should contain no other text.
- The --body portion may contain ascii \n to indicate where newlines should go.
- The --body portion should be a bullet Markdown list of changes.
- The title should be succient and general, not a list of changes. Try to sum of all the changes in a single phrase like ("improved scripts" or "added feature X")

Here are the changes:

{changes}
""".format(changes=get_changes_on_branch())
    else:
        raise ValueError(f"Invalid output type: {output_type}")
    return prompt

def cursor_generate(output_type: OutputType, verbose: bool = False) -> str:
    prompt = get_prompt(output_type, verbose)
    if verbose:
        console.log("Prompt:", style="bold")
        console.log(prompt, highlight=True, end="\n\n")
        # time.sleep(1) # this is for the logger to print a new time stamp
        console.log(f"Using cursor-agent to generate {output_type.desc}...", end="\\n\\n")

    p = subprocess.run(
        ["cursor-agent", "-p", "--output-format", "json", "--approve-mcps"],
        input=prompt,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=os.getcwd(),
    )
    if p.returncode not in (0, None):
        console.log(f"Error: {p.stderr}", style="red bold", end="\n\n")
        sys.exit(p.returncode)
        #raise subprocess.CalledProcessError(p.returncode, p.args, p.stderr)
    response_json = json.loads(p.stdout.strip())
    s = response_json["result"]
    # slice anything preceding the first "```json"
    s = s.split("```json")[1]
    # slice anything following the last "```"
    s = s.split("```")[0]
    return s

def ollama_generate(output_type: OutputType, verbose: bool = False) -> str:
    prompt = get_prompt(output_type)
    if verbose:
        console.log("Prompt:", style="bold")
        console.log(prompt, highlight=True, end="\n\n")
        # time.sleep(1) # this is for the logger to print a new time stamp
        console.log(f"Using ollama (gpt-oss) to generate {output_type.desc}...", end="\\n\\n")

    response = chat(
        messages=[
        {
            'role': 'user',
            'content': prompt,
        }
        ],
        model='gpt-oss',
        format=PRDescription.model_json_schema() if output_type == OutputType.PR_DESCRIPTION else ChangesOnMainDescription.model_json_schema(),
    )
    if verbose:
        console.log("Response:", style="bold")
        console.log(response.message.content, highlight=True, end="\\n\\n")
    resp = response.message.content
    return resp

def claude_generate(output_type: OutputType, verbose: bool = False) -> str:
    prompt = get_prompt(output_type)
    if verbose:
        console.log("Prompt:", style="bold")
        console.log(prompt, highlight=True, end="\n\n")
        # time.sleep(1) # this is for the logger to print a new time stamp
        console.log(f"Using Claude to generate {output_type.desc}...", end="\\n\\n")

    client = Anthropic()

    # Determine which schema to use
    schema = PRDescription.model_json_schema() if output_type == OutputType.PR_DESCRIPTION else ChangesOnMainDescription.model_json_schema()

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=8192,
        messages=[
            {
                'role': 'user',
                'content': prompt,
            }
        ],
        temperature=0.0,
    )

    if verbose:
        console.log("Response:", style="bold")
        console.log(response.content[0].text, highlight=True, end="\\n\\n")

    resp = response.content[0].text
    return resp

def validate_resp_str_and_return_json_str(resp_str: str, output_type: OutputType, verbose: bool = False) -> str:
    """
    Converts the response from the model into a JSON string.

    Args:
        resp_str: the response from the model as a string
        output_type: the type of output to convert the response to a JSON string for

    Returns:
        the JSON string
    """
    s: str | None = None
    try:
        if output_type == OutputType.PR_DESCRIPTION:
            pr_desc = PRDescription.model_validate_json(resp_str)
            if verbose:
                console.log("Pull Request Description:", style="bold")
                console.log(pr_desc, highlight=True, end="\\n\\n")
            s = pr_desc.to_json()
        elif output_type == OutputType.BRANCH_OFF_FROM_MAIN_ARGUMENTS:
            changes_on_main = ChangesOnMainDescription.model_validate_json(resp_str)
            if verbose:
                console.log("Branch off from main arguments:", style="bold")
                console.log(changes_on_main, highlight=True, end="\\n\\n")
            s = changes_on_main.to_json()
        else:
            raise ValueError(f"Invalid output type: {output_type}")
            s = None
    except ValidationError as e:
        console.log(f"Validation error: {e}", style="red bold", end="")
        s = None
    return s

def parse_args() -> tuple[AiSource, OutputType, bool]:
    parser = argparse.ArgumentParser(description="Generate a pull request description or `git branch-off` arguments based on analysis of the current branches changes.")

    # Add version argument
    try:
        pkg_version = version("ai-git-messages")
    except PackageNotFoundError:
        pkg_version = "unknown (not installed)"

    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"%(prog)s {pkg_version}"
    )

    ai_source_group = parser.add_argument_group("engine choices")
    ai_source_mutex_group = ai_source_group.add_mutually_exclusive_group()
    ai_source_mutex_group.add_argument("--ollama", "-o", dest="ai_source", action="store_const", const=AiSource.OLLAMA, help="use the Ollama AI agent")
    ai_source_mutex_group.add_argument("--cursor", "-c", dest="ai_source", action="store_const", const=AiSource.CURSOR, help="use the Cursor AI agent (default)")
    ai_source_mutex_group.add_argument("--claude", "-k", dest="ai_source", action="store_const", const=AiSource.CLAUDE, help="use the Claude AI agent")
    ai_source_mutex_group.add_argument("--debug-mode", "-D", dest="ai_source", action="store_const", const=AiSource.DEBUG, help="use the debug mode")
    parser.set_defaults(ai_source=AiSource.CURSOR)

    parser.add_argument("--editable", '-e', action="store_true", default=False, help="allow the user to edit the generated response (default: %(default)s)")
    
    output_type_group = parser.add_argument_group("output type choices")
    output_type_mutex_group = output_type_group.add_mutually_exclusive_group()
    output_type_mutex_group.add_argument("--pr-description", "-p", dest="output_type", action="store_const", const=OutputType.PR_DESCRIPTION, help="generate a pull request description (default)")
    output_type_mutex_group.add_argument("--branch-off-main", "-b", dest="output_type", action="store_const", const=OutputType.BRANCH_OFF_FROM_MAIN_ARGUMENTS, help="generate `git branch-off` arguments")
    parser.set_defaults(output_type=OutputType.PR_DESCRIPTION)

    VerbosityActionGroupFactory(
        parser, 
        quiet_flags=['--quiet', '-q'],
        verbose_flags=['--verbose', '-v'], 
        debug_flags=['--debug', '-d'], 
        MAX_VERBOSITY=3
    ).add_verbosity_group()

    args = parser.parse_args()

    return args

def run_model(ai_source: AiSource, output_type: OutputType, verbose: bool = False) -> str:
    if verbose:
        console.log(f"run_model:\n  ai_source='{ai_source}'\n  output type='{output_type}'\n  verbose='{verbose}'", end="\\n\\n")

    if ai_source == AiSource.OLLAMA:
        console.log(f"Using ollama (gpt-oss) to generate {output_type.desc}...", end="\\n\\n")
        resp_str = ollama_generate(output_type, verbose)
    elif ai_source == AiSource.CURSOR:
        console.log(f"Using cursor-agent to generate {output_type.desc}...", end="\\n\\n")
        resp_str = cursor_generate(output_type, verbose)
    elif ai_source == AiSource.CLAUDE:
        console.log(f"Using Claude to generate {output_type.desc}...", end="\\n\\n")
        resp_str = claude_generate(output_type, verbose)
    elif ai_source == AiSource.DEBUG:
        if output_type == OutputType.PR_DESCRIPTION:
            console.log(f"Using hardcoded {output_type.desc}...", end="\\n\\n")
            resp_obj = {
                "title":"Add git-branch script and clean Makefile output",
                "body":"- Replaced emoticons in Makefile fetch-latest-tags and publish status messages with plain text symbols.\n- Extracted the git-branch, commit, and push workflow into a new script `scripts/git-branch-add-commit-push.sh`.\n- Removed the temporary `push` rule from the Makefile.\n- Updated the script to validate arguments, ensure `git-extras` is installed, and provide a help message.\n- Added prompts for commit message and optional push confirmation.",
            }
        elif output_type == OutputType.BRANCH_OFF_FROM_MAIN_ARGUMENTS:
            console.log(f"Using hardcoded {output_type.desc}...", end="\\n\\n")
            resp_obj = {
                "feat_or_fix":"feat",
                "branch_name":"add-auth-tokens",
                "commit_message":"Add auth tokens to the Makefile",
            }
        else:
            raise ValueError(f"Invalid output type: {output_type}")
        resp_str = json.dumps(resp_obj)
    else:
        raise ValueError(f"Invalid AI source: {ai_source}")

    # validate the response
    s = validate_resp_str_and_return_json_str(resp_str, output_type, verbose)
    if s is None:
        console.log("Validation failed", style="red bold", end="\n\n")
        return None
    return s

def run_editor(path: str) -> None:
    import shlex

    # VISUAL > EDITOR > fallback
    editor = (
        os.environ.get("VISUAL")
        or os.environ.get("EDITOR")
        or "vi"
    )

    # $EDITOR might be "vim -u NONE" etc.
    cmd = shlex.split(editor) + [path]

    # Attach editor I/O directly to the controlling terminal
    tty_fd = os.open("/dev/tty", os.O_RDWR)
    try:
        subprocess.run(
            cmd,
            check=True,
            stdin=tty_fd,
            stdout=tty_fd,
            stderr=tty_fd,
            # commented out b/c setting to False is a bit dubious here; 
            #   however, it would only matter if we had fd's besides 0/1/2
            #   in this program (sockets, pipes, files, etc.):
            # close_fds=False,
        )
    finally:
        os.close(tty_fd)

def edit_json_str(json_str: str) -> Optional[str]:
    """
    Edits the given JSON string in a text editor.
    """
    updated_json_str: Optional[str] = None
    try:
        f = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        f.write(json_str.encode())
        f.flush()
        run_editor(f.name)
        with open(f.name, "r") as f:
            updated_json_str = f.read()
        if updated_json_str is None:
            console.log("Edit failed", style="red bold", end="\n\n")
            return None
        else:
            resp_obj = json.loads(updated_json_str)
            return json.dumps(resp_obj, indent=4)
    except Exception as e:
        console.log(f"Error: {e}", style="red bold", end="")
        return None
    finally:
        if f is not None:
            f.close()
        if os.path.exists(f.name):
            os.unlink(f.name)

def main():
    args = parse_args()
    configure_rich_root_logger(args.verbosity)

    try:
        s = run_model(args.ai_source, args.output_type, args.verbose)
        if s is None:
            raise ValueError("run_model returned nothing")
    except Exception as e:
        log.exception(e, exc_info=True)
        sys.exit(1)

    if args.verbose:
        console.log(f"writing to stdout:", style="bold", end="")
        console.log(JSON(s), highlight=True, end="\\n\\n")

    while args.editable: # equiv to 'while True', or else don't loop at all
        s = edit_json_str(s)
        if s is None:
            again = Confirm.ask(
                "Try again?", 
                choices=["y", "N"], 
                default="n",
                show_choices=False,
                show_default=False,
                case_sensitive=False)
            if again:
                continue
            else:
                sys.exit(1)
        else:
            if args.verbose:
                console.log(f"post-edit response going to stdout:", style="bold", end="")
                console.log(JSON(s), highlight=True, end="\\n\\n")
            break
    
    if s is None:
        log.critical("Unable to generate valid output")
        sys.exit(1)

    # emit the JSON directly to stdout
    print(s)
    sys.exit(0)

if __name__ == "__main__":
    main()