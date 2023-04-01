from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _


class Profile(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='profiles',
                                verbose_name=_('пользователь'))
    registration_date = models.DateField(auto_now_add=True, verbose_name=_('дата регистрации'))
    is_seller = models.BooleanField(verbose_name=_('продавец'), default=False)
    avatar = models.ImageField(upload_to='files/', blank=True, verbose_name=_('аватар'))
    funds = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('доступные средства'),
                                default=0)
    purchases = models.PositiveIntegerField(verbose_name='количество покупок', default=0)

    class Meta:
        verbose_name = _('профиль')
        verbose_name_plural = _('профили')

    def __str__(self):
        return f'Profile of {self.user}'

    @property
    def buyer_status(self):
        if self.purchases < 100:
            return _('начинающий покупатель')
        elif self.purchases < 500:
            return _('опытный покупатель')
        elif self.purchases < 1000:
            return _('постоянный покупатель')
        elif self.purchases < 5000:
            return _('преданный покупатель')
        else:
            return _('привилегированный покупатель')
