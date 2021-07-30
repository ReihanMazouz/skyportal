"""Add object cross match

Revision ID: 9ff36e96307d
Revises: 4ef77725b330
Create Date: 2021-07-28 11:29:15.221134

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9ff36e96307d'
down_revision = '4ef77725b330'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'localizationtiles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('nested_lo', sa.BigInteger(), nullable=False),
        sa.Column('nested_hi', sa.BigInteger(), nullable=False),
        sa.Column('localization_id', sa.Integer(), nullable=False),
        sa.Column('probdensity', sa.Float(), nullable=False),
        sa.Column('cumprob', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(
            ['localization_id'], ['localizations.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id', 'nested_lo'),
    )
    op.create_index(
        op.f('ix_localizationtiles_created_at'),
        'localizationtiles',
        ['created_at'],
        unique=False,
    )
    op.create_index(
        op.f('ix_localizationtiles_nested_lo'),
        'localizationtiles',
        ['nested_lo'],
        unique=False,
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(
        op.f('ix_localizationtiles_nested_lo'), table_name='localizationtiles'
    )
    op.drop_index(
        op.f('ix_localizationtiles_created_at'), table_name='localizationtiles'
    )
    op.drop_table('localizationtiles')
    # ### end Alembic commands ###
