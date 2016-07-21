"""New Flask structure

Revision ID: f7c68fbba74e
Revises: 964f61695f01
Create Date: 2016-07-20 20:55:55.645107

"""

# revision identifiers, used by Alembic.
revision = 'f7c68fbba74e'
down_revision = '964f61695f01'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('abilities',
    sa.Column('id', sa.VARCHAR(length=36), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=True),
    sa.Column('created_on', sa.DateTime(), nullable=False),
    sa.Column('updated_on', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('roles',
    sa.Column('id', sa.VARCHAR(length=36), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=True),
    sa.Column('created_on', sa.DateTime(), nullable=False),
    sa.Column('updated_on', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('role_abilities',
    sa.Column('role_id', sa.VARCHAR(length=36), nullable=True),
    sa.Column('ability_id', sa.VARCHAR(length=36), nullable=True),
    sa.ForeignKeyConstraint(['ability_id'], ['abilities.id'], ),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], )
    )
    with op.batch_alter_table(u'user_roles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('role_id', sa.VARCHAR(length=36), nullable=True))
        batch_op.alter_column('user_id',
               existing_type=sa.VARCHAR(length=36),
               nullable=True)
        # batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('user_roles', 'roles', ['role_id'], ['id'])
        batch_op.drop_column('updated_on')
        batch_op.drop_column('created_on')
        batch_op.drop_column('id')
        batch_op.drop_column('role_type_id')

    with op.batch_alter_table(u'users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('firstname', sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column('lastname', sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column('type', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('username', sa.String(), nullable=True))
        batch_op.drop_column('admin')
        batch_op.drop_column('openid')
        batch_op.drop_column('name')
        batch_op.drop_column('email')

    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table(u'users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('email', sa.VARCHAR(length=200), nullable=True))
        batch_op.add_column(sa.Column('name', sa.VARCHAR(length=60), nullable=True))
        batch_op.add_column(sa.Column('openid', sa.VARCHAR(length=200), nullable=True))
        batch_op.add_column(sa.Column('admin', sa.BOOLEAN(), server_default=sa.text(u"'0'"), autoincrement=False, nullable=True))
        batch_op.drop_column('username')
        batch_op.drop_column('type')
        batch_op.drop_column('lastname')
        batch_op.drop_column('firstname')

    with op.batch_alter_table(u'user_roles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('role_type_id', sa.VARCHAR(length=36), nullable=True))
        batch_op.add_column(sa.Column('id', sa.VARCHAR(length=36), nullable=False))
        batch_op.add_column(sa.Column('created_on', sa.DATETIME(), nullable=False))
        batch_op.add_column(sa.Column('updated_on', sa.DATETIME(), nullable=False))
        # batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('role_types_roles', 'role_types', ['role_type_id'], ['id'])
        batch_op.alter_column('user_id',
               existing_type=sa.VARCHAR(length=36),
               nullable=False)
        batch_op.drop_column('role_id')

    op.create_table('role_types',
    sa.Column('id', sa.VARCHAR(length=36), nullable=False),
    sa.Column('name', sa.VARCHAR(length=60), nullable=True),
    sa.Column('created_on', sa.DATETIME(), nullable=False),
    sa.Column('updated_on', sa.DATETIME(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('role_abilities')
    op.drop_table('roles')
    op.drop_table('abilities')
    ### end Alembic commands ###
