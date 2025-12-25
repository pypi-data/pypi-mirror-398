import asyncio
import os
import time
from typing import Any, Coroutine

import polib
from annotated_types import T


def run_in_current_event_loop(coro: Coroutine[Any, Any, T], max_retry=100):
    """
    Runs the given coroutine in the current event loop.

    Args:
        coro (Coroutine[Any, Any, T]): The coroutine to be run.
        max_retry (int, optional): The maximum number of retries to get the event loop. 1 equals to 0.1 second. Defaults to 100.

    Returns:
        T: The result of the coroutine.

    Raises:
        Exception: If failed to get the event loop after the maximum number of retries.
    """
    loop: asyncio.AbstractEventLoop | None = None
    while not loop:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            time.sleep(0.1)
            max_retry -= 1
            if max_retry == 0:
                raise Exception("Failed to get event loop")

    return loop.run_until_complete(coro)


def json_to_markdown(
    data: dict[str, Any],
    *,
    heading_level=1,
    newline_length=2,
    list_as_table=False,
    list_as_is=False,
    key="",
    configuration: dict[str, Any] | None = None,
):
    """
    Convert JSON data to markdown format.
    This function recursively converts a dictionary into a markdown string.

    Args:
        data (dict[str, Any]): The JSON data to convert.
        heading_level (int, optional): The heading level for the markdown. Can be set to start from higher levels. Also used internally for recursion. Defaults to 1.
        newline_length (int, optional): The number of newlines to add after each item. Defaults to 2.
        list_as_table (bool, optional): If True, the list of objects will be converted to a table. Defaults to False.
        list_as_is (bool, optional): If True, items in the list will be written as is without markdown formatting. Defaults to False.
        key (str, optional): The key of the current item. Used for recursion. Defaults to ''.
        configuration (dict[str, Any] | None, optional): A dictionary of configuration options for each key in the JSON data. Defaults to None. Configuration's value is passed to the function as keyword arguments.

    Returns:
        str: The converted markdown string.

    Example:
    ```python
    data = {
        "key1": "value1",
        "key2": {
            "key3": "value3",
            "key4": ["item1", "item2"],
        },
    }

    markdown = json_to_markdown(data)
    print(markdown)

    # Output:
    # # key1
    # value1
    # ## key2
    # ### key3
    # value3
    # ### key4
    # - item1
    # - item2
    ```
    """
    configuration = configuration or {}
    content = ""
    if isinstance(data, dict):
        if heading_level > 6:
            raise ValueError("Heading level cannot be greater than 6.")

        for key, value in data.items():
            content += f"{'#' * heading_level}"
            content += f" {key}"
            content += "\n" * newline_length
            content += json_to_markdown(
                value,
                heading_level=heading_level + 1,
                newline_length=newline_length,
                key=key,
                configuration=configuration,
                **configuration.get(key, {}),
            )
    elif isinstance(data, list):
        if list_as_table:
            if not data:
                return content

            keys = data[0].keys()
            content += "| " + " | ".join(keys) + " |\n"
            content += "| " + " | ".join(["---"] * len(keys)) + " |\n"
            for item in data:
                content += "| " + " | ".join([str(item[key]) for key in keys]) + " |\n"
            content += "\n" * (newline_length - 1)
        else:
            for item in data:
                if isinstance(item, dict):
                    content += json_to_markdown(
                        item,
                        heading_level=heading_level + 1,
                        newline_length=newline_length,
                        configuration=configuration,
                        **configuration.get(key, {}),
                    )
                else:
                    content += ("- " if not list_as_is else "") + json_to_markdown(
                        item,
                        heading_level=heading_level + 1,
                        newline_length=newline_length,
                        configuration=configuration,
                        **configuration.get(key, {}),
                    )
    else:
        content += f"{data}{'\n' * newline_length}"
    return content


def merge_pot_files(pot_files: list[str], output_path: str):
    """
    Merges multiple .pot files into a single .pot file while preserving header information from the first file.

    This function:
    - Loads the first .pot file to use as a base, ensuring that its header is preserved.
    - Iterates over the remaining .pot files.
    - Adds comment for the file source for the first entry of each subsequent .pot file.
    - Appends any translation entries not already present in the base file.
    - Merges source references (occurrences) for entries that already exist in the base file to include unique locations.

    Args:
        pot_files (list[str]): A list of file paths pointing to .pot files that need to be merged.
        output_path (str): The file path where the merged .pot file will be saved.

    Returns:
        None
    """
    base = polib.pofile(pot_files[0])  # use first file to preserve header

    for pot_path in pot_files[1:]:
        pot = polib.pofile(pot_path)
        first_entry = True
        for entry in pot:
            if first_entry:
                # Add label where the file coming from
                relative_path = os.path.relpath(
                    pot_path, start=os.path.dirname(output_path)
                )
                entry.comment = f"File: {relative_path}"
                first_entry = False

            existing = base.find(entry.msgid)
            if not existing:
                base.append(entry)
            else:
                # Optionally merge source refs
                existing.occurrences = list(
                    set(existing.occurrences + entry.occurrences)
                )

    base.save(output_path)
