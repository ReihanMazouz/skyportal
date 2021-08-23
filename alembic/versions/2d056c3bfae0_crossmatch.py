"""crossmatch

Revision ID: 2d056c3bfae0
Revises: 171e9ea18885
Create Date: 2021-08-23 11:35:34.019134

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2d056c3bfae0'
down_revision = '171e9ea18885'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('objs', sa.Column('x', sa.Float(), nullable=True))
    op.add_column('objs', sa.Column('y', sa.Float(), nullable=True))
    op.add_column('objs', sa.Column('z', sa.Float(), nullable=True))
    op.add_column('objs', sa.Column('nested', sa.BigInteger(), nullable=True))
    op.create_index(op.f('ix_objs_nested'), 'objs', ['nested'], unique=False)
    op.create_index('ix_objs_point', 'objs', ['x', 'y', 'z'], unique=False)
    op.add_column('photometry', sa.Column('x', sa.Float(), nullable=True))
    op.add_column('photometry', sa.Column('y', sa.Float(), nullable=True))
    op.add_column('photometry', sa.Column('z', sa.Float(), nullable=True))
    op.add_column('photometry', sa.Column('nested', sa.BigInteger(), nullable=True))
    op.create_index(
        op.f('ix_photometry_nested'), 'photometry', ['nested'], unique=False
    )
    op.create_index('ix_photometry_point', 'photometry', ['x', 'y', 'z'], unique=False)

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
    op.drop_index(op.f('ix_photometry_nested'), table_name='photometry')
    op.drop_column('photometry', 'nested')
    op.drop_column('photometry', 'z')
    op.drop_column('photometry', 'y')
    op.drop_column('photometry', 'x')
    op.drop_index(op.f('ix_objs_nested'), table_name='objs')
    op.drop_index('ix_photometry_point', table_name='photometry')
    op.drop_column('objs', 'nested')
    op.drop_column('objs', 'z')
    op.drop_column('objs', 'y')
    op.drop_column('objs', 'x')
    op.drop_index('ix_objs_point', table_name='objs')

    op.drop_index(
        op.f('ix_localizationtiles_nested_lo'), table_name='localizationtiles'
    )
    op.drop_index(
        op.f('ix_localizationtiles_created_at'), table_name='localizationtiles'
    )
    op.drop_table('localizationtiles')
    # ### end Alembic commands ###
