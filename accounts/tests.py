from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class SignUpTests(TestCase):
    def test_user_can_register_and_is_logged_in(self):
        response = self.client.post(
            reverse('signup'),
            {
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
            },
            follow=True,
        )

        self.assertRedirects(response, reverse('profile'))
        self.assertTrue(User.objects.filter(username='newuser').exists())
        self.assertContains(response, 'newuser')


class ChatTests(TestCase):
    def test_logged_in_user_can_send_chat_message(self):
        user = User.objects.create_user(username='chatuser', password='StrongPass123!')
        self.client.force_login(user)

        response = self.client.post(
            reverse('profile'),
            {'text': 'Привет всем!'},
            follow=True,
        )

        self.assertContains(response, 'Привет всем!')
        self.assertContains(response, 'chatuser')
