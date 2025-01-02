from fastapi import APIRouter, Depends, status, HTTPException
from slugify import slugify
from sqlalchemy import insert, select, update, delete, text
from sqlalchemy.orm import Session
from typing import Annotated

from app.backend.db_depends import get_db
from app.models import *
from app.schemas import CreateUser, UpdateUser

router = APIRouter(prefix="/user", tags=["user"])
Sess = Annotated[Session, Depends(get_db)]


@router.get('/')
async def all_users(sess: Sess):
    return sess.scalars(select(User)).all()


@router.get('/user_id')
async def user_by_id(sess: Sess, user_id: int):
    user = sess.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='User was not found')
    return user


@router.get('/user_id/tasks')
async def tasks_by_user_id(sess: Sess, user_id: int):
    if not sess.scalar(select(User.id).where(User.id == user_id)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='User was not found')
    return sess.scalars(select(Task).where(Task.user_id == user_id)).all()


@router.post('/create')
async def create_user(sess: Sess, user: CreateUser) -> dict:
    if sess.scalar(select(User.username)
                   .where(User.username == user.username)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail='Duplicated username')
    user_dict = dict(user)
    user_dict['slug'] = slugify(user.username)
    sess.execute(insert(User), user_dict)
    sess.commit()
    return {'status_code': status.HTTP_201_CREATED,
            'transaction': 'Successful'}


@router.put('/update')
async def update_user(sess: Sess, user: UpdateUser, user_id: int) -> dict:
    if not sess.scalar(select(User.id).where(User.id == user_id)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='User was not found')
    sess.execute(update(User).where(User.id == user_id),
                 dict(user))
    sess.commit()
    return {'status_code': status.HTTP_200_OK,
            'transaction': 'User has been updated successfully'}


@router.delete('/delete')
async def delete_user(sess: Sess, user_id: int) -> dict:
    if not sess.scalar(select(User.id).where(User.id == user_id)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='User was not found')
    # для sqlite'а нужно "включить" каскадное удаление
    sess.execute(text('PRAGMA foreign_keys=ON'))
    sess.execute(delete(User).where(User.id == user_id))
    sess.commit()
    return {'status_code': status.HTTP_200_OK,
            'transaction': 'User has been deleted successfully'}


'''
Чтобы вместе с пользователем удалялись все задачи, связанные с ним, я решил
переконфигурировать базу данных для каскадного удаления.

class Task(Base):
...
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id',
                                                    ondelete="CASCADE"))
...

class User(Base):
...
    tasks: Mapped[List['Task']] = relationship(back_populates='user', 
                                               cascade='all, delete',
                                               passive_deletes=True)

sqlite не поддерживает операцию ALTER, поэтому нужно изменить параметры для
стратегии копирование-и-перемещение

app/migrations/env.py:
...
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True
        )
..

alembic revision --autogenerate -m "Cascade deletion"

alembic'у для работы нужно как-то назвать неименованые ограничители sqlite'а
(https://alembic.sqlalchemy.org/en/latest/batch.html)

app/migrations/versions/dc0aaa50be80_cascade_deletion.py:

...
naming_convention = {
    "fk":
    "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
}

def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('tasks', schema=None,
                              naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint('fk_tasks_user_id_users', type_='foreignkey')
        batch_op.create_foreign_key('fk_tasks_user_id_users',
                                    'users', ['user_id'], ['id'],
                                    ondelete='CASCADE')
...

alembic upgrade head

Теперь схема таблицы tasks изменилась:
...
        CONSTRAINT fk_tasks_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
...
'''