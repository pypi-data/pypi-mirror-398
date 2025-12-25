:hide-toc: true


CodeGrade and GitHub automation
===============================


The complete script is available at the :ref:`end of the page <create_roster.py>`.


.. admonition:: Easier git integration

   Since newer CodeGrade versions, integrating the app with GitHub has
   become a lot easier. This feature is now part of the normal app's
   workflow and thus you might prefer using that.
   `See the official documentation <https://help.codegrade.com/for-students/advanced-features/handing-in-using-git>`_

   This example still showcases a more advanced usage of the API that
   still works and may be interesting to explore.


Using the CodeGrade API and the GitHub API, you can automatically populate
your students' GitHub repositories with the deploy key and webhook details
needed to automatically hand in to CodeGrade with every ``git push``.

Setup
-----

To use the CodeGrade API and GitHub API, first install the required packages:
``python3 -m pip install PyGithub``

You also need to `enable Git submissions <https://help.codegrade.com/faq/set-up-git-uploading>`_
for your CodeGrade assignment and generate a (temporary) personal access
token on GitHub.

Course / GitHub structure
^^^^^^^^^^^^^^^^^^^^^^^^^

The current scripts assume you use CodeGrade standalone, with SSO or have
an LTI 1.3 integration with your LMS, so that we have a full list of all
students before an assignment starts.

The script is created to automatically populate the deploy keys and webhooks
for student repositories in an Organization managed by you. You can of
course use the GitHub API to automatically create these repos in your org
and invite your students to this.

Step 1: Running |create_roster.py|_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

First, create the roster with Git details of all users in your course. By
running ``python3 create_roster.py``. Before running, make sure to fill in
your CodeGrade credentials and assignment ID (found in the URL on CodeGrade).
By default this will be generated as ``roster.csv``. The last column of this
roster should be manually filled in and is the mapping between the
CodeGrade accounts and GitHub repos / accounts. (For now, this mapping is
with repo names).

Step 2: Importing this to GitHub using |import_to_github.py|_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

After generating and adding to ``roster.csv``, you can run ``import_to_github.py``
to set up all webhook information on GitHub.

Before running, fill in:

- GitHub personal access token
- GitHub organization name
- The name of the roster (by default ``roster.csv``)
- The prefix of assignments

For this example, all assignments in our organization have a prefix (defined
in ``import_to_github.py``) and a suffix (the manually filled in name per
student in ``roster.csv``). For instance: **assignment1-johndoe**.

Step 3: Confirm your setup and sit back!
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It is always a good idea to make sure everything went according to plan and going
through some repos in your organization to see if correct deploy keys and
webhooks were added. You can always use a test repo, make a push (an easy way
is to just edit the readme in the GitHub UI) and check CodeGrade.

If everything is done correctly, your students can now start working in their
personal repo and will automatically hand in to CodeGrade with every push they
do!

Need more help? Check `https://help.codegrade.com <https://help.codegrade.com>`_ or send us an email at
support@codegrade.com!


.. |create_roster.py| replace:: ``create_roster.py``
.. _create_roster.py:

Create Roster
-------------


