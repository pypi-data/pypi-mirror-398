from django.core.management.base import BaseCommand
from django_whatsapp_api_wrapper.models import WhatsAppCloudApiBusiness


class Command(BaseCommand):
    help = 'Setup WhatsApp Business credentials'

    def add_arguments(self, parser):
        parser.add_argument('--tenant-id', type=int, required=True, help='Tenant/Organization ID')
        parser.add_argument('--token', required=True, help='Access token')
        parser.add_argument('--waba-id', required=True, help='WhatsApp Business Account ID')
        parser.add_argument('--phone-number-id', required=True, help='Phone Number ID')
        parser.add_argument('--phone-number', required=True, help='Phone number')
        parser.add_argument('--api-version', default='v23.0', help='API version (default: v23.0)')

    def handle(self, *args, **options):
        business, created = WhatsAppCloudApiBusiness.objects.update_or_create(
            tenant_id=options['tenant_id'],
            defaults={
                'type': 'cloud_api',
                'token': options['token'],
                'waba_id': options['waba_id'],
                'phone_number_id': options['phone_number_id'],
                'phone_number': options['phone_number'],
                'api_version': options['api_version'],
                'business_id': options['waba_id'],
            }
        )

        action = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(
            f'{action} WhatsApp Business account for tenant_id={options["tenant_id"]} (ID: {business.id})'
        ))
