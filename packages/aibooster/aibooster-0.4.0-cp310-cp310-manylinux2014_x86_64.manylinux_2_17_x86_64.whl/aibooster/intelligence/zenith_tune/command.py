import os
import re
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple

from .distributed import get_rank


def _command_split(command: str) -> List[str]:
    """Split command string preserving quotes and handling various quote types.

    Handles:
    - Double quotes (")
    - Single quotes (')
    - Backticks (`)
    - Command substitution $()
    - Escape sequences
    - Nested quotes
    """
    args = []
    current_arg = []
    i = 0

    while i < len(command):
        char = command[i]

        # Skip whitespace between arguments
        if char.isspace() and not current_arg:
            i += 1
            continue

        # End of argument on unquoted whitespace
        if (
            char.isspace()
            and current_arg
            and not any(current_arg[0] == q for q in ['"', "'", "`"])
        ):
            args.append("".join(current_arg))
            current_arg = []
            i += 1
            continue

        # Handle escape sequences
        if char == "\\" and i + 1 < len(command):
            current_arg.append(char)
            current_arg.append(command[i + 1])
            i += 2
            continue

        # Handle quotes
        if char in ['"', "'", "`"] and (
            not current_arg or i == 0 or command[i - 1] != "\\"
        ):
            quote_char = char
            current_arg.append(char)
            i += 1

            # Find matching quote
            while i < len(command):
                if command[i] == "\\" and i + 1 < len(command):
                    current_arg.append(command[i])
                    current_arg.append(command[i + 1])
                    i += 2
                elif command[i] == quote_char:
                    current_arg.append(command[i])
                    i += 1
                    break
                else:
                    current_arg.append(command[i])
                    i += 1

            # Check if this completes the argument
            if i < len(command) and command[i].isspace():
                args.append("".join(current_arg))
                current_arg = []
                i += 1
            continue

        # Handle command substitution $()
        if char == "$" and i + 1 < len(command) and command[i + 1] == "(":
            current_arg.append(char)
            current_arg.append("(")
            i += 2
            paren_count = 1

            # Find matching parenthesis
            while i < len(command) and paren_count > 0:
                if command[i] == "\\" and i + 1 < len(command):
                    current_arg.append(command[i])
                    current_arg.append(command[i + 1])
                    i += 2
                elif command[i] == "(":
                    paren_count += 1
                    current_arg.append(command[i])
                    i += 1
                elif command[i] == ")":
                    paren_count -= 1
                    current_arg.append(command[i])
                    i += 1
                else:
                    current_arg.append(command[i])
                    i += 1
            continue

        # Regular character
        current_arg.append(char)
        i += 1

    # Don't forget the last argument
    if current_arg:
        args.append("".join(current_arg))

    return args


class OptionFormat(Enum):
    """Enum for different option formats."""

    EQUALS = "equals"  # Example: --key=value
    SPACE = "space"  # Example: --key value
    KEYVALUE = "keyvalue"  # Example: --env KEY1=value1 KEY2=value2
    FLAG = "flag"  # Example: --verbose


@dataclass
class Option:
    """Represents a command-line option."""

    key: str
    value: Optional[str] = None
    format: OptionFormat = OptionFormat.FLAG

    def __post_init__(self):
        if self.value is None and self.format != OptionFormat.FLAG:
            raise ValueError(f"Non-flag option must have a value: {self.key}")

        # Normalize empty string to quoted empty string
        if self.value == "":
            self.value = "''"


class OptionHandler(ABC):
    """Abstract base class for option handlers."""

    @abstractmethod
    def can_handle(self, option: Option) -> bool:
        """Check if this handler can handle the given option."""
        pass

    @abstractmethod
    def append(self, args: List[str], option: Option) -> List[str]:
        """Append an option to the argument list."""
        pass

    @abstractmethod
    def update(self, args: List[str], option: Option) -> List[str]:
        """Update an option in the argument list."""
        pass

    @abstractmethod
    def remove(self, args: List[str], key: str) -> List[str]:
        """Remove an option from the argument list."""
        pass


