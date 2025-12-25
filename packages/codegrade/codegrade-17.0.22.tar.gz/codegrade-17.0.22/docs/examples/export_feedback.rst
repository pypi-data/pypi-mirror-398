:hide-toc: true


Export Feedback
===============


Use this script to export inline comments in any way you want.
The complete script is available at the :ref:`end of the page <complete-feedback-script>`.


Breakdown
---------


Before any operation can be executed, we need to import codegrade and
authenticate with the server.

To authenticate, we have to pass our username, password and to which
tenant we are connecting. It is best practice to not store your
password inside the script. Either have the user input it or add it
to your environment while working.

.. code-block:: python

   import os
   import codegrade

   client = codegrade.login(
      username='username',
      password=os.getenv('CG_PASSWORD')
      tenant='Tenant Name')

Once we receive a client from the server, we are able to query it for
the data we need. In this case, we are trying to access the submissions
of our assignment.

The first step to do this is getting the assignment's ID. You could put
it manually in the script, but we provide an interactive utility that
makes this process easier: :func:`codegrade.utils.select_from_list`.

As the user may insert an invalid value, we need to check that there
is a value to use to begin with. For this reason, we offer another
utility function, :func:`codegrade.utils.value_or_exit`. You can
specify also a custom error message to give more information to the
user.

To showcase the entire workflow, we will use this to acquire first the
course's ID, then the assignment's ID, so that you do not need to know
the actual ID, just the course's and assignment's names.

The utility takes three parameters:

- A prompt for the user, to describe them what they are seeing
- A list from which to choose
- What each item should show

Let's show the user the course's names. To do so, we will use the
data attached with the :class:`.ExtendedCourse`, in particular the
``name`` property.

.. code-block:: python

   all_courses = client.course.get_all()
   course = codegrade.utils.value_or_exit(
      codegrade.utils.select_from_list(
         'Select a course',
         all_courses,
         lambda c: c.name))

We can now repeat this process to get the assignment's id as well.
We do not need to query the server for the assignments, as we already
have them in ``course``.

.. code-block:: python

   assignment = codegrade.utils.value_or_exit(
      codegrade.utils.select_from_list(
         'Select an assignment',
         course.assignments,
         lambda a: a.name))

Now that we have an assignment, we can query the server for all its
submissions using the :class:`.AssignmentService` of the client.

We can also specify some further information with the query, for
example if we want all the submissions or only the latest. See
:meth:`.AssignmentService.get_all_submissions` for the documentation.

We will only get the latest submissions.

.. code-block:: python

   submissions = client.assignment.get_all_submissions(
      assignment_id=assignment.id,
      latest_only=True)

We can now get the actual feedback and print it using the
:class:`.SubmissionService`.

As we are not interested in the replies, we will not get them. We
can do this using the parameters for :meth:`.SubmissionService.get_feedback`.

Finally we can loop through the files, and then each of the
comments and print them.

.. code-block:: python

   for submission in submissions:
      print(f'\nSubmission by {submission.user.name}')
      feedback = client.submission.get_feedback(
         submission_id=submission.id,
         with_replies=False)

      for file_id, comments in feedback.user.items():
         for author_id, comment in comments.items():
            author = feedback.authors[file_id][author_id].name
            print(f'{author}: {comment}')


.. _complete-feedback-script:

Complete Feedback script
------------------------

.. container:: toggle

   .. container:: header

      Click here to see the copy-friendly script

   .. code-block:: python

        import os
        import codegrade

        # Login to CodeGrade
        client = codegrade.login(
            username='username',
            password=os.getenv('CG_PASSWORD')
            tenant='Tenant Name')

        # Get all courses and select the desired one
        all_courses = client.course.get_all()
        course = codegrade.utils.value_or_exit(
            codegrade.utils.select_from_list(
                'Select a course',
                all_courses,
                lambda c: c.name))

        # Select the desired assignment
        assignment = codegrade.utils.value_or_exit(
            codegrade.utils.select_from_list(
                'Select an assignment',
                course.assignments,
                lambda a: a.name))

        # Get all submissions for given assignment
        submissions = client.assignment.get_all_submissions(
            assignment_id=assignment.id,
            latest_only=True)

        # Loop over all submissions and print all inline comments
        for submission in submissions:
            print(f'\nSubmission by {submission.user.name}')
            feedback = client.submission.get_feedback(
                submission_id=submission.id,
                with_replies=False)

            # Loop over all individual files in the submission
            for file_id, comments in feedback.user.items():

                # Loop over all comments per file in submission and print
                for author_id, comment in comments.items():
                    author = feedback.authors[file_id][author_id].name
                    print(f'{author}: {comment}')