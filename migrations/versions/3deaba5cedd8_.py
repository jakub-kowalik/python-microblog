"""empty message

Revision ID: 3deaba5cedd8
Revises: e1a2aeea539c
Create Date: 2021-01-14 17:06:38.343367

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3deaba5cedd8'
down_revision = 'e1a2aeea539c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('followers',
    sa.Column('follower_id', sa.Integer(), nullable=True),
    sa.Column('followed_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['followed_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['follower_id'], ['user.id'], )
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('followers')
    # ### end Alembic commands ###