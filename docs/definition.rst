Execution Environment Definition
================================

The execution environment (EE) definition file supports multiple versions.

  * Version 1: Supported by all ``ansible-builder`` versions.
  * Version 2: Supported by ``ansible-builder`` versions ``1.2`` and later.
  * Version 3: Supported by ``ansible-builder`` versions ``2.0`` and later.

:ref:`Version 2 <version-2>` adds the capability to optionally use and verify
signed container images. This feature is only supported with the ``podman``
container runtime.

If the EE file does not specify a version, version 1 will be assumed.

.. _version-1:

Version 1 Format
----------------

Example V1
^^^^^^^^^^

.. code:: yaml

    ---
    version: 1

    build_arg_defaults:
      EE_BASE_IMAGE: 'quay.io/ansible/ansible-runner:latest'

    ansible_config: 'ansible.cfg'

    dependencies:
      galaxy: requirements.yml
      python: requirements.txt
      system: bindep.txt

    additional_build_steps:
      prepend: |
        RUN whoami
        RUN cat /etc/os-release
      append:
        - RUN echo This is a post-install command!
        - RUN ls -la /etc


The following keys are supported in this version of the EE file:

version
^^^^^^^

This integer value defines the version of the EE file. If not specified, the
default of ``1`` will be used.

build_arg_defaults
^^^^^^^^^^^^^^^^^^

Default values for build args can be specified in the definition file in
the ``build_arg_defaults`` section as a dictionary. This is an alternative
to using the ``--build-arg`` CLI flag.

Build args used by ``ansible-builder`` are the following:

``ANSIBLE_GALAXY_CLI_COLLECTION_OPTS``
  This allows the user to pass the '--pre' flag (or others) to enable the installation of pre-releases collections.

``ANSIBLE_GALAXY_CLI_ROLE_OPTS``
  This allows the user to pass the flags to the Role installation.

``EE_BASE_IMAGE``
  This string value specifies the parent image for the execution environment.

``EE_BUILDER_IMAGE``
  This string value specifies the image used for compiling type tasks.

Values given inside of ``build_arg_defaults`` will be hard-coded into the
Containerfile, so they will persist if ``podman build`` is called manually.

If the same variable is specified in the CLI ``--build-arg`` flag,
the CLI value will take higher precedence.

ansible_config
^^^^^^^^^^^^^^

When using an ``ansible.cfg`` file to pass a token and other settings for a
private account to an Automation Hub server, listing the config file path here
(as a string) will enable it to be included as a build argument in the initial
phase of the build.

.. _dependencies_v1:

dependencies
^^^^^^^^^^^^

This section is a dictionary value that is used to define the Ansible Galaxy,
Python, and system dependencies that must be installed into the final container.
Valid keys for this section are:

``galaxy``
  This string value is the path to a file containing the Ansible Galaxy
  dependencies to be installed with the ``ansible-galaxy collection install -r ...``
  command.

  The supplied value may be a relative path from the directory of the execution
  environment definition's folder, or an absolute path.

``python``
  This string value is the path to a file containing the Python dependencies
  to be installed with the ``pip install -r ...`` command.

  The supplied value may be a relative path from the directory of the execution
  environment definition's folder, or an absolute path.

``system``
  This string value is points to a
  `bindep <https://docs.openstack.org/infra/bindep/readme.html>`__
  requirements file. This will be processed by ``bindep`` and then passed
  to ``dnf``, other platforms are not yet supported.

additional_build_steps
^^^^^^^^^^^^^^^^^^^^^^

Additional commands may be specified in the ``additional_build_steps``
section, either for before the main build steps (``prepend``) or after
(``append``). The syntax needs to be one of the following:

- a multi-line string (example shown in the ``prepend`` section above)
- a list (as shown via ``append``)

.. _version-2:

Version 2 Format
----------------

Changes from the :ref:`version 1 <version-1>` format are noted below. Any
new configuration sections, or major changes to existing sections, are
documented below as well.

Changes from V1
^^^^^^^^^^^^^^^^

* A new ``images`` key is added that supports more complex definitions of the
  base and builder images. Image signature validation is supported, based on
  the value of the :ref:`container-policy` CLI option. (See note below.)
