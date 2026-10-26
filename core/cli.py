import os
import click
from core.extensions import db


def register_cli(app):
    @app.cli.command('setup-db')
    def setup_db():
        """Create missing tables and seed accounts, products, links, and optional sample orders."""
        from auth.seed import seed_accounts
        from shop.seed import seed_products, seed_links, seed_dummy_orders
        db.create_all()
        try:
            seed_accounts()
            seed_products()
            seed_links()
            if os.environ.get('SEED_DUMMY_DATA', '1') == '1':
                seed_dummy_orders()
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        click.echo('Database ready. Existing accounts and orders were preserved.')

    @app.cli.command('reset-db')
    @click.confirmation_option(prompt='Delete ALL local accounts, activity and orders?')
    @click.pass_context
    def reset_db(ctx):
        if not app.debug or not app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:'):
            raise click.ClickException('Reset is only allowed for a local SQLite database in debug mode.')
        db.drop_all()
        ctx.invoke(setup_db)

