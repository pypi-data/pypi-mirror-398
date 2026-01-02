"""Command-line interface for dotpop."""

import argparse
import sys
import os
import re
from pathlib import Path

from . import __version__
from .exceptions import DotpopError
from .helpers import export, apply
from .loader import load


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='dotpop',
        description='Parse and validate .env and .dpop files'
    )
    parser.add_argument('--version', action='version', version=f'dotpop {__version__}')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    check_parser = subparsers.add_parser('check', help='Validate a file')
    check_parser.add_argument('path', help='Path to file')
    check_parser.add_argument('--no-os-env', action='store_true', help='Do not merge with OS environment')
    
    print_parser = subparsers.add_parser('print', help='Print resolved environment')
    print_parser.add_argument('path', help='Path to file')
    print_parser.add_argument('--no-os-env', action='store_true', help='Do not merge with OS environment')
    print_parser.add_argument('--no-redact', action='store_true', help='Do not redact secrets')
    
    export_parser = subparsers.add_parser('export', help='Export to different format')
    export_parser.add_argument('path', help='Path to file')
    export_parser.add_argument('--format', choices=['dotenv', 'json', 'cmake', 'cpp-header'],
                               default='dotenv', help='Output format')
    export_parser.add_argument('--no-os-env', action='store_true', help='Do not merge with OS environment')
    export_parser.add_argument('--no-redact', action='store_true', help='Do not redact secrets')
    
    apply_parser = subparsers.add_parser('apply', help='Apply variables to current shell environment')
    apply_parser.add_argument('path', help='Path to file')
    apply_parser.add_argument('--no-os-env', action='store_true', help='Do not merge with OS environment')
    apply_parser.add_argument('--overwrite', action='store_true', help='Overwrite existing environment variables')
    apply_parser.add_argument('--dry-run', action='store_true', help='Preview changes without applying')
    
    clear_parser = subparsers.add_parser('clear', help='Remove variables from current shell environment')
    clear_parser.add_argument('path', help='Path to file')
    clear_parser.add_argument('--no-os-env', action='store_true', help='Do not merge with OS environment')
    
    set_parser = subparsers.add_parser('set', help='Set or update a variable in the config file')
    set_parser.add_argument('path', help='Path to file')
    set_parser.add_argument('key', help='Variable name')
    set_parser.add_argument('value', help='Variable value')
    set_parser.add_argument('--type', choices=['str', 'int', 'float', 'bool', 'json', 'list', 'path', 'url'],
                           help='Variable type')
    set_parser.add_argument('--validators', help='Validators (e.g., "required | min=1 | max=100")')
    set_parser.add_argument('--create', action='store_true', help='Create file if it does not exist')
    set_parser.add_argument('--backup', action='store_true', help='Create backup before modifying')
    
    get_parser = subparsers.add_parser('get', help='Get a variable value from the config file')
    get_parser.add_argument('path', help='Path to file')
    get_parser.add_argument('key', help='Variable name')
    get_parser.add_argument('--no-os-env', action='store_true', help='Do not merge with OS environment')
    get_parser.add_argument('--raw', action='store_true', help='Print raw value without type conversion')
    
    unset_parser = subparsers.add_parser('unset', help='Remove a variable from the config file')
    unset_parser.add_argument('path', help='Path to file')
    unset_parser.add_argument('key', help='Variable name')
    unset_parser.add_argument('--backup', action='store_true', help='Create backup before modifying')
    
    list_parser = subparsers.add_parser('list', help='List all variables in the config file')
    list_parser.add_argument('path', help='Path to file')
    list_parser.add_argument('--no-os-env', action='store_true', help='Do not merge with OS environment')
    list_parser.add_argument('--keys-only', action='store_true', help='Print only variable names')
    list_parser.add_argument('--filter', help='Filter variables by pattern (regex)')
    
    crypto_parser = subparsers.add_parser('crypto', help='Encryption utilities')
    crypto_subparsers = crypto_parser.add_subparsers(dest='crypto_command')
    
    crypto_gen = crypto_subparsers.add_parser('generate', help='Generate encryption key')
    
    crypto_enc = crypto_subparsers.add_parser('encrypt', help='Encrypt a value')
    crypto_enc.add_argument('key', help='Encryption key')
    crypto_enc.add_argument('value', help='Value to encrypt')
    
    crypto_dec = crypto_subparsers.add_parser('decrypt', help='Decrypt a value')
    crypto_dec.add_argument('key', help='Encryption key')
    crypto_dec.add_argument('value', help='Encrypted value')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    try:
        if args.command == 'check':
            return cmd_check(args)
        elif args.command == 'print':
            return cmd_print(args)
        elif args.command == 'export':
            return cmd_export(args)
        elif args.command == 'apply':
            return cmd_apply(args)
        elif args.command == 'clear':
            return cmd_clear(args)
        elif args.command == 'set':
            return cmd_set(args)
        elif args.command == 'get':
            return cmd_get(args)
        elif args.command == 'unset':
            return cmd_unset(args)
        elif args.command == 'list':
            return cmd_list(args)
        elif args.command == 'crypto':
            return cmd_crypto(args)
    except DotpopError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 2
    
    return 0