* Defining ``EE_BASE_IMAGE`` or ``EE_BUILDER_IMAGE`` in the ``build_args_defaults``
  section, or with the :ref:`build-arg` CLI option, is no longer allowed.

.. note::

    Although builder will create a `policy.json` file (see :ref:`images-v2` section
    below) to control Podman image validation, it is up to the user to properly
    configure the Podman runtime to talk to the registries needed. This may include
    defining the sigstore for each registry, using secure connections (or not), etc.
    Such configuration is beyond the scope of this document.

Example V2
^^^^^^^^^^

An example version 2 execution environment definition schema is as follows:

.. code:: yaml

    ---
    version: 2

    build_arg_defaults:
      ANSIBLE_GALAXY_CLI_COLLECTION_OPTS: '--pre'

    dependencies:
      galaxy: requirements.yml
      python: requirements.txt
      system: bindep.txt

    images:
      base_image:
        name: registry.redhat.io/ansible-automation-platform-21/ee-minimal-rhel8:latest
      builder_image:
        name: my-mirror.example.com/aap-mirror/ansible-builder-rhel8:latest
        signature_original_name: registry.redhat.io/ansible-automation-platform-21/ansible-builder-rhel8:latest

.. _images-v2:

images
^^^^^^

This section is a dictionary that is used to define the base and builder images.
How this data is used in relation to a Podman
`policy.json <https://github.com/containers/image/blob/main/docs/containers-policy.json.5.md>`_
file for container image signature validation depends on the value of the
:ref:`container-policy` CLI option.

  * ``ignore_all`` policy: Generate a `policy.json` file in the build
    :ref:`context directory <context>` where no signature validation is
    performed. This duplicates the functionality under the
    :ref:`version 1 format<version-1>`.

  * ``system`` policy: Signature validation is performed using pre-existing
    `policy.json` files in standard system locations. ``ansible-builder`` assumes
    no responsibility for the content within these files, and the user has complete
    control over the content.

  * ``signature_required`` policy: ``ansible-builder`` will use the container
    image definitions here to generate a `policy.json` file in the build
    :ref:`context directory <context>` that will be used during the build to
    validate the images.

Valid keys for this section are:

``base_image``
  A dictionary defining the parent image for the execution environment. A ``name``
  key must be supplied with the container image to use. Use the ``signature_original_name``
  key if the image is mirrored within your repository, but signed with the original
  image's signature key. Image names *MUST* contain a tag, such as ``:latest``.

``builder_image``
  A dictionary defining the image used for compiling type tasks.  A ``name``
  key must be supplied with the container image to use. Use the ``signature_original_name``
  key if the image is mirrored within your repository, but signed with the original
  image's signature key. Image names *MUST* contain a tag, such as ``:latest``.

.. _version-3:

Version 3 Format
----------------

Changes from the :ref:`version 2 <version-2>` format are noted below. Any
new configuration sections, or major changes to existing sections, are
documented below as well.

Changes from V2
^^^^^^^^^^^^^^^

* The ``images`` section no longer supports the ``builder_image`` key.
* The ``ansible_config`` keyword is removed. Similar functionality can be
  achieved through the use of ``additional_build_steps`` and ``additional_build_files``
  (see below for an example).
* The ``additional_build_steps`` section allows for specifying additional commands
  either before or after each of the four build phases (base/galaxy/builder/final).
  The :ref:`version 1 <version-1>` format supported this for only the final build stage.
* A new ``additional_build_files`` section allows for including any file in
  the build context to be referenced at any image build stage.
* The ``dependencies`` section supports the new keys ``ansible_core``,
  ``ansible_runner``, and ``python_interpreter``. It also supports inline values
  for the existing keys. See :ref:`below for more information <dependencies_v3>`.

Example V3
^^^^^^^^^^

An example version 3 execution environment definition schema is as follows:

