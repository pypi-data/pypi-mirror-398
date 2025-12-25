=======
History
=======

0.3.1 (2025-12-22)
------------------

* `!21`_: Fixed incorrect handling of boolean values (--snow-pixels-only).
* `!22`_: Fixed AOT and AE handling in CLI.
* `!23`_: Replaced hyphens in CLI parameters with underscores.
* `!24`_: Added range checks for AOT, AE, and thresholds.


0.3.0 (2025-12-19)
------------------

* `!18`_: Implemented AOT and AE defaults as discussed in #1 (resolves #1).
* `!19`_: Made AOT and AE customizable by the user.
* `!6`_: Added snow and cloud screening to allow running retrievals only on snow pixels
  (threshold-based classification) (resolves #5 and #7). Added snow screening flag and
  thresholds as API and command line arguments.


0.2.2 (2025-12-01)
------------------

* `!17`_: Added decorator to dump argparse arguments if $IS_ENFROSP_GUI_TEST=1.
* Added separate environment file that only contains the requirements needed at runtime.


0.2.1 (2025-09-01)
------------------

* Dropped Python 3.8 support due to EOL status and added 3.12 and 3.13.
* `!15`_: Switched to hatchling build backend.
* `!16`_: Replaced deprecated license declaration in pyproject.toml.


0.2.0 (2025-08-29)
------------------

* Updated installation instructions.
* `!14`_: Added preliminary command line interface.


0.1.1 (2025-08-27)
------------------

* `!8`_: Updated GFZ URLs and institute name.
* `!9`_: Added gitleaks job to CI.
* `!10`_: Updated copyright.
* `!11`_: Revised license headers.
* `!12`_: Added CI job to deploy to PyPI.
* `!13`_: Added CI job to deploy to Zenodo.


0.1.0 (2025-01-31)
------------------

* Package skeleton as created by https://github.com/danschef/cookiecutter-pypackage.
* `!1`_: Moved command line interface to enfrosp.cli. Renamed entry point to 'enfrosp'.
* `!2`_: Adapted CI runner build script to upstream changes in GitLab 17.0. Bumped version of docker base image.
* `!3`_: Replaced setup.py + setup.cfg by pyproject.toml.
* `!4`_: Added prototypic EnMAP L1C reader.
* `!5`_: Added core algorithm to run snow retrievals over clean and polluted snow.

.. _!1: https://git.gfz.de/EnMAP/GFZ_Tools_EnMAP_BOX/enfrosp/-/merge_requests/1
.. _!2: https://git.gfz.de/EnMAP/GFZ_Tools_EnMAP_BOX/enfrosp/-/merge_requests/2
.. _!3: https://git.gfz.de/EnMAP/GFZ_Tools_EnMAP_BOX/enfrosp/-/merge_requests/3
.. _!4: https://git.gfz.de/EnMAP/GFZ_Tools_EnMAP_BOX/enfrosp/-/merge_requests/4
.. _!5: https://git.gfz.de/EnMAP/GFZ_Tools_EnMAP_BOX/enfrosp/-/merge_requests/5
.. _!6: https://git.gfz.de/EnMAP/GFZ_Tools_EnMAP_BOX/enfrosp/-/merge_requests/6
.. _!8: https://git.gfz.de/EnMAP/GFZ_Tools_EnMAP_BOX/enfrosp/-/merge_requests/8
.. _!9: https://git.gfz.de/EnMAP/GFZ_Tools_EnMAP_BOX/enfrosp/-/merge_requests/9
.. _!10: https://git.gfz.de/EnMAP/GFZ_Tools_EnMAP_BOX/enfrosp/-/merge_requests/10
.. _!11: https://git.gfz.de/EnMAP/GFZ_Tools_EnMAP_BOX/enfrosp/-/merge_requests/11
.. _!12: https://git.gfz.de/EnMAP/GFZ_Tools_EnMAP_BOX/enfrosp/-/merge_requests/12
.. _!13: https://git.gfz.de/EnMAP/GFZ_Tools_EnMAP_BOX/enfrosp/-/merge_requests/13
.. _!14: https://git.gfz.de/EnMAP/GFZ_Tools_EnMAP_BOX/enfrosp/-/merge_requests/14
.. _!15: https://git.gfz.de/EnMAP/GFZ_Tools_EnMAP_BOX/enfrosp/-/merge_requests/15
.. _!16: https://git.gfz.de/EnMAP/GFZ_Tools_EnMAP_BOX/enfrosp/-/merge_requests/16
.. _!17: https://git.gfz.de/EnMAP/GFZ_Tools_EnMAP_BOX/enfrosp/-/merge_requests/17
.. _!18: https://git.gfz.de/EnMAP/GFZ_Tools_EnMAP_BOX/enfrosp/-/merge_requests/18
.. _!19: https://git.gfz.de/EnMAP/GFZ_Tools_EnMAP_BOX/enfrosp/-/merge_requests/19
.. _!21: https://git.gfz.de/EnMAP/GFZ_Tools_EnMAP_BOX/enfrosp/-/merge_requests/21
.. _!22: https://git.gfz.de/EnMAP/GFZ_Tools_EnMAP_BOX/enfrosp/-/merge_requests/22
.. _!23: https://git.gfz.de/EnMAP/GFZ_Tools_EnMAP_BOX/enfrosp/-/merge_requests/23
.. _!24: https://git.gfz.de/EnMAP/GFZ_Tools_EnMAP_BOX/enfrosp/-/merge_requests/24
