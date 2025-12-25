dkist-processing-cryonirsp
==========================

|codecov|

Overview
--------
The dkist-processing-cryonirsp library contains the implementation of the cryonirsp pipelines as a collection of the
`dkist-processing-core <https://pypi.org/project/dkist-processing-core/>`_ framework and
`dkist-processing-common <https://pypi.org/project/dkist-processing-common/>`_ Tasks.

The recommended project structure is to separate tasks and workflows into separate packages.  Having the workflows
in their own package facilitates using the build_utils to test the integrity of those workflows in the unit test.

Environment Variables
---------------------

.. list-table::
   :widths: 10 90
   :header-rows: 1

   * - Variable
     - Field Info
   * - LOGURU_LEVEL
     - annotation=str required=False default='INFO' alias_priority=2 validation_alias='LOGURU_LEVEL' description='Log level for the application'
   * - MESH_CONFIG
     - annotation=dict[str, MeshService] required=False default_factory=dict alias_priority=2 validation_alias='MESH_CONFIG' description='Service mesh configuration' examples=[{'upstream_service_name': {'mesh_address': 'localhost', 'mesh_port': 6742}}]
   * - RETRY_CONFIG
     - annotation=RetryConfig required=False default_factory=RetryConfig description='Retry configuration for the service'
   * - OTEL_SERVICE_NAME
     - annotation=str required=False default='unknown-service-name' alias_priority=2 validation_alias='OTEL_SERVICE_NAME' description='Service name for OpenTelemetry'
   * - DKIST_SERVICE_VERSION
     - annotation=str required=False default='unknown-service-version' alias_priority=2 validation_alias='DKIST_SERVICE_VERSION' description='Service version for OpenTelemetry'
   * - NOMAD_ALLOC_ID
     - annotation=str required=False default='unknown-allocation-id' alias_priority=2 validation_alias='NOMAD_ALLOC_ID' description='Nomad allocation ID for OpenTelemetry'
   * - NOMAD_ALLOC_NAME
     - annotation=str required=False default='unknown-allocation-name' alias='NOMAD_ALLOC_NAME' alias_priority=2 description='Allocation name for the deployed container the task is running on.'
   * - NOMAD_GROUP_NAME
     - annotation=str required=False default='unknown-allocation-group' alias='NOMAD_GROUP_NAME' alias_priority=2 description='Allocation group for the deployed container the task is running on'
   * - OTEL_EXPORTER_OTLP_TRACES_INSECURE
     - annotation=bool required=False default=True description='Use insecure connection for OTLP traces'
   * - OTEL_EXPORTER_OTLP_METRICS_INSECURE
     - annotation=bool required=False default=True description='Use insecure connection for OTLP metrics'
   * - OTEL_EXPORTER_OTLP_TRACES_ENDPOINT
     - annotation=Union[str, NoneType] required=False default=None description='OTLP traces endpoint. Overrides mesh configuration' examples=['localhost:4317']
   * - OTEL_EXPORTER_OTLP_METRICS_ENDPOINT
     - annotation=Union[str, NoneType] required=False default=None description='OTLP metrics endpoint. Overrides mesh configuration' examples=['localhost:4317']
   * - OTEL_PYTHON_DISABLED_INSTRUMENTATIONS
     - annotation=list[str] required=False default_factory=list description='List of instrumentations to disable. https://opentelemetry.io/docs/zero-code/python/configuration/' examples=[['pika', 'requests']]
   * - OTEL_PYTHON_FASTAPI_EXCLUDED_URLS
     - annotation=str required=False default='health' description='Comma separated list of URLs to exclude from OpenTelemetry instrumentation in FastAPI.' examples=['client/.*/info,healthcheck']
   * - SYSTEM_METRIC_INSTRUMENTATION_CONFIG
     - annotation=Union[dict[str, bool], NoneType] required=False default=None description='Configuration for system metric instrumentation. https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/system_metrics/system_metrics.html' examples=[{'system.memory.usage': ['used', 'free', 'cached'], 'system.cpu.time': ['idle', 'user', 'system', 'irq'], 'system.network.io': ['transmit', 'receive'], 'process.runtime.memory': ['rss', 'vms'], 'process.runtime.cpu.time': ['user', 'system'], 'process.runtime.context_switches': ['involuntary', 'voluntary']}]
   * - ISB_USERNAME
     - annotation=str required=False default='guest' description='Username for the interservice-bus.'
   * - ISB_PASSWORD
     - annotation=str required=False default='guest' description='Password for the interservice-bus.'
   * - ISB_EXCHANGE
     - annotation=str required=False default='master.direct.x' description='Exchange for the interservice-bus.'
   * - ISB_QUEUE_TYPE
     - annotation=str required=False default='classic' description='Queue type for the interservice-bus.' examples=['quorum', 'classic']
   * - BUILD_VERSION
     - annotation=str required=False default='dev' description='Fallback build version for workflow tasks.'
   * - GQL_AUTH_TOKEN
     - annotation=Union[str, NoneType] required=False default='dev' description='The auth token for the metadata-store-api.'
   * - OBJECT_STORE_ACCESS_KEY
     - annotation=Union[str, NoneType] required=False default=None description='The access key for the object store.'
   * - OBJECT_STORE_SECRET_KEY
     - annotation=Union[str, NoneType] required=False default=None description='The secret key for the object store.'
   * - OBJECT_STORE_USE_SSL
     - annotation=bool required=False default=False description='Whether to use SSL for the object store connection.'
   * - MULTIPART_THRESHOLD
     - annotation=Union[int, NoneType] required=False default=None description='Multipart threshold for the object store.'
   * - S3_CLIENT_CONFIG
     - annotation=Union[dict, NoneType] required=False default=None description='S3 client configuration for the object store.'
   * - S3_UPLOAD_CONFIG
     - annotation=Union[dict, NoneType] required=False default=None description='S3 upload configuration for the object store.'
   * - S3_DOWNLOAD_CONFIG
     - annotation=Union[dict, NoneType] required=False default=None description='S3 download configuration for the object store.'
   * - GLOBUS_MAX_RETRIES
     - annotation=int required=False default=5 description='Max retries for transient errors on calls to the globus api.'
   * - GLOBUS_INBOUND_CLIENT_CREDENTIALS
     - annotation=list[GlobusClientCredential] required=False default_factory=list description='Globus client credentials for inbound transfers.' examples=[[{'client_id': 'id1', 'client_secret': 'secret1'}, {'client_id': 'id2', 'client_secret': 'secret2'}]]
   * - GLOBUS_OUTBOUND_CLIENT_CREDENTIALS
     - annotation=list[GlobusClientCredential] required=False default_factory=list description='Globus client credentials for outbound transfers.' examples=[[{'client_id': 'id3', 'client_secret': 'secret3'}, {'client_id': 'id4', 'client_secret': 'secret4'}]]
   * - OBJECT_STORE_ENDPOINT
     - annotation=Union[str, NoneType] required=False default=None description='Object store Globus Endpoint ID.'
   * - SCRATCH_ENDPOINT
     - annotation=Union[str, NoneType] required=False default=None description='Scratch Globus Endpoint ID.'
   * - SCRATCH_BASE_PATH
     - annotation=str required=False default='scratch/' description='Base path for scratch storage.'
   * - SCRATCH_INVENTORY_DB_COUNT
     - annotation=int required=False default=16 description='Number of databases in the scratch inventory (redis).'
   * - DOCS_BASE_URL
     - annotation=str required=False default='my_test_url' description='Base URL for the documentation site.'
   * - FTS_ATLAS_DATA_DIR
     - annotation=Union[str, NoneType] required=False default=None description='Common cached directory for a downloaded FTS Atlas.'

