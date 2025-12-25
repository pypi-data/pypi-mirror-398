# coding=utf-8

import mongoengine as me

from applyx.mongo import Document


class User(Document):
    STATUS_CHOICES = (
        (0, 'UNKNOWN'),
        (1, 'NORMAL'),
        (2, 'DEACTIVATED'),
        (3, 'RESTRICTED'),
        (4, 'DELETED'),
    )

    email = me.StringField(default='', help_text='邮箱')
    username = me.StringField(default='', help_text='账号')
    password = me.StringField(default='', help_text='密码')  # encode
    status = me.IntField(choices=STATUS_CHOICES, default=0, help_text='状态')

    created_at = me.DateTimeField(default=None, help_text='创建时间')
    updated_at = me.DateTimeField(default=None, help_text='更新时间')

    meta = {
        'db_alias': 'default',
        'collection': 'users',
    }

    def dict(self):
        record = super().dict()
        record.pop('password')
        return record