def cmd_check(args):
    path = Path(args.path)
    
    if not path.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        return 1
    
    use_os_env = not args.no_os_env
    
    try:
        env = load(str(path), use_os_env=use_os_env)
        
        print(f"✓ Successfully parsed {path}")
        print(f"  {len(env.values)} variables loaded")
        
        if env.warnings:
            print(f"\nWarnings:")
            for warning in env.warnings:
                print(f"  - {warning}")
        
        return 0
    
    except DotpopError as e:
        print(f"✗ Validation failed:", file=sys.stderr)
        try:
            source_lines = path.read_text().splitlines()
            print(e.format_with_context(source_lines), file=sys.stderr)
        except:
            print(f"  {e}", file=sys.stderr)
        return 1


def cmd_print(args):
    """Print resolved environment."""
    path = Path(args.path)
    
    if not path.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        return 1
    
    use_os_env = not args.no_os_env
    redact = not args.no_redact
    
    env = load(str(path), use_os_env=use_os_env)
    
    output = export(env.values, format='dotenv', redact_secrets=redact)
    print(output, end='')
    
    return 0


def cmd_export(args):
    """Export to different format."""
    path = Path(args.path)
    
    if not path.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        return 1
    
    use_os_env = not args.no_os_env
    redact = not args.no_redact
    
    env = load(str(path), use_os_env=use_os_env)
    
    output = export(env.values, format=args.format, redact_secrets=redact)
    print(output, end='')
    
    return 0


def cmd_apply(args):
    path = Path(args.path)
    
    if not path.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        return 1
    
    use_os_env = not args.no_os_env
    overwrite = args.overwrite
    dry_run = args.dry_run
    
    env = load(str(path), use_os_env=use_os_env)
    
    applied = []
    skipped = []
    
    for key, value in env.values.items():
        if key in os.environ and not overwrite:
            skipped.append(key)
        else:
            if not dry_run:
                os.environ[key] = str(value)
            applied.append(key)
    
    if dry_run:
        print(f"✓ Dry run: Would apply {len(applied)} variables to environment")
    else:
        print(f"✓ Applied {len(applied)} variables to environment")
    
    if applied:
        print(f"\nApplied:")
        for key in sorted(applied):
            print(f"  {key}")
    
    if skipped:
        print(f"\nSkipped (already set, use --overwrite to replace):")
        for key in sorted(skipped):
            print(f"  {key}")
    
    if applied:
        print(f"\nNote: Variables are only set in the current Python process.")
        print(f"To apply to your shell, use: eval $(dotpop export {path})")
    
    return 0


def cmd_clear(args):
    """Remove variables from shell environment."""
    path = Path(args.path)
    
    if not path.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        return 1
    
    use_os_env = not args.no_os_env
    
    env = load(str(path), use_os_env=use_os_env)
    
    removed = []
    not_found = []
    
    for key in env.values.keys():
        if key in os.environ:
            del os.environ[key]
            removed.append(key)
        else:
            not_found.append(key)
    
    print(f"✓ Removed {len(removed)} variables from environment")
    
    if removed:
        print(f"\nRemoved:")
        for key in sorted(removed):
            print(f"  {key}")
    
    if not_found:
        print(f"\nNot found in environment:")
        for key in sorted(not_found):
            print(f"  {key}")
    
    if removed:
        print(f"\nNote: Variables are only removed from the current Python process.")
        print(f"To clear from your shell, use: eval $(dotpop export {path} | sed 's/^/unset /' | sed 's/=.*//')")
    
    return 0


