"""
Unittests for referral.views
"""
import json
import time

from django.test import RequestFactory
from opal.core.test import OpalTestCase
from opal.models import Patient, Episode
from opal.tests.models import Colour
from mock import MagicMock, patch

from referral import api
from referral.routes import ReferralRoute

class TestRoute(ReferralRoute):
    name            = 'View Test Route'
    description     = 'This is a Route we use for unittests'
    target_teams    = ['test']
    target_category = 'testing'
    success_link    = '/awesome/fun/times/'

    def post_create(self, episode, user):
        return


class TestDontCreate(ReferralRoute):
    name            = "View Don't create Test Route"
    description     = 'Another Test Route we use for unittests'
    target_teams    = ['test']
    target_category = 'testing'
    create_new_episode = False


class TestAdditionalRoute(ReferralRoute):
    name = 'Additional Route'
    description = 'To test whether we can save additional models'
    target_teams = []
    create_new_episode = False
    additional_models = [
        Colour
    ]

class ReferralViewTestCase(OpalTestCase):
    def setUp(self):
        for name, viewset in api.viewsets():
            if viewset.referral == TestRoute:
                self.viewset = viewset
            if viewset.referral == TestDontCreate:
                self.dont_create_viewset = viewset
            if viewset.referral == TestAdditionalRoute:
                self.additional_viewset = viewset

        self.request = RequestFactory().post('/referral/refer')
        self.patient = Patient.objects.create()
        self.episode = Episode.objects.create(patient=self.patient)
        self.demographics = self.patient.demographics_set.get()
        self.demographics.hospital_number = str(time.time())
        self.demographics.save()

    def test_retrieve_gets_route(self):
        route = self.viewset().list(None)
        expected = {
            'additional_models': [],
            'name': 'View Test Route',
            'description': 'This is a Route we use for unittests',
            'slug': 'view_test_route',
            'verb': 'Refer',
            'past_verb': 'Referred',
            'progressive_verb': 'Referring',
            'page_title': None,
        }
        self.assertEqual(expected, route.data)

    def test_refer_creates_new_episode(self):
        mock_request = MagicMock(name='Mock request')
        mock_request.data = {
            'hospital_number': self.demographics.hospital_number
        }
        mock_request.user = self.user
        self.assertEqual(1, self.patient.episode_set.count())
        response = self.viewset().create(mock_request)
        self.assertEqual(201, response.status_code)
        expected_response_data = {'success_link': '/awesome/fun/times/'}

        # check we return the success link
        self.assertEqual(expected_response_data, response.data)
        self.assertEqual(2, self.patient.episode_set.count())

    def test_refer_creates_new_patient(self):
        mock_request = MagicMock(name='Mock request')
        new_number = 'n' + str(time.time())
        mock_request.data = {
            'hospital_number': new_number,
            }
        mock_request.user = self.user
        self.assertEqual(0, Patient.objects.filter(demographics__hospital_number=new_number).count())
        response = self.viewset().create(mock_request)
        self.assertEqual(201, response.status_code)
        self.assertEqual(1, Patient.objects.filter(
            demographics__hospital_number=new_number).count())

    def test_refer_sets_additional_models(self):
        mock_request = MagicMock(name='Mock request')
        mock_request.data = {
            'hospital_number': self.demographics.hospital_number,
            'colour': {
                'name': "Fuchsia"
            }
        }
        mock_request.user = self.user
        self.assertEqual(0, self.episode.colour_set.count())
        self.additional_viewset().create(mock_request)
        self.assertEqual(1, self.episode.colour_set.count())
        self.assertEqual('Fuchsia', self.episode.colour_set.first().name)

    def test_refer_updates_demographics(self):
        mock_request = MagicMock(name='Mock request')
        mock_request.data = {
            'hospital_number': self.demographics.hospital_number,
            'demographics'   : {
                'first_name': 'Test',
            }
        }
        mock_request.user = self.user
        self.assertEqual(None, self.patient.demographics_set.get().first_name)
        self.viewset().create(mock_request)
        self.assertEqual(
            'Test', self.patient.demographics_set.get().first_name
        )

    def test_refer_creates_correct_episode_category(self):
        mock_request = MagicMock(name='Mock request')
        mock_request.data = {
            'hospital_number': self.demographics.hospital_number
        }
        mock_request.user = self.user
        self.assertEqual(0, self.patient.episode_set.filter(
            category_name='testing').count())
        self.viewset().create(mock_request)
        self.assertEqual(1, self.patient.episode_set.filter(
            category_name='testing').count())

    def test_refer_sets_tag_names(self):
        mock_request = MagicMock(name='Mock request')
        mock_request.data = {
            'hospital_number': self.demographics.hospital_number
        }
        mock_request.user = self.user
        self.viewset().create(mock_request)
        episode = self.patient.episode_set.get(category_name='testing')
        self.assertEqual(['test'], list(episode.get_tag_names(None)))

    def test_refer_calls_post_create(self):
        mock_request = MagicMock(name='Mock request')
        mock_request.data = {
            'hospital_number': self.demographics.hospital_number
        }
        mock_request.user = self.user
        with patch.object(TestRoute, 'post_create') as mock_create:
            response = self.viewset().create(mock_request)
            episode = self.patient.episode_set.get(category_name='testing')
            mock_create.assert_called_with(episode, mock_request.user)

    def test_dont_create(self):
        self.episode.set_tag_names(["old_team"], self.user)
        mock_request = MagicMock(name='Mock request')
        mock_request.data = {
            'hospital_number': self.demographics.hospital_number
        }
        mock_request.user = self.user
        self.assertEqual(1, self.patient.episode_set.count())
        response = self.dont_create_viewset().create(mock_request)
        self.assertEqual(201, response.status_code)
        self.assertEqual(1, self.patient.episode_set.count())
        new_team_names = set(self.episode.get_tag_names(self.user))
        self.assertEqual(new_team_names, {'old_team', 'test'})