class CommandBuilder:
    """Improved command builder with better separation of concerns."""

    def __init__(self, command: str = ""):
        self._args = _command_split(command) if command else []
        self._handlers = self._create_handlers()

    def _create_handlers(self) -> List[OptionHandler]:
        """Create option handlers."""
        return [
            EqualsHandler(),
            SpaceHandler(),
            KeyValueHandler(),
            FlagHandler(),
        ]

    def _find_handler(self, option: Option) -> OptionHandler:
        """Find appropriate handler for the option."""
        for handler in self._handlers:
            if handler.can_handle(option):
                return handler
        raise ValueError(f"No handler found for option: {option}")

    def update(self, option: str) -> "CommandBuilder":
        """Update an option."""
        key, value, format = self._parse_option_string(option)

        # Get existing format and check compatibility
        existing_format = self._detect_format(key)

        if existing_format:
            if existing_format == OptionFormat.FLAG and value:
                raise ValueError(
                    "Invalid option format: cannot update flag format option"
                )
            elif existing_format != OptionFormat.FLAG and existing_format != format:
                raise ValueError(
                    f"Invalid option format: cannot mix {existing_format.value} and {format.value} formats"
                )
            target_format = existing_format
        else:
            # If option doesn't exist, use the detected format from parsing
            target_format = format

        option_obj = Option(key, value, target_format)
        handler = self._find_handler(option_obj)
        self._args = handler.update(self._args, option_obj)
        return self

    def append(self, option: str) -> "CommandBuilder":
        """Append an option (allows duplicates)."""
        key, value, format = self._parse_option_string(option)

        option_obj = Option(key, value, format)
        handler = self._find_handler(option_obj)
        self._args = handler.append(self._args, option_obj)
        return self

    def remove(self, option: str) -> "CommandBuilder":
        """Remove an option."""
        format = self._detect_format(option)
        if format:
            handler = self._find_handler_by_format(format)
            self._args = handler.remove(self._args, option)
        return self

    def _find_handler_by_format(self, format: OptionFormat) -> OptionHandler:
        """Find handler by format type."""
        for handler in self._handlers:
            if handler.can_handle(
                Option(
                    "dummy", None if format == OptionFormat.FLAG else "dummy", format
                )
            ):
                return handler
        raise ValueError(f"No handler found for format: {format}")

    def _parse_option_string(
        self, option: str
    ) -> Tuple[str, Optional[str], OptionFormat]:
        """Parse option string to extract key, value, and format."""
        # Parse the option using command_split to handle quotes properly
        parts = _command_split(option)

        # Check for equals format first (e.g., "--key=value")
        if "=" in option and (len(parts) == 1 or "=" in parts[0]):
            key, value = option.split("=", 1)
            return key, value, OptionFormat.EQUALS
        # Check for space-separated key=value format (e.g., "--option key=value")
        elif len(parts) >= 2 and "=" in parts[1]:
            key = parts[0]
            value = " ".join(parts[1:])  # Join all values
            return key, value, OptionFormat.KEYVALUE
        # Check for space-separated format (e.g., "--key value" or "--key value1 value2")
        elif len(parts) >= 2:
            key = parts[0]
            value = " ".join(parts[1:])  # Join all values
            return key, value, OptionFormat.SPACE
        # Flag format (e.g., "--verbose")
        elif len(parts) == 1 and parts[0].startswith("-"):
            key = parts[0]
            return key, None, OptionFormat.FLAG
        # Invalid format
        else:
            raise ValueError(f"Invalid option format: '{option}'")

    def _detect_format(self, option: str) -> Optional[OptionFormat]:
        """Detect the format of an existing option."""
        # Handle keyvalue format with target key (e.g., "--env TARGET_KEY")
        option_parts = option.split(None, 1)
        if len(option_parts) == 2:
            key, _ = option_parts
        else:
            key = option

        for i, arg in enumerate(self._args):
            if arg.startswith(key + "="):
                return OptionFormat.EQUALS

            if arg != key:
                continue

            # Found the key, check what follows
            if i + 1 >= len(self._args):
                return OptionFormat.FLAG

            next_arg = self._args[i + 1]
            if next_arg.startswith("-"):
                return OptionFormat.FLAG
            elif "=" in next_arg:
                return OptionFormat.KEYVALUE
            else:
                return OptionFormat.SPACE

        return None

    def get_command(self) -> str:
        """Get the command string."""
        return " ".join(self._args)

    def __str__(self) -> str:
        return self.get_command()

    def staging_directory(
        self, old_path: str, new_path: str, copy_files: bool = False
    ) -> "CommandBuilder":
        """
        Replace directory paths in command and optionally copy directory for distributed training.

        Args:
            old_path: Path to replace in the command
            new_path: New path to use in the command
            copy_files: Whether to actually copy the directory (default: False)

        Returns:
            CommandBuilder instance for method chaining

        Raises:
            FileNotFoundError: If old_path doesn't exist and copy_files is True
            NotADirectoryError: If old_path is not a directory and copy_files is True
            OSError: If copying fails
        """
        # Replace paths in command arguments with path boundary consideration
        original_args = self._args[:]
        self._args = [
            self._replace_path_safely(arg, old_path, new_path) for arg in self._args
        ]

        # Only copy if replacement actually occurred and copy_files is True
        if copy_files and self._args != original_args:
            self._validate_and_copy_directory(old_path, new_path)

        return self

    def _replace_path_safely(self, arg: str, old_path: str, new_path: str) -> str:
        """Replace path considering path boundaries to avoid partial matches."""
        # Use regex to ensure we only replace full paths, not partial matches
        # The pattern matches old_path followed by either '/' or end of string
        pattern = re.escape(old_path) + r"(?=/|$)"
        return re.sub(pattern, new_path, arg)

    def _validate_and_copy_directory(self, old_path: str, new_path: str) -> None:
        """Validate source directory and copy if rank 0."""
        if not os.path.exists(old_path):
            raise FileNotFoundError(f"Source path does not exist: {old_path}")

        if not os.path.isdir(old_path):
            raise NotADirectoryError(f"Source path is not a directory: {old_path}")

        # Only rank 0 performs the copy operation for distributed training
        if get_rank() == 0:
            try:
                shutil.copytree(old_path, new_path, dirs_exist_ok=True)
            except OSError as e:
                raise OSError(
                    f"Failed to copy directory from {old_path} to {new_path}: {e}"
                )