Development
-----------
.. code-block:: bash

    git clone git@bitbucket.org:dkistdc/dkist-processing-cryonirsp.git
    cd dkist-processing-cryonirsp
    pre-commit install
    pip install -e .[test]
    pytest -v --cov dkist_processing_cryonirsp

Build
-----
Artifacts are built through Bitbucket Pipelines.

The pipeline can be used in other repos with a modification of the package and artifact locations
to use the names relevant to the target repo.

e.g. dkist-processing-test -> dkist-processing-vbi and dkist_processing_test -> dkist_processing_vbi

Deployment
----------
Deployment is done with `turtlebot <https://bitbucket.org/dkistdc/turtlebot/src/main/>`_ and follows
the process detailed in `dkist-processing-core <https://pypi.org/project/dkist-processing-core/>`_

Additionally, when a new release is ready to be built the following steps need to be taken:

1. Freezing Dependencies
#########################

A new "frozen" extra is generated by the `dkist-dev-tools <https://bitbucket.org/dkistdc/dkist-dev-tools/src/main/>`_
package. If you don't have `dkist-dev-tools` installed please follow the directions from that repo.

To freeze dependencies run

.. code-block:: bash

    ddt freeze vX.Y.Z[rcK]

Where "vX.Y.Z[rcK]" is the version about to be released.