.. container:: toggle

   .. container:: header

      Complete script

   .. code-block:: python

        import csv
        import os

        import codegrade


        # Get list of all students in the course
        def get_users(client, course_id):
            return client.course.get_all_users(course_id=course_id)


        # Get Git webhook data for a user in an assignment
        def webhookdata_per_user(client, username, assignment_id):
            return client.assignment.get_webhook_settings(
                assignment_id=assignment_id,
                webhook_type='git',
                extra_parameters={'author': username}
            )


        # Generate webhook information (webhook url, secret and key)
        def generate_webhook_dict(webhook, client):
            return {
                'url': '{}/api/v1/webhooks/{}'.format(
                    client.http.base_url,
                    webhook.id,
                ),
                'secret': webhook.secret,
                'key': webhook.public_key,
            }


        # Write exported users and webhook information to a CSV
        def init_roster(client, assignment_id, roster):
            users = get_users(
                client,
                client.assignment.get_course(assignment_id=assignment_id).id
            )

            # Open / create roster file and write header and row per user
            with open(roster, mode='w', newline='') as out:
                w = csv.writer(out)
                w.writerow([
                    'name',
                    'codegrade-user',
                    'webhook_url',
                    'secret',
                    'deploy_key',
                    'github-user'
                ])

                # Loop over all users in the course and write webhook data in row
                for u in users:

                    webhook = generate_webhook_dict(
                        webhookdata_per_user(client, u.user.username, assignment_id),
                        client,
                    )

                    w.writerow([
                        u.user.name,
                        u.user.username,
                        webhook['url'],
                        webhook['secret'],
                        webhook['key'],
                        '?'
                    ])


        def main():

            # SET CODEGRADE CREDENTIALS AND TENANT NAME
            client = codegrade.login(
                username='username',
                password=os.getenv('CG_PASSWORD'),
                tenant='Tenant Name'
            )

            # SET ASSIGNMENT ID AND EXPORT FILE NAME
            init_roster(
                client,
                assignment_id=0000,
                roster='roster.csv'
            )


        if __name__ == '__main__':
            main()


.. |import_to_github.py| replace:: ``import_to_github.py``
.. _import_to_github.py:

Import to GitHub
----------------


.. container:: toggle

   .. container:: header

      Complete script

   .. code-block:: python

        import sys
        import csv
        from github import Github


        # Load the roster generated in `create_roster.py` and return list of users
        def load_user_data(filename='roster.csv'):
            with open(filename) as user_data:
                reader = csv.DictReader(user_data)
                try:
                    data = [line for line in reader if line['github-user'] is not '?']
                except csv.Error as e:
                    sys.exit(
                        'file {}, line {}: {}'.format(
                            filename,
                            reader.line_num,
                            e
                        )
                    )
            return data


        # Login to GitHub and set correct webhooks for student repos in organization
        def sync(access, organization, roster, assignment):
            g = Github(access['github']['token'])
            org = g.get_organization(organization['github-name'])
            students = load_user_data(roster)

            no_users = 0
            no_errors = 0

            # Loop over all users from the roster file and set webhook data if not set
            # already
            for student in students:
                try:

                    # Looking for repo with name '$AssignmentName - $GitHubUsername'
                    repo = org.get_repo(
                        assignment['github-name'] + '-' + student['github-user']
                    )

                    # Set deploy key if none is set already
                    if 'codegrade-key' not in [key.title for key in repo.get_keys()]:
                        repo.create_key(
                            title='codegrade-key',
                            key=student['deploy_key']
                        )
                    else:
                        print('>', 'Deploy key already found for', student['name'])

                    # Set webhook if none is set already
                    if (
                        student['webhook_url'] not in
                        [hook.config['url'] for hook in repo.get_hooks()]
                    ):

                        repo.create_hook(
                            'web',
                            config={
                                'url': student['webhook_url'],
                                'content_type': 'json',
                                'secret': student['secret']
                            },
                            events=['push'],
                            active=True
                        )
                    else:
                        print('>', 'Webhook already found for', student['name'])
                    no_users += 1
                except:
                    e = sys.exc_info()[0]
                    print('>', 'Error:', e)
                    no_errors += 1

            print('\nProcessed', no_users, 'student(s);', no_errors, 'error(s).')


        def main():
            sync(

                # SET GITHUB API PERSONAL ACCESS TOKEN
                access={
                    'github': {
                        'token': '0000000000000000000000000000000000000'
                    }
                },

                # SET GITHUB ORGANIZATION INFORMATION NAME
                organization={
                    'github-name': 'organization-name'
                },

                # SET ROSTER FILE (GENERATED BY `CREATE_ROSTER.PY`)
                roster='roster.csv',

                # SET GITHUB REPO NAME PREFIX
                assignment={
                    'github-name': 'repo-prefix'
                }
            )


        if __name__ == '__main__':
            main()