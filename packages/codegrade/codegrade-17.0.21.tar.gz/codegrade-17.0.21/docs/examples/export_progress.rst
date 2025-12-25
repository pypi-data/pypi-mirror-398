:hide-toc: true


Export Student Progress
=======================


Use this script to export the progress over all submissions done by each
individual student. The complete script is available at the :ref:`end of the page <complete-progress-script>`.


.. note::
   This example presupposes you have read the previous example. If you have not
   please read `Export Feedback <export_feedback.html>`_ first.


Breakdown
---------


Before querying the server, we need to login. A different way of logging
in, that is potentially more secure if multiple users need to use the
script, is by asking for the credentials in input. Fortunately, our
package comes equipped with such a utility, :func:`.codegrade.login_from_cli`.

.. code-block:: python

    import codegrade

    client = codegrade.login_from_cli()

We now need a user's id to get the information we need. We will use
:func:`.codegrade.utils.select_from_list`. We will first select a course
and then one of the users from the given course.

There is a catch, as :meth:`.CourseService.get_all_users` returns a
:class:`.Union` of both type :class:`.User` and :class:`.UserCourse`.
We will solve this by mapping objects of the latter type to the former
through :attr:`.UserCourse.user`.

.. code-block:: python

    all_courses = client.course.get_all()
    course = codegrade.utils.value_or_exit(
        codegrade.utils.select_from_list(
            'Select a course',
            all_courses,
            lambda c: c.name))

    all_users = list(map(
        lambda u: u if isinstance(u, codegrade.models.user.User) else u.user,
        client.course.get_all_users(course_id=course.id)))
    user = codegrade.utils.value_or_exit(
        codegrade.utils.select_from_list(
            'Select a user',
            all_users,
            lambda u: f'{u.name} ({u.username})'))

Now we can get all the users submissions through :meth:`.AssignmentService.get_submissions_by_user`.
As such, we first need to select an assignment for which we want the
user's progress.

.. code-block:: python

    assignment = codegrade.utils.value_or_exit(
        codegrade.utils.select_from_list(
            'Select an assignment',
            course.assignments,
            lambda a: a.name))

    submissions = client.assignment.get_submissions_by_user(
        assignment_id=assignemnt.id,
        user_id=user.id)

Now we can finally print the grades for the various submissions of
the given user for the given assignment.

.. code-block:: python

    for submission in submissions:
        print(f'Submission uploaded: {submission.created_at.isoformat()}'
              f' | Grade: {submission.grade}')


.. _complete-progress-script:

Complete Student Progress script
--------------------------------

.. container:: toggle

   .. container:: header

      Click here to see the copy-friendly script

   .. code-block:: python

        import codegrade

        # Login to CodeGrade
        client = codegrade.login_from_cli()

        # Get all courses and select the desired one
        all_courses = client.course.get_all()
        course = codegrade.utils.value_or_exit(
            codegrade.utils.select_from_list(
                'Select a course',
                all_courses,
                lambda c: c.name))

        # Get all course's users, map them to user types and select the desired one
        all_users = list(map(
            lambda u: u if isinstance(u, codegrade.models.user.User) else u.user,
            client.course.get_all_users(course_id=course.id)))
        user = codegrade.utils.value_or_exit(
            codegrade.utils.select_from_list(
                'Select a user',
                all_users,
                lambda u: f'{u.name} ({u.username})'))

        # Select desired assignment from course
        assignment = codegrade.utils.value_or_exit(
            codegrade.utils.select_from_list(
                'Select an assignment',
                course.assignments,
                lambda a: a.name))

        # Get all user's submissions for the given assignment
        submissions = client.assignment.get_submissions_by_user(
            assignment_id=assignment.id,
            user_id=user.id)

        # Loop over user's submissions and print the acheived grade
        for submission in submissions:
            print(f'Submission uploaded: {submission.created_at.isoformat()}'
                  f' | Grade: {submission.grade}')