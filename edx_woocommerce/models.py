from django.db.models import Model
from django.db.models import UniqueConstraint, ForeignKey, PROTECT
from django.db.models import BigIntegerField, EmailField
from django.db.models import CharField, DateTimeField

from django.utils import timezone

from django_fsm import FSMIntegerField, ConcurrentTransitionMixin, transition

from edx_webhooks import STATE

import logging


APP_LABEL = 'edx_woocommerce'

logger = logging.getLogger(__name__)


class Order(ConcurrentTransitionMixin, Model):
    class Meta:
        app_label = APP_LABEL

    NEW = STATE.NEW
    PROCESSING = STATE.PROCESSING
    PROCESSED = STATE.PROCESSED
    ERROR = STATE.ERROR

    CHOICES = STATE.CHOICES

    id = BigIntegerField(primary_key=True, editable=False)
    email = EmailField()
    first_name = CharField(max_length=254)
    last_name = CharField(max_length=254)
    received = DateTimeField(default=timezone.now)
    status = FSMIntegerField(choices=CHOICES,
                             default=NEW,
                             protected=True)

    @transition(field=status,
                source=NEW,
                target=PROCESSING,
                on_error=ERROR)
    def start_processing(self):
        logger.debug('Processing order %s' % self.id)

    @transition(field=status,
                source=PROCESSING,
                target=PROCESSED,
                on_error=ERROR)
    def finish_processing(self):
        logger.debug('Finishing order %s' % self.id)

    @transition(field=status,
                source=PROCESSING,
                target=ERROR)
    def fail(self):
        logger.debug('Failed to process order %s' % self.id)


class OrderItem(ConcurrentTransitionMixin, Model):
    class Meta:
        app_label = APP_LABEL
        constraints = [
            UniqueConstraint(fields=['order', 'sku', 'email'],
                             name='unique_order_sku_email')
        ]

    NEW = STATE.NEW
    PROCESSING = STATE.PROCESSING
    PROCESSED = STATE.PROCESSED
    ERROR = STATE.ERROR

    CHOICES = STATE.CHOICES

    order = ForeignKey(
        Order,
        on_delete=PROTECT
    )
    sku = CharField(max_length=254)
    email = EmailField()
    status = FSMIntegerField(choices=CHOICES,
                             default=NEW,
                             protected=True)

    @transition(field=status,
                source=NEW,
                target=PROCESSING,
                on_error=ERROR)
    def start_processing(self):
        logger.debug('Processing item %s for order %s' % (self.id,
                                                          self.order.id))

    @transition(field=status,
                source=PROCESSING,
                target=PROCESSED,
                on_error=ERROR)
    def finish_processing(self):
        logger.debug('Finishing item %s for order %s' % (self.id,
                                                         self.order.id))

    @transition(field=status,
                source=PROCESSING,
                target=ERROR)
    def fail(self):
        logger.debug('Failed to process item %s '
                     'for order %s' % (self.id,
                                       self.order.id))