# Concrete handlers
class EqualsHandler(OptionHandler):
    """Handler for --key=value format."""

    def can_handle(self, option: Option) -> bool:
        return option.format == OptionFormat.EQUALS

    def append(self, args: List[str], option: Option) -> List[str]:
        return args + [f"{option.key}={option.value}"]

    def update(self, args: List[str], option: Option) -> List[str]:
        new_args = []
        updated = False
        key_prefix = option.key + "="

        for arg in args:
            if arg.startswith(key_prefix):
                new_args.append(f"{option.key}={option.value}")
                updated = True
            else:
                new_args.append(arg)

        if not updated:
            new_args.append(f"{option.key}={option.value}")

        return new_args

    def remove(self, args: List[str], key: str) -> List[str]:
        return [arg for arg in args if not arg.startswith(key + "=")]


class SpaceHandler(OptionHandler):
    """Handler for --key value format."""

    def can_handle(self, option: Option) -> bool:
        return option.format == OptionFormat.SPACE

    def append(self, args: List[str], option: Option) -> List[str]:
        existing_key_index = self._find_existing_key(args, option.key)
        if existing_key_index is not None:
            return self._append_to_existing(args, option, existing_key_index)
        else:
            return self._append_as_new(args, option)

    def _find_existing_key(self, args: List[str], key: str) -> Optional[int]:
        """Find the index of an existing key that has values."""
        for i, arg in enumerate(args):
            if arg == key and i + 1 < len(args):
                return i
        return None

    def _find_value_range_end(self, args: List[str], start_index: int) -> int:
        """Find the end index of values for a key."""
        i = start_index
        while i < len(args) and not args[i].startswith("-"):
            i += 1
        return i

    def _append_to_existing(
        self, args: List[str], option: Option, key_index: int
    ) -> List[str]:
        """Append value to existing key."""
        value_start = key_index + 1
        value_end = self._find_value_range_end(args, value_start)

        # Parse new values (quotes preserved by _command_split)
        quoted_new_parts = _command_split(option.value)

        # Build result with existing values quoted if needed
        new_args = args[:value_start]  # Keep up to the key

        # Quote existing values
        for value in args[value_start:value_end]:
            if value == "":
                new_args.append('""')
            elif " " in value and not (
                (value.startswith("'") and value.endswith("'"))
                or (value.startswith('"') and value.endswith('"'))
            ):
                new_args.append(f'"{value}"')
            else:
                new_args.append(value)

        # Add new quoted values
        new_args.extend(quoted_new_parts)
        # Add remaining args
        new_args.extend(args[value_end:])

        return new_args

    def _append_as_new(self, args: List[str], option: Option) -> List[str]:
        """Add option as new key-value pair."""
        quoted_parts = _command_split(option.value)
        return args + [option.key] + quoted_parts

    def update(self, args: List[str], option: Option) -> List[str]:
        new_args = []
        updated = False
        i = 0

        while i < len(args):
            if args[i] == option.key and not updated:
                # Add the key and new value
                new_args.extend([option.key, option.value])
                updated = True
                i += 1
                # Skip all subsequent non-option arguments
                while i < len(args) and not args[i].startswith("-"):
                    i += 1
            else:
                new_args.append(args[i])
                i += 1

        if not updated:
            new_args.extend([option.key, option.value])

        return new_args

    def remove(self, args: List[str], key: str) -> List[str]:
        new_args = []
        skip_next = False

        for i, arg in enumerate(args):
            if skip_next:
                skip_next = False
                continue

            if arg == key and i + 1 < len(args):
                skip_next = True
                continue

            new_args.append(arg)

        return new_args


