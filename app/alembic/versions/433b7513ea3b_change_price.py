"""change price

Revision ID: 433b7513ea3b
Revises: c10045cd4f2d
Create Date: 2024-08-10 16:43:46.332374

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '433b7513ea3b'
down_revision = 'c10045cd4f2d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('price', sa.Column('model', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.drop_index('ix_price_expiration_datetime', table_name='price')
    op.drop_column('price', 'weekly_days')
    op.drop_column('price', 'entrance_fee')
    op.drop_column('price', 'hourly_fee')
    op.drop_column('price', 'penalty_fee')
    op.drop_column('price', 'expiration_datetime')
    op.drop_column('price', 'daily_fee')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('price', sa.Column('daily_fee', sa.BIGINT(), autoincrement=False, nullable=True))
    op.add_column('price', sa.Column('expiration_datetime', postgresql.TIMESTAMP(), autoincrement=False, nullable=True))
    op.add_column('price', sa.Column('penalty_fee', sa.BIGINT(), autoincrement=False, nullable=True))
    op.add_column('price', sa.Column('hourly_fee', sa.BIGINT(), autoincrement=False, nullable=True))
    op.add_column('price', sa.Column('entrance_fee', sa.BIGINT(), autoincrement=False, nullable=True))
    op.add_column('price', sa.Column('weekly_days', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True))
    op.create_index('ix_price_expiration_datetime', 'price', ['expiration_datetime'], unique=False)
    op.drop_column('price', 'model')
    # ### end Alembic commands ###
