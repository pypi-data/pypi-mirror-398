==========================
Contributing to bilby_pipe
==========================

Making releases
---------------

**Note:** releases should be made in coordination with other developers and,
doing so requires certain permissions.

Versioning
==========

We use `semantic versioning <https://semver.org/>`_ when creating bilby releases
and versions should have the format ``MAJOR.MINOR.PATCH``.
The version tag should also start with ``v`` e.g. ``v2.4.0``.

``bilby_pipe`` uses ``setuptools_scm`` to automatically set the version based on git tags.
This means no manual changes are needed to the version number are required.

Updating the changelog
======================

Before making a release, the `changelog <https://git.ligo.org/lscsoft/bilby_pipe/-/blob/master/CHANGELOG.md?ref_type=heads>`_
should be updated to include the changes since the last release. This should
be done by a new pull request.
We roughly follow the style proposed in `keep a changelog <https://keepachangelog.com/en/1.1.0/>`_

When making a changelog keep the following in mind:

- Only document meaningful changes to the code. Changes to, e.g., the CI or test suite do not need to be included.

Making a release on GitLab
==========================

To make a new release of bilby_pipe, first ensure the changelog is up-to-date.
Once this is done, follow these steps:

1. Navigate to https://git.ligo.org/lscsoft/bilby_pipe/-/releases
2. Click ``New release``
3. Specify the tag (e.g., v1.5.0). This should either be an existing tag or you can create new tag. If creating a new tag, ensure the `master` branch is selected.
4. (Optional) Select the corresponding milestone
5. Set the ``Release date`` as today
6. Copy the changelog notes into the ``Release notes`` box
7. Click ``Create release``

Once step 7 is complete, the CI will trigger and the new release will be 
automatically uploaded to PyPI. Check that the CI workflow completed successfully.
After this, you should see the new release on PyPI.

If you run into any issues, please contact Colm Talbot or Michael Williams.

Updating conda-forge
====================

`conda-forge` is not automatically updated when a new release is made, but an 
pull request should be opened automatically on the `bilby_pipe feedstock <https://github.com/conda-forge/bilby_pipe-feedstock>`_
(this can take up to a day). Once it is open, follow the steps in the pull request
to review and merge the changes.