def cmd_set(args):
    """Set or update a variable in the config file."""
    path = Path(args.path)
    
    if not path.exists():
        if args.create:
            path.touch()
            print(f"Created {path}")
        else:
            print(f"Error: File not found: {path}", file=sys.stderr)
            print(f"Use --create to create the file", file=sys.stderr)
            return 1
    
    if args.backup:
        backup_path = Path(str(path) + '.backup')
        import shutil
        shutil.copy2(path, backup_path)
        print(f"Backup created: {backup_path}")
    
    content = path.read_text()
    lines = content.split('\n')
    
    key_pattern = re.compile(rf'^(\s*)(!?)({re.escape(args.key)})(:[a-z]+)?(\s*=)')
    found = False
    new_lines = []
    
    type_annotation = f':{args.type}' if args.type else ''
    validators = f' | {args.validators}' if args.validators else ''
    new_line = f'{args.key}{type_annotation}={args.value}{validators}'
    
    for line in lines:
        match = key_pattern.match(line)
        if match:
            new_lines.append(new_line)
            found = True
            print(f"✓ Updated {args.key}")
        else:
            new_lines.append(line)
    
    if not found:
        if new_lines and not new_lines[-1].strip():
            new_lines[-1] = new_line
        else:
            new_lines.append(new_line)
        print(f"✓ Added {args.key}")
    
    path.write_text('\n'.join(new_lines))
    
    try:
        env = load(str(path), use_os_env=False)
        print(f"✓ Validated successfully")
        print(f"  Value: {env[args.key]}")
        if args.type:
            print(f"  Type: {type(env[args.key]).__name__}")
    except DotpopError as e:
        print(f"⚠ Warning: Validation failed: {e}", file=sys.stderr)
        return 1
    
    return 0


def cmd_get(args):
    """Get a variable value from the config file."""
    path = Path(args.path)
    
    if not path.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        return 1
    
    use_os_env = not args.no_os_env
    
    try:
        env = load(str(path), use_os_env=use_os_env)
        
        if args.key not in env:
            print(f"Error: Variable '{args.key}' not found", file=sys.stderr)
            return 1
        
        if args.raw:
            print(env.get_str(args.key))
        else:
            value = env[args.key]
            print(value)
        
        return 0
    
    except DotpopError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_unset(args):
    """Remove a variable from the config file."""
    path = Path(args.path)
    
    if not path.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        return 1
    
    if args.backup:
        backup_path = Path(str(path) + '.backup')
        import shutil
        shutil.copy2(path, backup_path)
        print(f"Backup created: {backup_path}")
    
    content = path.read_text()
    lines = content.split('\n')
    
    key_pattern = re.compile(rf'^(\s*)(!?)({re.escape(args.key)})(:[a-z]+)?(\s*=)')
    found = False
    new_lines = []
    
    for line in lines:
        if key_pattern.match(line):
            found = True
            print(f"✓ Removed {args.key}")
        else:
            new_lines.append(line)
    
    if not found:
        print(f"Warning: Variable '{args.key}' not found in file", file=sys.stderr)
        return 1
    
    path.write_text('\n'.join(new_lines))
    
    try:
        load(str(path), use_os_env=False)
        print(f"✓ File validated successfully")
    except DotpopError as e:
        print(f"⚠ Warning: Validation failed after removal: {e}", file=sys.stderr)
    
    return 0


def cmd_crypto(args):
    from cryptography.fernet import Fernet
    from .types import set_encryption_key, encrypt_secret, decrypt_secret
    
    if not args.crypto_command:
        print("Error: No crypto subcommand specified", file=sys.stderr)
        return 1
    
    if args.crypto_command == 'generate':
        key = Fernet.generate_key()
        print(key.decode('utf-8'))
        return 0
    
    elif args.crypto_command == 'encrypt':
        key = args.key.encode('utf-8')
        set_encryption_key(key)
        encrypted = encrypt_secret(args.value)
        print(f"ENC({encrypted})")
        return 0
    
    elif args.crypto_command == 'decrypt':
        key = args.key.encode('utf-8')
        set_encryption_key(key)
        
        value = args.value
        if value.startswith("ENC(") and value.endswith(")"):
            value = value[4:-1]
        
        decrypted = decrypt_secret(value)
        print(decrypted)
        return 0
    
    return 1


def cmd_list(args):
    """List all variables in the config file."""
    path = Path(args.path)
    
    if not path.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        return 1
    
    use_os_env = not args.no_os_env
    
    try:
        env = load(str(path), use_os_env=use_os_env)
        
        keys = sorted(env.values.keys())
        
        if args.filter:
            pattern = re.compile(args.filter)
            keys = [k for k in keys if pattern.search(k)]
        
        if not keys:
            print("No variables found")
            return 0
        
        if args.keys_only:
            for key in keys:
                print(key)
        else:
            max_key_len = max(len(k) for k in keys)
            for key in keys:
                value = env[key]
                value_str = str(value)
                if len(value_str) > 50:
                    value_str = value_str[:47] + "..."
                print(f"{key:<{max_key_len}}  {value_str}")
        
        print(f"\nTotal: {len(keys)} variables")
        
        return 0
    
    except DotpopError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
