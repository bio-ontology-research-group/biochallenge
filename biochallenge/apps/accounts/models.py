from django.db import models

from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.utils.translation import ugettext as _
from django.core.exceptions import ValidationError
from django.utils import timezone


def check_unique_email(sender, instance, **kwargs):
    if instance.email and sender.objects.filter(
            email=instance.email).exclude(username=instance.username).count():
        raise ValidationError(_("The email %(email)s already exists!") % {
            'email': instance.email
        })

pre_save.connect(check_unique_email, sender=User)


class UserProfile(models.Model):
    user = models.OneToOneField(
        User, primary_key=True, on_delete=models.CASCADE)
    organization = models.CharField(max_length=255)


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(
            user=instance)

post_save.connect(create_user_profile, sender=User)


class Team(models.Model):
    name = models.CharField(max_length=64, unique=True)
    description = models.TextField(max_length=1024)
    logo = models.ImageField()
    created_date = models.DateTimeField(default=timezone.now)
    created_user = models.ForeignKey(
        User, related_name='created_teams', null=True, on_delete=models.SET_NULL)
    members = models.ManyToManyField(User, through='Member', related_name='teams')

    def get_membership(self, user):
        queryset = self.member_set.filter(user=user)
        if queryset.exists():
            return queryset.get()
        return None

    def __str__(self):
        return self.name


class MemberManager(models.Manager):
    use_for_related_fields = True

    def add_member(self, user, team):
        self.create(user=user, team=team)

    def add_admin_member(self, user, team):
        self.create(user=user, team=team, is_admin=True, status=Member.ACTIVE)

    def remove_member(self, user, team):
        self.filter(user=user, team=team).delete()


class Member(models.Model):
    ACTIVE = 'active'
    INVITED = 'invited'
    STATUSES = ((ACTIVE, ACTIVE), (INVITED, INVITED))

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)
    joined_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=15, default=INVITED)
    
    objects = MemberManager()

    class Meta:
        unique_together = [['user', 'team'],]
