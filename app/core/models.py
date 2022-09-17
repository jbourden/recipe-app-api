'''
Database models
'''
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)

class UserManager(BaseUserManager):
    '''Manager for users'''

    def create_user(self, email, password = None, **extra_fields):
        if not email:
            raise ValueError('User must have an email address.')

        user = self.model(email = self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password = None , **extra_fields):

        superuser = self.model(email = self.normalize_email(email), **extra_fields)
        superuser.set_password(password)
        superuser.is_superuser = True
        superuser.is_staff = True
        superuser.save(using=self._db)

        return superuser

class User(AbstractBaseUser, PermissionsMixin):
    '''User in the system'''
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email' 