#!/usr/bin/env python3
"""Syntax check both scripts."""
import ast, sys

for f in ['scripts/northstar_final.py', 'scripts/high_towns_pipeline.py']:
    try:
        ast.parse(open(f).read())
        print(f"{f}: Syntax OK")
    except SyntaxError as e:
        print(f"{f}: SYNTAX ERROR - {e}")
        sys.exit(1)

print("All scripts valid")