2. Changelog
############

When you make **any** change to this repository it **MUST** be accompanied by a changelog file.
The changelog for this repository uses the `towncrier <https://github.com/twisted/towncrier>`__ package.
Entries in the changelog for the next release are added as individual files (one per change) to the ``changelog/`` directory.

Writing a Changelog Entry
^^^^^^^^^^^^^^^^^^^^^^^^^

A changelog entry accompanying a change should be added to the ``changelog/`` directory.
The name of a file in this directory follows a specific template::

  <PULL REQUEST NUMBER>.<TYPE>[.<COUNTER>].rst

The fields have the following meanings:

* ``<PULL REQUEST NUMBER>``: This is the number of the pull request, so people can jump from the changelog entry to the diff on BitBucket.
* ``<TYPE>``: This is the type of the change and must be one of the values described below.
* ``<COUNTER>``: This is an optional field, if you make more than one change of the same type you can append a counter to the subsequent changes, i.e. ``100.bugfix.rst`` and ``100.bugfix.1.rst`` for two bugfix changes in the same PR.

The list of possible types is defined in the towncrier section of ``pyproject.toml``, the types are:

* ``feature``: This change is a new code feature.
* ``bugfix``: This is a change which fixes a bug.
* ``doc``: A documentation change.
* ``removal``: A deprecation or removal of public API.
* ``misc``: Any small change which doesn't fit anywhere else, such as a change to the package infrastructure.


Rendering the Changelog at Release Time
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When you are about to tag a release first you must run ``towncrier`` to render the changelog.
The steps for this are as follows:

* Run `towncrier build --version vx.y.z` using the version number you want to tag.
* Agree to have towncrier remove the fragments.
* Add and commit your changes.
* Tag the release.

**NOTE:** If you forget to add a Changelog entry to a tagged release (either manually or automatically with ``towncrier``)
then the Bitbucket pipeline will fail. To be able to use the same tag you must delete it locally and on the remote branch:

.. code-block:: bash

    # First, actually update the CHANGELOG and commit the update
    git commit

    # Delete tags
    git tag -d vWHATEVER.THE.VERSION
    git push --delete origin vWHATEVER.THE.VERSION

    # Re-tag with the same version
    git tag vWHATEVER.THE.VERSION
    git push --tags origin main

Science Changelog
^^^^^^^^^^^^^^^^^

Whenever a release involves changes to the scientific quality of L1 data, additional changelog fragment(s) should be
created. These fragments are intended to be as verbose as is needed to accurately capture the scope of the change(s),
so feel free to use all the fancy RST you want. Science fragments are placed in the same ``changelog/`` directory
as other fragments, but are always called::

  <PR NUMBER | +>.science[.<COUNTER>].rst

In the case that a single pull request encapsulates the entirety of the scientific change then the first field should
be that PR number (same as the normal CHANGELOG). If, however, there is not a simple mapping from a single PR to a scientific
change then use the character "+" instead; this will create a changelog entry with no associated PR. For example:

.. code-block:: bash

  $ ls changelog/
  99.bugfix.rst    # This is a normal changelog fragment associated with a bugfix in PR 99
  99.science.rst   # Apparently that bugfix also changed the scientific results, so that PR also gets a science fragment
  +.science.rst    # This fragment is not associated with a PR


When it comes time to build the SCIENCE_CHANGELOG, use the ``science_towncrier.sh`` script in this repo to do so.
This script accepts all the same arguments as the default `towncrier`. For example:

.. code-block:: bash

  ./science_towncrier.sh build --version vx.y.z

This will update the SCIENCE_CHANGELOG and remove any science fragments from the changelog directory.

3. Tag and Push
###############

Once all commits are in place add a git tag that will define the released version, then push the tags up to Bitbucket:

.. code-block:: bash

    git tag vX.Y.Z[rcK]
    git push --tags origin BRANCH

In the case of an rc, BRANCH will likely be your development branch. For full releases BRANCH should be "main".

.. |codecov| image:: https://codecov.io/bb/dkistdc/dkist-processing-cryonirsp/graph/badge.svg?token=TZBK64UKG5
   :target: https://codecov.io/bb/dkistdc/dkist-processing-cryonirsp
