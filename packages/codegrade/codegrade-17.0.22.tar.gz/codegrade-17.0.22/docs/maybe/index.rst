:hide-toc: true


Maybe
=====


.. toctree::
   :maxdepth: 1
   :glob:
   :hidden:


   *


.. currentmodule:: cg_maybe.maybe

.. class:: Maybe


The ``Maybe`` class is used in CodeGrade to define variables that
are not certain to have an actual value. To represent this we use a
special value, :class:`._Nothing`. Any value is instead stored in
a :class:`.Just` object.