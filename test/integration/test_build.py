import pytest
import os

from ansible_builder import constants

# Need to call this directly for multiple tag testing
from test.conftest import delete_image


@pytest.mark.test_all_runtimes
def test_build_fail_exitcode(cli, runtime, ee_tag, tmp_path, data_dir):
    """Test that when a build fails, the ansible-builder exits with non-zero exit code.

    Example: https://github.com/ansible/ansible-builder/issues/51
    """
    bc = tmp_path
    ee_def = data_dir / 'build_fail' / 'execution-environment.yml'
    r = cli(
        f"ansible-builder build -c {bc} -f {ee_def} -t {ee_tag} --container-runtime {runtime} -v3",
        allow_error=True
    )
    assert r.rc != 0, (r.stdout + r.stderr)
    assert 'RUN thisisnotacommand' in (r.stdout + r.stderr), (r.stdout + r.stderr)
    assert 'thisisnotacommand: command not found' in (r.stdout + r.stderr), (r.stdout + r.stderr)


@pytest.mark.test_all_runtimes
def test_blank_execution_environment(cli, runtime, ee_tag, tmp_path, data_dir):
    """Just makes sure that the build process does not require any particular input"""
    bc = tmp_path
    ee_def = data_dir / 'minimal_fast' / 'execution-environment.yml'
    cli(
        f'ansible-builder build -c {bc} -f {ee_def} -t {ee_tag} --container-runtime {runtime} --squash off'
    )
    result = cli(f'{runtime} run --rm {ee_tag} echo "This is a simple test"')
    assert 'This is a simple test' in result.stdout, result.stdout


@pytest.mark.test_all_runtimes
def test_multiple_tags(cli, runtime, ee_tag, tmp_path, data_dir):
    """Make sure multiple tagging works"""
    bc = tmp_path
    ee_def = data_dir / 'minimal_fast' / 'execution-environment.yml'
    cli(
        f'ansible-builder build -c {bc} -f {ee_def} -t {ee_tag} -t testmultitags --container-runtime {runtime} --squash off'
    )
    result = cli(f'{runtime} run --rm {ee_tag} echo "test: test_multiple_tags 1"')
    assert 'test: test_multiple_tags 1' in result.stdout, result.stdout

    result = cli(f'{runtime} run --rm testmultitags echo "test: test_multiple_tags 2"')
    assert 'test: test_multiple_tags 2' in result.stdout, result.stdout
    delete_image(runtime, 'testmultitags')


@pytest.mark.test_all_runtimes
def test_user_system_requirement(cli, runtime, ee_tag, tmp_path, data_dir):
    bc = tmp_path
    ee_def = data_dir / 'subversion' / 'execution-environment.yml'
    command = f'ansible-builder build -c {bc} -f {ee_def} -t {ee_tag} --container-runtime {runtime} --squash off'
    cli(command)
    result = cli(
        f'{runtime} run --rm {ee_tag} svn --help'
    )
    assert 'Subversion is a tool for version control' in result.stdout, result.stdout


@pytest.mark.test_all_runtimes
def test_collection_system_requirement(cli, runtime, ee_tag, tmp_path, data_dir):
    bc = tmp_path
    ee_def = data_dir / 'ansible.posix.at' / 'execution-environment.yml'
    cli(
        f'ansible-builder build -c {bc} -f {ee_def} -t {ee_tag} --container-runtime {runtime} -v3 --squash off'
    )
    result = cli(
        f'{runtime} run --rm {ee_tag} at -V'
    )
    assert 'at version' in result.stderr, result.stderr


@pytest.mark.test_all_runtimes
def test_user_python_requirement(cli, runtime, ee_tag, tmp_path, data_dir):
    bc = tmp_path
    ee_def = data_dir / 'pip' / 'execution-environment.yml'
    command = f'ansible-builder build -c {bc} -f {ee_def} -t {ee_tag} --container-runtime {runtime} --squash off'
    cli(command)
    result = cli(
        f'{runtime} run --rm {ee_tag} /usr/libexec/platform-python -m pip show awxkit'
    )
    assert 'The official command line interface for Ansible AWX' in result.stdout, result.stdout

    # TODO: not sure why we're checking for this be missing...
    for py_library in ('requirements-parser'):
        result = cli(
            f'{runtime} run --rm {ee_tag} /usr/libexec/platform-python -m pip show {py_library}', allow_error=True
        )
        assert result.rc != 0, py_library


