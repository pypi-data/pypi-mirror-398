from django.test import TestCase, Client


class ServiceTestCase(TestCase):
    def test_validation(self):
        'Test taxonomy validation service.'

        c = Client()
        response = c.get('/taxonomy/api/v1/validation/S')
        self.assertEqual(response.status_code, 200)

        c = Client()
        response = c.get('/taxonomy/api/v1/validation/S+SL')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['is_canonical'], True)

        response = c.get('/taxonomy/api/v1/validation/SL+S')
        self.assertEqual(response.data['is_canonical'], False)
        self.assertEqual(response.data['canonical'], 'S+SL')
        self.assertEqual(response.status_code, 200)

        response = c.get('/taxonomy/api/v1/validation/S+SL+S')
        self.assertEqual(response.status_code, 400)

        response = c.get('/taxonomy/api/v1/validation/SSSS')
        self.assertEqual(response.data['message'],
                         'Attribute [SSSS]: unknown atom [SSSS].')
        self.assertEqual(response.status_code, 400)

        response = c.get('/taxonomy/api/v1/info')
        self.assertEqual(response.status_code, 200)
