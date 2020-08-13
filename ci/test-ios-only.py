# coding=utf-8

# Purpose:
#   test Android & iOS packages connection to SpatialOS
#   use GCS to upload to firebase directly will fail because of the file size being too large
#   test:
#       1. download Android & iOS packages to local
#       2. upload Android & iOS packages to gcloud
#       3. download the log file
#       4. analyze log file if spatialos connection successful keywords found

import io
import os
import re
import json
import sys
import common
import platform

# Based on artifact_paths in nightly.android.firebase.test.yaml and nightly.ios.firebase.test.yaml
FIREBASE_LOG_DIR="firebase_log"

def switch_gcloud_project(project_id):
    args = ['config', 'set', 'project', project_id]
    common.run_command('gcloud', ' '.join(args))


def check_firebase_log(app_platform, url, device, success_keyword):
    filename = ''
    localfilename = os.path.join(FIREBASE_LOG_DIR, '%s.txt' % device)
    if os.path.exists(localfilename):
        os.remove(localfilename)
    if app_platform == 'android':
        filename = 'logcat'
    elif app_platform == 'ios':
        filename = 'syslog.txt'
    else:
        print("unsupported platform:%s" % app_platform)
        return False
    fullurl = 'gs://%s%s/%s' % (url, device, filename)
    common.run_command('gsutil', 'cp %s %s' % (fullurl, localfilename))
    print(os.path.abspath(localfilename))
    if os.path.exists(localfilename):
        with io.open(localfilename, encoding="utf8") as fp:
            line = fp.readline()
            while line:
                if success_keyword in line:
                    return True
                line = fp.readline()
    return False


def gcloud_upload(app_platform, app_path):
    args = [
        'beta',
        'firebase',
        'test',
        app_platform,
        'run',
        '--type=game-loop',
        '--app="%s"' % app_path,
        '--scenario-numbers=1',
        '--format="json"',
    ]
    print('%s exist:%d' % (app_path, os.path.isfile(app_path)))
    common.run_command('gcloud', ' '.join(args))


def download_app():
    localpath = 'GDKShooter.ipa'
    args = [
        'cp', 
        'gs://io-internal-infra-intci-artifacts-production/organizations/improbable/pipelines/unrealgdkexampleproject-nightly/builds/7db042e4-869f-45fa-8b77-069831c17a49/jobs/v4-9c6ee0ef-d/fe8ad796-1565-4c33-aec2-19b894a15a0e/macos/cooked-ios/IOS/GDKShooter.ipa',
        localpath
    ]
    common.run_command('gsutil', ' '.join(args))
    return localpath


if __name__ == "__main__":
    app_platform = 'ios'
    cmds = ['gcloud', 'config', 'get-value', 'project']
    res = common.run_shell(cmds)
    project = res.stdout.read().decode('UTF-8')

    # Makre sure FIREBASE_LOG_DIR is exist
    if os.path.exists(FIREBASE_LOG_DIR):
        os.mkdir(FIREBASE_LOG_DIR)
        
    # Set to firebase gcloud project both Windows & Mac
    # switch_gcloud_project('chlorodize-bipennated-8024348')

    # Download app to local
    localpath = download_app()

    # Upload local app to firebase for test
    gcloud_upload(app_platform, localpath)

    # Set to buildkite infrastructure gcloud project
    # switch_gcloud_project(project)

    # Update firebase succeed/total value
    exit(0)