@pytest.mark.test_all_runtimes
def test_python_git_requirement(cli, runtime, ee_tag, tmp_path, data_dir):
    # FIXME: is this test even necessary, since we don't (currently) special-case git in builder?

    bc = tmp_path
    ee_def = data_dir / 'needs_git' / 'execution-environment.yml'
    command = f'ansible-builder build -c {bc} -f {ee_def} -t {ee_tag} --container-runtime {runtime} --squash off'
    cli(command)
    result = cli(f'{runtime} run --rm {ee_tag} pip3 freeze')
    assert 'flask' in result.stdout.lower(), result.stdout


@pytest.mark.test_all_runtimes
def test_prepended_steps(cli, runtime, ee_tag, tmp_path, data_dir):
    """
    Tests that prepended steps are in final stage
    """
    bc = tmp_path

    # FIXME: share with an existing image for cached performance
    ee_def = data_dir / 'prepend_steps' / 'execution-environment.yml'
    cli(
        f'ansible-builder build -c {bc} -f {ee_def} -t {ee_tag} --container-runtime {runtime} --squash off'
    )

    result = cli(f"{runtime} run --rm {ee_tag} cat /baseout.txt")

    assert 'hello from prepend_base' in result.stdout


@pytest.mark.test_all_runtimes
def test_build_args_basic(cli, runtime, ee_tag, tmp_path, data_dir):
    bc = tmp_path
    ee_def = data_dir / 'build_args' / 'execution-environment.yml'
    result = cli(
        f'ansible-builder build -c {bc} -f {ee_def} -t {ee_tag} --container-runtime {runtime} --build-arg FOO=bar -v3 --no-cache'
    )
    assert 'FOO=bar' in result.stdout


@pytest.mark.test_all_runtimes
def test_build_args_from_environment(cli, runtime, ee_tag, tmp_path, data_dir):
    bc = tmp_path
    ee_def = data_dir / 'build_args' / 'execution-environment.yml'
    # need a unique value to avoid the cache for this, but don't want the perf hit of --no-cache
    os.environ['FOO'] = f'secretsecret_{ee_tag}'
    result = cli(
        f'ansible-builder build -c {bc} -f {ee_def} -t {ee_tag} --container-runtime {runtime} --build-arg FOO -v3 --squash off'
    )
    assert 'secretsecret_' in result.stdout


@pytest.mark.test_all_runtimes
def test_base_image_build_arg(cli, runtime, ee_tag, tmp_path, data_dir):
    bc = tmp_path
    ee_def = data_dir / 'build_args' / 'base-image.yml'
    os.environ['FOO'] = 'secretsecret'

    # Build with custom image tag, then use that as input to --build-arg EE_BASE_IMAGE
    cli(f'ansible-builder build -c {bc} -f {ee_def} -t {ee_tag} --container-runtime {runtime} -v3 --squash off')
    cli(f'ansible-builder build -c {bc} -f {ee_def} -t {ee_tag} '
        f'--container-runtime {runtime} --build-arg EE_BASE_IMAGE={ee_tag} -v3 --squash off')

    result = cli(f"{runtime} run --rm {ee_tag} cat /base_image")
    assert f"{ee_tag}" in result.stdout


@pytest.mark.test_all_runtimes
def test_has_pytz(cli, runtime, data_dir, ee_tag, tmp_path):
    ee_def = data_dir / 'pytz' / 'execution-environment.yml'
    cli(f'ansible-builder build -c {tmp_path} -f {ee_def} -t {ee_tag} --container-runtime {runtime} -v 3 --squash off')
    result = cli(f'{runtime} run --rm {ee_tag} pip3 show pytz')

    assert 'World timezone definitions, modern and historical' in result.stdout