.. code:: yaml

    ---
    version: 3

    build_arg_defaults:
      ANSIBLE_GALAXY_CLI_COLLECTION_OPTS: '--pre'

    dependencies:
      galaxy: requirements.yml
      python:
        - six
        - psutil
      system: bindep.txt

    images:
      base_image:
        name: registry.redhat.io/ansible-automation-platform-21/ee-minimal-rhel8:latest

    additional_build_files:
        - src: files/ansible.cfg
          dest: configs

    additional_build_steps:
      prepend_galaxy:
        - ADD _build/configs/ansible.cfg ~/.ansible.cfg

      prepend_final: |
        RUN whoami
        RUN cat /etc/os-release
      append_final:
        - RUN echo This is a post-install command!
        - RUN ls -la /etc

additional_build_steps (v3)
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Similar to the version 2 format, you can specify custom build commands in this
section, but for all build phases.

Below are the valid keys for this section. Each supports either a multi-line
string, or a list of strings. The ``prepend`` and ``append`` keys are no longer
supported.

``prepend_base``
  Commands to insert before building of the base image.

``append_base``
  Commands to insert after building of the base image.

``prepend_galaxy``
  Commands to insert before building of the galaxy image.

``append_galaxy``
  Commands to insert after building of the galaxy image.

``prepend_builder``
  Commands to insert before building of the builder image.

``append_builder``
  Commands to insert after building of the builder image.

``prepend_final``
  Commands to insert before building of the final image. This is the equivalent
  of the ``prepend`` version 2 keyword.

``append_final``
  Commands to insert after building of the final image. This is the equivalent
  of the ``append`` version 2 keyword.

additional_build_files
^^^^^^^^^^^^^^^^^^^^^^

This section allows you to add any file to the build context directory. These can
then be referenced at any of image build stages. The format is a list of dictionary
values, each with a ``src`` and ``dest`` key and value.

Each list item must be a dictionary containing the following (non-optional) keys:

``src``
  Specifies the source file(s) to copy into the build context directory. This
  may either be an absolute path (e.g., ``/home/user/.ansible.cfg``),
  or a path that is relative to the execution environment file. Relative paths may be
  a regular expression matching one or more files (e.g. ``files/*.cfg``). Note
  that the absolute path may *not* include a regular expression. If ``src`` is
  a directory, the entire contents of that directory are copied to ``dest``.

``dest``
  Specifies a subdirectory path underneath the ``_build`` subdirectory of the
  build context directory that should contain the source file(s) (e.g., ``files/configs``).
  This may not be an absolute path or contain ``..`` within the path. This directory
  will be created for you if it does not exist.

.. _dependencies_v3:

dependencies (v3)
^^^^^^^^^^^^^^^^^

The ``dependencies`` section for version 3 is similar to its
:ref:`version 1 counterpart <dependencies_v1>`. The exception is that three new
keywords are added, and the values of the existing ``galaxy``, ``python`` and
``system`` keys may either be the name of a file, or inline representations
of those files. The ``python`` and ``system`` values can be a list of dependency
values, but the ``galaxy`` value must be a string representation of the Galaxy
requirements YAML.

For example, this format is supported in all versions:

.. code:: yaml

    dependencies:
        python: requirements.txt
        system: bindep.txt
        galaxy: requirements.yml

And this format, only supported in version 3, uses inline values:

.. code:: yaml

    dependencies:
        python:
          - pywinrm
        system:
          - iputils [platform:rpm]
        galaxy: |
          collections:
            - community.windows
            - ansible.utils

.. note::

  The ``|`` symbol is a YAML operator that allows you to define a block of text
  that may contain newline characters as a literal string. Because the ``galaxy``
  requirements content is expressed in YAML, we need this value to be a string
  of YAML so that we can pass it along to ``ansible-galaxy``.

The following are new keywords added for this section:

``ansible_core``
  The version of the Ansible python package to be installed by pip into the
  base image.

``ansible_runner``
  The version of the Ansible Runner python package to be installed by pip into the
  base image.

``python_interpreter``
  A dictionary that defines the Python system package name to be installed by
  dnf (``package_name``) into the base image and/or a path to the Python
  interpreter to be used (``python_path``).

Below is an example of how to use these new keywords:

.. code:: yaml

    dependencies:
        ansible_core: ansible-core==2.14.2
        ansible_runner: ansible-runner==2.3.1
        python_interpreter:
            package_name: "python310"
            python_path: "/usr/bin/python3.10"
