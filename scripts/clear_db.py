#!/usr/bin/env python3
"""Script seguro para limpar registros do banco de dados do projeto.

Uso:
  - Para listar opções: python scripts/clear_db.py --help
  - Limpar findings:     python scripts/clear_db.py --findings
  - Limpar scans:        python scripts/clear_db.py --scans
  - Reset completo:      python scripts/clear_db.py --reset

O script roda dentro do contexto da Flask app e pede confirmação antes de executar.
"""
import argparse
import sys
from app import create_app, db
from app.models import Scan, Finding


def confirm(prompt: str) -> bool:
    ans = input(prompt + " [y/N]: ").strip().lower()
    return ans == "y" or ans == "yes"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--findings", action="store_true", help="Delete all findings")
    parser.add_argument("--scans", action="store_true", help="Delete all scans (and findings)")
    parser.add_argument("--reset", action="store_true", help="Drop all tables and recreate the database")
    args = parser.parse_args()

    if not (args.findings or args.scans or args.reset):
        parser.print_help()
        sys.exit(1)

    app = create_app()

    with app.app_context():
        if args.findings:
            print("This will DELETE ALL findings from the database.")
            if not confirm("Are you sure?"):
                print("Cancelled")
                return
            n = Finding.query.delete()
            db.session.commit()
            print(f"Deleted {n} findings.")

        if args.scans:
            print("This will DELETE ALL scans and related findings from the database.")
            if not confirm("Are you sure?"):
                print("Cancelled")
                return
            # delete findings first to avoid FK issues
            n1 = Finding.query.delete()
            n2 = Scan.query.delete()
            db.session.commit()
            print(f"Deleted {n2} scans and {n1} findings.")

        if args.reset:
            print("This will DROP ALL TABLES and recreate the database. This is destructive.")
            if not confirm("Are you sure?"):
                print("Cancelled")
                return
            db.drop_all()
            db.create_all()
            print("Database reset: all tables dropped and recreated.")


if __name__ == "__main__":
    main()
