# coding=utf-8

import datetime
from typing import Any

from mongoengine import Q

from applyx.service import BaseService
from project.apps.models import User


class UserService(BaseService):
    def create(self, user_dict: dict[str, Any]):
        user = User()

        user.email = user_dict['email']
        user.username = user_dict['username']
        user.password = user_dict['password']
        user.status = 2

        now = datetime.datetime.now()
        user.created_at = now
        user.updated_at = now

        user.switch_db('default').save()
        return user

    def filter(self, criteria: dict[str, Any], pn=0, ps=20):
        users = User.objects

        keyword = criteria.get('keyword')
        if keyword:
            query = Q(email__icontains=keyword) | Q(username__icontains=keyword)
            users = users.filter(query)

        total = users.count()
        start, end = (pn - 1) * ps, pn * ps
        users = users.order_by('-created_at')[start:end]
        return total, users

    def get(self, user_id: str):
        user = User.objects.filter(id=user_id).first()
        return user

    def activate(self, user_id: str):
        user = User.objects.filter(id=user_id)
        if user is None:
            return False

        user.status = 1

        now = datetime.datetime.now()
        user.updated_at = now

        user.switch_db('default').save()
        return True

    def update(self, user_id: str, user_dict: dict[str, Any]):
        user = User.objects.filter(id=user_id).first()
        if user is None:
            return False

        user.email = user_dict['email']
        user.username = user_dict['username']

        now = datetime.datetime.now()
        user.updated_at = now

        user.switch_db('default').save()
        return True
