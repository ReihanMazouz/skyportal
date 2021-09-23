"""healpix_alchemy migration

Revision ID: 4047c470ab83
Revises: 171e9ea18885
Create Date: 2021-08-24 13:35:39.484659

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4047c470ab83'
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
    op.add_column('photometry', sa.Column('x', sa.Float(), nullable=True))
    op.add_column('photometry', sa.Column('y', sa.Float(), nullable=True))
    op.add_column('photometry', sa.Column('z', sa.Float(), nullable=True))
    op.add_column('photometry', sa.Column('nested', sa.BigInteger(), nullable=True))
    op.create_index(
        op.f('ix_photometry_nested'), 'photometry', ['nested'], unique=False
    )
    op.create_index(
        op.f('ix_photometry_point'), 'photometry', ['x', 'y', 'z'], unique=False
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_photometry_point'), table_name='photometry')
    op.drop_index(op.f('ix_photometry_nested'), table_name='photometry')
    op.drop_column('photometry', 'nested')
    op.drop_column('photometry', 'z')
    op.drop_column('photometry', 'y')
    op.drop_column('photometry', 'x')
    op.drop_index(op.f('ix_objs_nested'), table_name='objs')
    op.drop_column('objs', 'nested')
    op.drop_column('objs', 'z')
    op.drop_column('objs', 'y')
    op.drop_column('objs', 'x')
    # ### end Alembic commands ###