class FlagHandler(OptionHandler):
    """Handler for --flag format."""

    def can_handle(self, option: Option) -> bool:
        return option.format == OptionFormat.FLAG

    def append(self, args: List[str], option: Option) -> List[str]:
        return args + [option.key]

    def update(self, args: List[str], option: Option) -> List[str]:
        if option.key not in args:
            return args + [option.key]
        return args

    def remove(self, args: List[str], key: str) -> List[str]:
        return [arg for arg in args if arg != key]


class KeyValueHandler(OptionHandler):
    """Handler for --key key1=value1 key2=value2 format."""

    def can_handle(self, option: Option) -> bool:
        return option.format == OptionFormat.KEYVALUE

    def append(self, args: List[str], option: Option) -> List[str]:
        existing_option_index = self._find_existing_keyvalue_option(args, option.key)
        if existing_option_index is not None:
            args = args[:]  # Create a copy to avoid modifying the original
            value_index = existing_option_index + 1
            existing_values = args[value_index]
            args[value_index] = f"{existing_values} {option.value}"
            return args
        else:
            return args + [option.key, option.value]

    def _find_existing_keyvalue_option(
        self, args: List[str], key: str
    ) -> Optional[int]:
        """Find the index of an existing keyvalue option."""
        for option_index, arg in enumerate(args):
            if arg == key and option_index + 1 < len(args):
                next_arg = args[option_index + 1]
                if not next_arg.startswith("-") and "=" in next_arg:
                    return option_index
        return None

    def update(self, args: List[str], option: Option) -> List[str]:
        new_args = args[:]

        for i, arg in enumerate(new_args):
            if arg != option.key:
                continue

            existing_pairs = self._collect_keyvalue_pairs(new_args, i)
            updated_pairs = self._update_keyvalue_pairs(existing_pairs, option.value)
            result = self._replace_keyvalue_pairs(
                new_args, i, existing_pairs, updated_pairs
            )
            return result

        # Option not found, add as new
        new_args.extend([option.key, option.value])
        return new_args

    def _collect_keyvalue_pairs(self, args: List[str], option_index: int) -> List[str]:
        """Collect all key=value pairs following the option."""
        pairs = []
        for arg in args[option_index + 1 :]:
            if arg.startswith("-"):
                break
            if "=" in arg:
                pairs.append(arg)
        return pairs

    def _update_keyvalue_pairs(
        self, existing_pairs: List[str], new_keyvalue: str
    ) -> List[str]:
        """Update existing pairs with new key=value, or add if not found."""
        new_key = new_keyvalue.split("=", 1)[0]
        updated_pairs = []
        key_found = False

        for pair in existing_pairs:
            if pair.startswith(new_key + "="):
                updated_pairs.append(new_keyvalue)
                key_found = True
            else:
                updated_pairs.append(pair)

        if not key_found:
            updated_pairs.append(new_keyvalue)

        return updated_pairs

    def _replace_keyvalue_pairs(
        self,
        args: List[str],
        option_index: int,
        existing_pairs: List[str],
        updated_pairs: List[str],
    ) -> List[str]:
        """Replace existing pairs with updated ones in the args list."""
        pairs_start = option_index + 1
        pairs_end = pairs_start + len(existing_pairs)
        new_args = args[:]
        new_args[pairs_start:pairs_end] = [" ".join(updated_pairs)]
        return new_args

    def remove(self, args: List[str], key: str) -> List[str]:
        key_parts = key.split(None, 1)
        if len(key_parts) == 2:
            option_key, target_key = key_parts
            return self._remove_specific_keyvalue(args, option_key, target_key)
        else:
            return self._remove_entire_option(args, key)

    def _remove_entire_option(self, args: List[str], key: str) -> List[str]:
        """Remove entire keyvalue option."""
        result = []
        i = 0

        while i < len(args):
            if args[i] != key:
                result.append(args[i])
                i += 1
            else:
                # Found target key, skip it and all its key=value pairs
                pairs = self._collect_keyvalue_pairs(args, i)
                i += len(pairs) + 1  # Skip key + all pairs

        return result

    def _remove_specific_keyvalue(
        self, args: List[str], option_key: str, target_key: str
    ) -> List[str]:
        """Remove specific key=value pair from keyvalue option."""
        result = []
        i = 0

        while i < len(args):
            if args[i] != option_key:
                result.append(args[i])
                i += 1
            else:
                # Found the option key, collect and filter pairs
                pairs = self._collect_keyvalue_pairs(args, i)
                remaining_pairs = [
                    p for p in pairs if not p.startswith(target_key + "=")
                ]

                if remaining_pairs:
                    result.append(option_key)
                    result.append(" ".join(remaining_pairs))
                # If no pairs left, don't add the option at all

                # Skip past this option and its values
                i += len(pairs) + 1  # Skip key + all pairs

        return result


__all__ = ["CommandBuilder"]
