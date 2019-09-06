from celery import task
from subprocess import Popen, PIPE
from challenge.models import Challenge, Release
from django.utils import timezone
import requests
import datetime
import os


def get_release_version(endpoint):
    try:
        r = requests.head(endpoint)
        version_string = r.headers['ETag']
        version = version_string[3:-1]
        return version
    except Exception as e:
        print(e)
    date = timezone.now()
    return f'{date.year}_{date.month:02d}'
        
@task
def load_release(challenge_id):
    challenge = Challenge.objects.get(pk=challenge_id)
    version = get_release_version(challenge.sparql_endpoint)
    y, m = version.split('_')
    y, m = int(y), int(m)
    date = datetime.datetime(year=y, month=m, day=1)
    print('Release version', version)
    latest_release = challenge.get_latest_release()
    if latest_release is not None and latest_release.version == version:
        print('No new release')
        return
    
    release = Release(
        challenge=challenge,
        sparql_endpoint=challenge.sparql_endpoint,
        sparql_query=challenge.sparql_query,
        date=date,
        version=version)
    release.save()

    challenge.status = challenge.UPDATING
    challenge.save()
    
    # Load release data
    env = dict(os.environ)
    env['JAVA_OPTS'] = '-Xms2g -Xmx32g'
    p = Popen(['groovy', challenge.script, '-c', release.get_dir(),
               '-j', release.get_config_file(),], env=env)
    
    if p.wait() == 0:
        challenge.status = challenge.ACTIVE
    else:
        challenge.status = challenge.UPDATE_FAILED
    challenge.save()
        
