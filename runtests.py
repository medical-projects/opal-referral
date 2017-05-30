"""
Standalone test runner for referral plugin
"""
import os
import sys
from opal.core import application


class Application(application.OpalApplication):
    pass

from django.conf import settings

settings.configure(DEBUG=True,
                   DATABASES={
                       'default': {
                           'ENGINE': 'django.db.backends.sqlite3',
                       }
                   },
                   ROOT_URLCONF='opal.urls',
                   STATIC_URL='/assets/',
                   STATIC_ROOT='static',
                   STATICFILES_FINDERS=(
                        'django.contrib.staticfiles.finders.FileSystemFinder',
                        'django.contrib.staticfiles.finders.AppDirectoriesFinder',
                        'compressor.finders.CompressorFinder',
                    ),
                   COMPRESS_ROOT='/tmp/',
                   MIDDLEWARE_CLASSES = (
                       'django.middleware.common.CommonMiddleware',
                       'django.contrib.sessions.middleware.SessionMiddleware',
                       'opal.middleware.AngularCSRFRename',
                       'django.middleware.csrf.CsrfViewMiddleware',
                       'django.contrib.auth.middleware.AuthenticationMiddleware',
                       'django.contrib.messages.middleware.MessageMiddleware',
                       'opal.middleware.DjangoReversionWorkaround',
                       'axes.middleware.FailedLoginMiddleware',
                   ),
                   INSTALLED_APPS=('django.contrib.auth',
                                   'django.contrib.contenttypes',
                                   'django.contrib.sessions',
                                   'django.contrib.staticfiles',
                                   'compressor',
                                   'django.contrib.admin',
                                   'opal',
                                   'opal.tests',
                                   'referral',
                   ))

import django
django.setup()

from django.test.runner import DiscoverRunner
test_runner = DiscoverRunner(verbosity=1)
if len(sys.argv) == 2:
    failures = test_runner.run_tests([sys.argv[-1], ])
else:
    failures = test_runner.run_tests(['referral', ])
if failures:
    sys.exit(failures)