# can trash the build cache, must be run independently and with the user's explicit consent
@pytest.mark.serial
@pytest.mark.destructive
@pytest.mark.test_all_runtimes
def test_build_layer_reuse(cli, runtime, data_dir, ee_tag, tmp_path):
    ee_def = data_dir / 'minimal_fast' / 'execution-environment.yml'

    containerfile_name = 'Dockerfile' if runtime == 'docker' else 'Containerfile'

    build_cmd = f'ansible-builder build -c {tmp_path} -f {ee_def} -t {ee_tag} --container-runtime {runtime} -v 3 --squash off'

    print(f"tempdir {tmp_path}")
    no_cache_result = cli(build_cmd + ' --no-cache')

    pass1_containerfile = (tmp_path / containerfile_name).read_text()

    print(f"no_cache_result stdout: \n{no_cache_result.stdout}")
    print(f"no_cache_result stderr: \n{no_cache_result.stderr}")
    print(f"containerfile contents for no-cache: \n{pass1_containerfile}")

    assert 'hi mom' in no_cache_result.stdout, no_cache_result.stdout

    cache_result = cli(build_cmd)
    pass2_containerfile = (tmp_path / containerfile_name).read_text()

    print(f"cache_result stdout: \n{cache_result.stdout}")
    print(f"cache_result stderr: \n{cache_result.stderr}")
    print(f"containerfile contents after cached run: \n{pass2_containerfile}")

    # Get the range of lines that contain the step we want to ensure used the cached layer
    out_lines = cache_result.stdout.splitlines()
    test_index = [idx for idx, value in enumerate(out_lines) if 'RUN echo "$(echo hi) $(echo mom)"' in value][0]

    assert pass1_containerfile == pass2_containerfile

    assert 'hi mom' not in cache_result.stdout, cache_result.stdout
    assert any('cache' in line.lower() for line in out_lines[test_index:])


@pytest.mark.test_all_runtimes
def test_collection_verification_off(cli, runtime, data_dir, ee_tag, tmp_path):
    """
    Test that, by default, collection verification is off via the env var.
    """
    # FIXME: we could still make this even a lot faster with `minimal_fast` plus aliasing `ansible-galaxy` to `/bin/true`
    ee_def = data_dir / 'pytz' / 'execution-environment.yml'
    result = cli(f'ansible-builder build --no-cache -c {tmp_path} -f {ee_def} -t {ee_tag} --container-runtime {runtime} -v 3')
    assert "RUN ANSIBLE_GALAXY_DISABLE_GPG_VERIFY=1 ansible-galaxy" in result.stdout


@pytest.mark.test_all_runtimes
def test_collection_verification_on(cli, runtime, data_dir, ee_tag, tmp_path):
    """
    Test that collection verification is on when given a keyring.
    """
    keyring = tmp_path / "mykeyring.gpg"
    keyring.touch()

    # FIXME: we could still make this even a lot faster with `minimal_fast` plus aliasing `ansible-galaxy` to `/bin/true`
    ee_def = data_dir / 'pytz' / 'execution-environment.yml'

    # ansible-galaxy might error (older Ansible), but that should be ok
    result = cli(f'ansible-builder build --no-cache --galaxy-keyring {keyring} -c {tmp_path} -f {ee_def} -t {ee_tag} --container-runtime {runtime} -v 3',
                 allow_error=True)

    keyring_copy = tmp_path / constants.user_content_subfolder / constants.default_keyring_name
    assert keyring_copy.exists()

    assert "RUN ANSIBLE_GALAXY_DISABLE_GPG_VERIFY=1 ansible-galaxy" not in result.stdout
    assert f"--keyring \"{constants.default_keyring_name}\"" in result.stdout


@pytest.mark.test_all_runtimes
def test_galaxy_signing_extra_args(cli, runtime, data_dir, ee_tag, tmp_path):
    """
    Test that all extra signing args for gpg are passed into the container file.
    """

    keyring = tmp_path / "mykeyring.gpg"
    keyring.touch()

    # FIXME: we could still make this even a lot faster with `minimal_fast` plus aliasing `ansible-galaxy` to `/bin/true`
    ee_def = data_dir / 'pytz' / 'execution-environment.yml'

    result = cli(f'ansible-builder build --no-cache -c {tmp_path} -f {ee_def} -t {ee_tag} --container-runtime {runtime} -v 3 '
                 f'--galaxy-keyring {keyring} --galaxy-ignore-signature-status-code NODATA '
                 f'--galaxy-required-valid-signature-count 3', allow_error=True)

    assert "--ignore-signature-status-code NODATA" in result.stdout
    assert "--required-valid-signature-count 3" in result.stdout
