from fastapi import APIRouter, Depends, status, HTTPException
from slugify import slugify
from sqlalchemy import insert, select, update, delete
from sqlalchemy.orm import Session
from typing import Annotated

from app.backend.db_depends import get_db
from app.models import *
from app.schemas import CreateTask, UpdateTask

router = APIRouter(prefix="/task", tags=["task"])
Sess = Annotated[Session, Depends(get_db)]


@router.get('/')
async def all_tasks(sess: Sess):
    return sess.scalars(select(Task)).all()


@router.get('/task_id')
async def task_by_id(sess: Sess, task_id: int):
    task = sess.scalar(select(Task).where(Task.id == task_id))
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='Task was not found')
    return task


@router.post('/create')
async def create_task(sess: Sess, task: CreateTask, user_id: int) -> dict:
    if not sess.scalar(select(User.id).where(User.id == user_id)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='User was not found')
    task_dict = dict(task)
    task_dict['slug'] = slugify(task.title)
    task_dict['user_id'] = user_id
    sess.execute(insert(Task), task_dict)
    sess.commit()
    return {'status_code': status.HTTP_201_CREATED,
            'transaction': 'Successful'}


@router.put('/update')
async def update_task(sess: Sess, task: UpdateTask, task_id: int) -> dict:
    if not sess.scalar(select(Task.id).where(Task.id == task_id)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='Task was not found')
    task_dict = dict(task)
    task_dict['slug'] = slugify(task.title)
    sess.execute(update(Task).where(Task.id == task_id), task_dict)
    sess.commit()
    return {'status_code': status.HTTP_200_OK,
            'transaction': 'Task has been updated successfully'}


@router.delete('/delete')
async def delete_task(sess: Sess, task_id: int) -> dict:
    if not sess.scalar(select(Task.id).where(Task.id == task_id)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='Task was not found')
    sess.execute(delete(Task).where(Task.id == task_id))
    sess.commit()
    return {'status_code': status.HTTP_200_OK,
            'transaction': 'Task has been deleted successfully'}