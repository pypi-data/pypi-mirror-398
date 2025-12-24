import json
import os
import pytest
from unittest.mock import patch
from sagemaker_jupyterlab_extension_common.jumpstart.constants import (
    DEFAULT_PYTHON3_KERNEL_SPEC,
    FETCH_CODE_COMMIT_CREDENTIALS,
    CODE_COMMIT_CLONE_TEMPLATE,
)
from sagemaker_jupyterlab_extension_common.jumpstart.notebook_transformation import (
    InferNotebook,
    OpenSourceNotebook,
    _get_substitute_cell,
    _is_cell_removal,
    _is_cell_replacement,
    _replace_line_with_none,
    _should_remove_cell,
    _should_remove_trainer_cell,
    update_notebook,
)
from sagemaker_jupyterlab_extension_common.jumpstart.notebook_types import (
    JumpStartModelNotebookAlterationType,
    JumpStartModelNotebookGlobalActionType,
    JumpStartModelNotebookSubstitution,
    JumpStartModelNotebookSubstitutionTarget,
    UpdateHubNotebookUpdateOptions,
)
from sagemaker_jupyterlab_extension_common.util.app_metadata import (
    get_region_name,
)


@pytest.fixture
def basic_notebook_content():
    return {
        "cells": [
            {
                "cell_type": "code",
                "execution_count": None,
                "source": [],
                "metadata": {},
                "outputs": [],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "source": [],
                "metadata": {},
                "outputs": [],
            },
        ],
        "metadata": {
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
            "version": "3.8.13",
            "kernelspec": {
                "display_name": "Initial Python Kernel",
                "language": "python",
                "name": "initialpython",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


@pytest.mark.parametrize(
    "target, expected",
    [
        ("test-endpoint-name", 'endpoint_name="test-endpoint-name"'),
        (None, "endpoint_name=None"),
    ],
)
def test_replace_line_with_none(target, expected):
    line = 'endpoint_name="!!!name!!!"'
    find = "!!!name!!!"
    assert expected == _replace_line_with_none(line, find, target)


@pytest.mark.parametrize(
    "alteration_type,expected",
    [
        (JumpStartModelNotebookAlterationType.modelIdVersion, True),
        (JumpStartModelNotebookAlterationType.modelIdOnly, True),
        (JumpStartModelNotebookAlterationType.dropModelSelection, False),
        (JumpStartModelNotebookAlterationType.dropForDeploy, False),
        (JumpStartModelNotebookAlterationType.dropForTraining, False),
        (JumpStartModelNotebookAlterationType.clusterName, True),
        (JumpStartModelNotebookAlterationType.clusterId, True),
        (JumpStartModelNotebookAlterationType.hyperPodStudio, True),
        (JumpStartModelNotebookAlterationType.hyperPodUnifiedStudio, True),
        (JumpStartModelNotebookAlterationType.getRecipePath, True),
        (JumpStartModelNotebookAlterationType.getExtractedRecipePath, True),
        (JumpStartModelNotebookAlterationType.cloneRepository, True),
        (JumpStartModelNotebookAlterationType.fetchCodeCommitCredentials, True),
        (
            JumpStartModelNotebookAlterationType.novaTrainingJobNotebookHeaderMarkdown,
            True,
        ),
        (JumpStartModelNotebookAlterationType.novaHyperpodNotebookHeaderMarkdown, True),
        (JumpStartModelNotebookAlterationType.trainerSelection, False),
    ],
)
def test_is_cell_replacement(alteration_type, expected):
    assert expected == _is_cell_replacement(alteration_type)


@pytest.mark.parametrize(
    "alteration_type,expected",
    [
        (JumpStartModelNotebookAlterationType.modelIdVersion, False),
        (JumpStartModelNotebookAlterationType.modelIdOnly, False),
        (JumpStartModelNotebookAlterationType.dropModelSelection, True),
        (JumpStartModelNotebookAlterationType.dropForDeploy, True),
        (JumpStartModelNotebookAlterationType.dropForTraining, True),
        (
            JumpStartModelNotebookAlterationType.novaTrainingJobNotebookHeaderMarkdown,
            False,
        ),
        (
            JumpStartModelNotebookAlterationType.novaHyperpodNotebookHeaderMarkdown,
            False,
        ),
        (JumpStartModelNotebookAlterationType.trainerSelection, False),
    ],
)
def test_is_cell_removal(alteration_type, expected):
    assert expected == _is_cell_removal(alteration_type)


@pytest.mark.parametrize(
    "alteration_type,expected",
    [
        (JumpStartModelNotebookAlterationType.modelIdVersion.value, False),
        (JumpStartModelNotebookAlterationType.modelIdOnly.value, False),
        (JumpStartModelNotebookAlterationType.dropModelSelection.value, True),
        (JumpStartModelNotebookAlterationType.dropForDeploy.value, True),
        (JumpStartModelNotebookAlterationType.dropForTraining.value, True),
        (None, False),
        ("invalidType", False),
    ],
)
def test_should_remove_cell(alteration_type, expected):
    if alteration_type:
        cell = {"metadata": {"jumpStartAlterations": [f"{alteration_type}"]}}
    else:
        cell = {"metadata": {}}
    assert expected == _should_remove_cell(cell)


@pytest.mark.parametrize(
    "trainer_type,selected_technique,expected",
    [
        ("SFT", "SFT", False),  # Keep matching trainer
        ("DPO", "SFT", True),  # Remove non-matching trainer
        ("RLVR", "DPO", True),  # Remove non-matching trainer
        (None, "SFT", False),  # No trainer_type metadata
    ],
)
def test_should_remove_trainer_cell(trainer_type, selected_technique, expected):
    cell = {
        "metadata": {
            "jumpStartAlterations": ["trainerSelection"],
            "trainer_type": trainer_type,
        }
    }
    assert expected == _should_remove_trainer_cell(cell, selected_technique)


@pytest.mark.parametrize(
    "alteration_type,expected",
    [
        (
            JumpStartModelNotebookAlterationType.modelIdVersion.value,
            ['model_id, model_version = "test_model_id", "*"'],
        ),
        (
            JumpStartModelNotebookAlterationType.modelIdOnly.value,
            ['model_id = "test_model_id"'],
        ),
        (
            JumpStartModelNotebookAlterationType.modelInitHubName.value,
            [
                'model = JumpStartModel(model_id=model_id, model_version=model_version, hub_name="test_hub_name")'
            ],
        ),
        (
            JumpStartModelNotebookAlterationType.clusterId.value,
            [
                "%%bash\n",
                f"aws ssm start-session --target sagemaker-cluster:test-eks --region {get_region_name()}",
            ],
        ),
        (
            JumpStartModelNotebookAlterationType.clusterName.value,
            ["!hyperpod connect-cluster --cluster-name test-eks"],
        ),
        (
            JumpStartModelNotebookAlterationType.hyperPodStudio.value,
            ['HYPERPOD_CLUSTER_NAME = "test-eks"'],
        ),
        (
            JumpStartModelNotebookAlterationType.hyperPodUnifiedStudio.value,
            [
                f'HYPERPOD_CLUSTER_NAME = "test-eks"\n',
                f'DOMAIN_ID = "d-23jk672h5"\n',
                f'CONNECTION_ID = "c-23jk672h5"',
            ],
        ),
        (
            JumpStartModelNotebookAlterationType.getRecipePath.value,
            [
                'recipe_path = "./sagemaker-hyperpod-recipes/recipes_collection/recipes/training/nova/recipe.yaml"'
            ],
        ),
        (
            JumpStartModelNotebookAlterationType.cloneRepository.value,
            [CODE_COMMIT_CLONE_TEMPLATE],
        ),
        (
            JumpStartModelNotebookAlterationType.fetchCodeCommitCredentials.value,
            [FETCH_CODE_COMMIT_CREDENTIALS],
        ),
        (
            JumpStartModelNotebookAlterationType.getExtractedRecipePath.value,
            ['os.environ["RECIPE"] = "training/nova/recipe"'],
        ),
        (
            JumpStartModelNotebookAlterationType.novaTrainingJobNotebookHeaderMarkdown.value,
            ["# 🚀 Nova | Training using SageMaker Training Job"],
        ),
        (
            JumpStartModelNotebookAlterationType.novaHyperpodNotebookHeaderMarkdown.value,
            ["# 🚀 Nova | Training using SageMaker HyperPod"],
        ),
        (
            JumpStartModelNotebookAlterationType.openSourceTrainingJobNotebookHeaderMarkdown.value,
            ["# 🚀 Llama | Fine-tuning using SageMaker Training Job"],
        ),
        (
            JumpStartModelNotebookAlterationType.openSourceHyperpodNotebookHeaderMarkdown.value,
            ["# 🚀 Llama | Fine-tuning using SageMaker HyperPod"],
        ),
        (
            JumpStartModelNotebookAlterationType.novaTrainingJobNotebookEstimatorCode.value,
            [],  # With training_type="training", this should return empty source since condition needs "evaluation"
        ),
        (
            JumpStartModelNotebookAlterationType.estimatorInitHubName.value,
            [
                (
                    "estimator = JumpStartEstimator(\n"
                    "        model_id=train_model_id,\n"
                    "        hyperparameters=hyperparameters,\n"
                    "        instance_type=training_instance_type,\n"
                    '        hub_name="test_hub_name",\n'
                    ")"
                )
            ],
        ),
        (
            None,
            [],
        ),
    ],
)
def test_get_substitute_cell(alteration_type, expected):
    model_id = "test_model_id"
    hub_name = "test_hub_name"
    cluster_id = "test-eks"
    connection_id = "c-23jk672h5"
    domain = "d-23jk672h5"
    recipe_path = "/recipes/training/nova/recipe.yaml"
    training_type = "training"
    nova_model_name = "nova"
    model_name = "llama"
    git_clone_url = CODE_COMMIT_CLONE_TEMPLATE
    is_prime = True

    if alteration_type:
        current_cell = {
            "metadata": {"jumpStartAlterations": [f"{alteration_type}"]},
            "source": [],
        }
    else:
        current_cell = {"metadata": {}, "source": []}
    assert (
        expected
        == _get_substitute_cell(
            model_id,
            current_cell,
            hub_name=hub_name,
            recipe_path=recipe_path,
            training_type=training_type,
            nova_model_name=nova_model_name,
            model_name=model_name,
            git_clone_url=git_clone_url,
            is_prime=is_prime,
            cluster_id=cluster_id,
            connection_id=connection_id,
            domain=domain,
        )["source"]
    )


def test_get_substitute_cell_with_evaluation_training_type():
    """Test _get_substitute_cell with the novaTrainingJobNotebookEstimatorCode alteration and evaluation training type."""
    model_id = "test_model_id"
    training_type = "evaluation"
    recipe_path = "/recipes/training/nova/recipe.yaml"
    nova_model_name = "nova"

    current_cell = {
        "metadata": {
            "jumpStartAlterations": [
                JumpStartModelNotebookAlterationType.novaTrainingJobNotebookEstimatorCode.value
            ]
        },
        "source": [],
    }

    result = _get_substitute_cell(
        model_id,
        current_cell,
        recipe_path=recipe_path,
        training_type=training_type,
        nova_model_name=nova_model_name,
    )

    # Expected PyTorch estimator code for evaluation
    expected_source = [
        "from sagemaker.pytorch import PyTorch\n",
        "\n",
        "estimator = PyTorch(\n",
        "    image_uri=image_uri,\n",
        "    base_job_name=base_job_name,\n",
        "    role=role_arn,\n",
        "    instance_type=instance_type,\n",
        "    training_recipe=recipe_path,\n",
        "    sagemaker_session=sagemaker_session,\n",
        "    output_path=output_s3_uri,\n",
        "    tensorboard_output_config=tensorboard_output_config, # For data augmentation distillation, the following TensorBoard configuration must be disabled (commented out).\n",
        "    tags=[\n",
        '        {"Key": "is-model-evaluation-job", "Value": "true"},\n',
        "    ],\n",
        "    # subnets=[], # Specify subnets for data augmentation distillation job.\n",
        "    # security_group_ids=[] # Specify security_group_ids for data augmentation distillation job.\n",
        ")",
    ]

    assert result["source"] == expected_source


@pytest.mark.parametrize(
    "content,error_message",
    [
        ("invalid_json_content", "Notebook is not a valid JSON"),
        ("{}", "Notebook validation failed"),
    ],
)
def test_update_notebook_with_invalid_notebook(content, error_message):
    options = UpdateHubNotebookUpdateOptions([], [], [])
    with pytest.raises(ValueError, match=error_message):
        update_notebook(content, None, options)


def test_update_notebook_with_valid_notebook():
    options = UpdateHubNotebookUpdateOptions([], [], [])
    content = {
        "cells": [],
        "metadata": {
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
            "version": "3.8.13",
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    content_str = json.dumps(content)
    assert content_str == update_notebook(content_str, None, options)


def test_update_notebook_with_drop_cell_operation():
    alterations = [
        JumpStartModelNotebookAlterationType.dropModelSelection,
    ]
    options = UpdateHubNotebookUpdateOptions([], alterations, [])
    content = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {"jumpStartAlterations": ["dropModelSelection"]},
                "source": ["content"],
            }
        ],
        "metadata": {
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
            "version": "3.8.13",
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    content_str = json.dumps(content)
    assert 0 == len(json.loads(update_notebook(content_str, None, options))["cells"])


def test_update_notebook_with_model_id_substitution():
    alterations = [
        JumpStartModelNotebookAlterationType.modelIdOnly,
    ]
    options = UpdateHubNotebookUpdateOptions([], alterations, [])
    content = {
        "cells": [
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {"jumpStartAlterations": ["modelIdOnly"]},
                "source": ["content"],
                "outputs": [],
            }
        ],
        "metadata": {
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
            "version": "3.8.13",
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    content_str = json.dumps(content)
    assert ['model_id = "mock_model_id"'] == json.loads(
        update_notebook(content_str, "mock_model_id", options)
    )["cells"][0]["source"]


def test_update_notebook_with_model_version_substitution():
    alterations = [
        JumpStartModelNotebookAlterationType.modelIdVersion,
    ]
    options = UpdateHubNotebookUpdateOptions([], alterations, [])
    content = {
        "cells": [
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {"jumpStartAlterations": ["modelIdVersion"]},
                "source": ["content"],
                "outputs": [],
            }
        ],
        "metadata": {
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
            "version": "3.8.13",
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    content_str = json.dumps(content)
    assert ['model_id, model_version = "mock_model_id", "*"'] == json.loads(
        update_notebook(content_str, "mock_model_id", options)
    )["cells"][0]["source"]


def test_update_notebook_with_estimator_hub_name_substitution():
    alterations = [
        JumpStartModelNotebookAlterationType.estimatorInitHubName,
    ]
    options = UpdateHubNotebookUpdateOptions([], alterations, [])
    content = {
        "cells": [
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {
                    "jumpStartAlterations": ["jumpStartEstimatorInitOptionalHubName"]
                },
                "source": ["content"],
                "outputs": [],
            }
        ],
        "metadata": {
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
            "version": "3.8.13",
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    content_str = json.dumps(content)
    assert [
        (
            "estimator = JumpStartEstimator(\n"
            "        model_id=train_model_id,\n"
            "        hyperparameters=hyperparameters,\n"
            "        instance_type=training_instance_type,\n"
            '        hub_name="mock_hub_name",\n'
            ")"
        )
    ] == json.loads(
        update_notebook(
            content_str, "random_model_id", options, hubName="mock_hub_name"
        )
    )[
        "cells"
    ][
        0
    ][
        "source"
    ]


def test_update_notebook_with_model_hub_name_substitution():
    alterations = [
        JumpStartModelNotebookAlterationType.modelInitHubName,
    ]
    options = UpdateHubNotebookUpdateOptions([], alterations, [])
    content = {
        "cells": [
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {
                    "jumpStartAlterations": ["jumpStartModelInitOptionalHubName"]
                },
                "source": ["content"],
                "outputs": [],
            }
        ],
        "metadata": {
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
            "version": "3.8.13",
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    content_str = json.dumps(content)
    assert [
        'model = JumpStartModel(model_id=model_id, model_version=model_version, hub_name="mock_hub_name")'
    ] == json.loads(
        update_notebook(
            content_str, "random_model_id", options, hubName="mock_hub_name"
        )
    )[
        "cells"
    ][
        0
    ][
        "source"
    ]


def test_update_notebook_without_estimator_hub_name_substitution():
    alterations = [
        JumpStartModelNotebookAlterationType.estimatorInitHubName,
    ]
    options = UpdateHubNotebookUpdateOptions([], alterations, [])
    expected = "mock_content"
    content = {
        "cells": [
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {
                    "jumpStartAlterations": ["jumpStartEstimatorInitOptionalHubName"]
                },
                "source": [f"{expected}"],
                "outputs": [],
            }
        ],
        "metadata": {
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
            "version": "3.8.13",
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    content_str = json.dumps(content)
    assert [expected] == json.loads(
        update_notebook(content_str, "random_model_id", options, hubName=None)
    )["cells"][0]["source"]


def test_update_notebook_without_model_hub_name_substitution():
    alterations = [
        JumpStartModelNotebookAlterationType.modelInitHubName,
    ]
    options = UpdateHubNotebookUpdateOptions([], alterations, [])
    expected = "mock_content"
    content = {
        "cells": [
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {
                    "jumpStartAlterations": ["jumpStartModelInitOptionalHubName"]
                },
                "source": [f"{expected}"],
                "outputs": [],
            }
        ],
        "metadata": {
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
            "version": "3.8.13",
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    content_str = json.dumps(content)
    assert [expected] == json.loads(
        update_notebook(content_str, "random_model_id", options, hubName=None)
    )["cells"][0]["source"]


def test_update_notebook_with_global_drop_markdow():
    globalActions = [
        JumpStartModelNotebookGlobalActionType.dropAllMarkdown,
    ]
    options = UpdateHubNotebookUpdateOptions([], [], globalActions)
    content = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {"jumpStartAlterations": ["dropAllMarkdown"]},
                "source": ["content"],
            }
        ],
        "metadata": {
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
            "version": "3.8.13",
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    content_str = json.dumps(content)
    assert 0 == len(json.loads(update_notebook(content_str, None, options))["cells"])


def test_update_notebook_with_endpoint_name_substitution(basic_notebook_content):
    substitutions = [
        JumpStartModelNotebookSubstitution(
            JumpStartModelNotebookSubstitutionTarget.endpointName,
            "mock-endpoint-name",
            True,
        ),
        JumpStartModelNotebookSubstitution(
            JumpStartModelNotebookSubstitutionTarget.inferenceComponentBoto3,
            "mock-inference-component-name",
            True,
        ),
    ]
    options = UpdateHubNotebookUpdateOptions(substitutions, [], [])
    basic_notebook_content["cells"][0]["source"] = ["endpointName=!!!name!!!"]
    basic_notebook_content["cells"][1]["source"] = ["EndpointName=endpoint_name"]
    content_str = json.dumps(basic_notebook_content)
    result = json.loads(update_notebook(content_str, None, options))
    assert "endpointName=mock-endpoint-name" == result["cells"][0]["source"][0]
    assert "mock-inference-component-name" == result["cells"][1]["source"][0]


@pytest.mark.parametrize(
    "inference_component_name,expected_replacement",
    [
        ("inference-component-name", '"inference-component-name"'),
        (None, None),
    ],
)
def test_inference_component_name_substitution(
    basic_notebook_content, inference_component_name, expected_replacement
):
    notebook_transformer = InferNotebook()
    basic_notebook_content["cells"][0]["source"] = [
        'component_name="!!!component_name!!!"'
    ]

    result_json = notebook_transformer.transform(
        json.dumps(basic_notebook_content),
        "test-endpoint-name",
        inference_component_name,
    )
    result = json.loads(result_json)

    expected_source = f"component_name={expected_replacement}"
    assert (
        result["cells"][0]["source"][0] == expected_source
    ), f"The inference component name was not correctly substituted with {expected_replacement}."


@pytest.mark.parametrize(
    "component_name,expected_modification",
    [
        ("inference-component-name", True),
        (None, False),
    ],
)
def test_endpoint_name_and_component_substitution(
    basic_notebook_content, component_name, expected_modification
):
    notebook_transformer = InferNotebook()
    basic_notebook_content["cells"][0]["source"] = [
        "predictor = retrieve_default(endpoint_name)"
    ]

    result_json = notebook_transformer.transform(
        json.dumps(basic_notebook_content), "test-endpoint-name", component_name
    )
    result = json.loads(result_json)

    if expected_modification:
        expected_source = f"predictor = retrieve_default(endpoint_name=endpoint_name, inference_component_name='{component_name}')"
    else:
        expected_source = "predictor = retrieve_default(endpoint_name)"

    assert (
        result["cells"][0]["source"][0] == expected_source
    ), f"Substitution mismatch. Expected: {expected_source}."


def test_multiple_substitutions_single_cell(basic_notebook_content):
    notebook_transformer = InferNotebook()
    basic_notebook_content["cells"][0]["source"] = [
        'endpoint_name = "!!!name!!!"; component_name = "!!!component_name!!!"'
    ]

    endpoint_name = "test-endpoint"
    component_name = "test-component"
    result_json = notebook_transformer.transform(
        json.dumps(basic_notebook_content), endpoint_name, component_name
    )
    result = json.loads(result_json)

    expected_source = (
        f'endpoint_name = "{endpoint_name}"; component_name = "{component_name}"'
    )

    assert (
        result["cells"][0]["source"][0] == expected_source
    ), "The method did not correctly perform multiple substitutions within a single cell."


def test_substitution_with_no_placeholder(basic_notebook_content):
    notebook_transformer = InferNotebook()
    basic_notebook_content["cells"][0]["source"] = ['print("Hello, world!")']

    content_str_without_placeholders = json.dumps(basic_notebook_content)

    transformed_result_json = notebook_transformer.transform(
        content_str_without_placeholders, "any-endpoint-name", "any-component-name"
    )
    transformed_result = json.loads(transformed_result_json)

    expected_source_without_placeholders = 'print("Hello, world!")'

    assert (
        transformed_result["cells"][0]["source"][0]
        == expected_source_without_placeholders
    ), "Content without placeholders was unexpectedly modified."


@pytest.mark.parametrize(
    "endpoint_name,component_name,expected_endpoint_replacement,expected_component_replacement",
    [
        ("9" * 62, "3" * 62, '"' + "9" * 62 + '"', '"' + "3" * 62 + '"'),
        ("name", "component_name", '"name"', '"component_name"'),
    ],
)
def test_edge_cases_in_notebook_substitution(
    basic_notebook_content,
    endpoint_name,
    component_name,
    expected_endpoint_replacement,
    expected_component_replacement,
):
    notebook_transformer = InferNotebook()
    basic_notebook_content["cells"][0]["source"] = [
        'endpoint_name = "!!!name!!!"; component_name = "!!!component_name!!!"'
    ]

    result_json = notebook_transformer.transform(
        json.dumps(basic_notebook_content), endpoint_name, component_name
    )
    result = json.loads(result_json)

    expected_source = f"endpoint_name = {expected_endpoint_replacement}; component_name = {expected_component_replacement}"

    assert (
        result["cells"][0]["source"][0] == expected_source
    ), "Edge case handling failed for substitutions."


def test_kernel_spec_update(basic_notebook_content):
    notebook_json_str = json.dumps(basic_notebook_content)

    notebook_transformer = InferNotebook()

    transformed_notebook_str = notebook_transformer.transform(
        notebook_json_str, endpoint_name="dummy_endpoint", set_default_kernel=True
    )
    transformed_notebook = json.loads(transformed_notebook_str)
    assert (
        transformed_notebook["metadata"]["kernelspec"] == DEFAULT_PYTHON3_KERNEL_SPEC
    ), "The kernel_spec was not updated correctly."


def test_base_model_name_substitution(basic_notebook_content):
    """Test substitution of base_model_name with serverless parameter"""
    substitutions = [
        JumpStartModelNotebookSubstitution(
            JumpStartModelNotebookSubstitutionTarget.baseModelName,
            'BASE_MODEL = "llama-3-1-8b"',
            True,
        )
    ]
    options = UpdateHubNotebookUpdateOptions(substitutions, [], [])
    basic_notebook_content["cells"][0]["source"] = ['BASE_MODEL = ""']
    content_str = json.dumps(basic_notebook_content)
    result = json.loads(update_notebook(content_str, None, options))
    assert 'BASE_MODEL = "llama-3-1-8b"' == result["cells"][0]["source"][0]


def test_customization_technique_substitution(basic_notebook_content):
    """Test substitution of customization_technique with serverless parameter"""
    substitutions = [
        JumpStartModelNotebookSubstitution(
            JumpStartModelNotebookSubstitutionTarget.customizationTechnique,
            'CUSTOMIZATION_TECHNIQUE = "SFT"',
            True,
        )
    ]
    options = UpdateHubNotebookUpdateOptions(substitutions, [], [])
    basic_notebook_content["cells"][0]["source"] = ['CUSTOMIZATION_TECHNIQUE = ""']
    content_str = json.dumps(basic_notebook_content)
    result = json.loads(update_notebook(content_str, None, options))
    assert 'CUSTOMIZATION_TECHNIQUE = "SFT"' == result["cells"][0]["source"][0]


def test_model_package_group_name_substitution(basic_notebook_content):
    """Test substitution of model_package_group_name with serverless parameter"""
    substitutions = [
        JumpStartModelNotebookSubstitution(
            JumpStartModelNotebookSubstitutionTarget.modelPackageGroupName,
            'MODEL_PACKAGE_GROUP_NAME = "my-model-group"',
            True,
        )
    ]
    options = UpdateHubNotebookUpdateOptions(substitutions, [], [])
    basic_notebook_content["cells"][0]["source"] = ['MODEL_PACKAGE_GROUP_NAME = ""']
    content_str = json.dumps(basic_notebook_content)
    result = json.loads(update_notebook(content_str, None, options))
    assert (
        'MODEL_PACKAGE_GROUP_NAME = "my-model-group"' == result["cells"][0]["source"][0]
    )


def test_dataset_arn_substitution(basic_notebook_content):
    """Test substitution of dataset_arn with serverless parameter"""
    substitutions = [
        JumpStartModelNotebookSubstitution(
            JumpStartModelNotebookSubstitutionTarget.dataSetArn,
            'TRAINING_DATASET = "arn:aws:sagemaker:us-west-2:123456789012:hub-content/AIRegistry/DataSet/my-dataset/v1"',
            True,
        )
    ]
    options = UpdateHubNotebookUpdateOptions(substitutions, [], [])
    basic_notebook_content["cells"][0]["source"] = ['TRAINING_DATASET = ""']
    content_str = json.dumps(basic_notebook_content)
    result = json.loads(update_notebook(content_str, None, options))
    assert (
        'TRAINING_DATASET = "arn:aws:sagemaker:us-west-2:123456789012:hub-content/AIRegistry/DataSet/my-dataset/v1"'
        == result["cells"][0]["source"][0]
    )


def test_serverless_multiple_substitutions(basic_notebook_content):
    """Test multiple serverless SMTJ substitutions in one cell"""
    substitutions = [
        JumpStartModelNotebookSubstitution(
            JumpStartModelNotebookSubstitutionTarget.baseModelName,
            'BASE_MODEL = "llama-3-1-8b"',
            True,
        ),
        JumpStartModelNotebookSubstitution(
            JumpStartModelNotebookSubstitutionTarget.customizationTechnique,
            'CUSTOMIZATION_TECHNIQUE = "DPO"',
            True,
        ),
    ]
    options = UpdateHubNotebookUpdateOptions(substitutions, [], [])
    basic_notebook_content["cells"][0]["source"] = [
        'BASE_MODEL = ""',
        'CUSTOMIZATION_TECHNIQUE = ""',
    ]
    content_str = json.dumps(basic_notebook_content)
    result = json.loads(update_notebook(content_str, None, options))
    assert 'BASE_MODEL = "llama-3-1-8b"' == result["cells"][0]["source"][0]
    assert 'CUSTOMIZATION_TECHNIQUE = "DPO"' == result["cells"][0]["source"][1]


@patch(
    "sagemaker_jupyterlab_extension_common.jumpstart.notebook_transformation.get_aws_account_id"
)
def test_open_source_notebook_serverless_e2e_transformation(mock_aws_account):
    """Comprehensive e2e test for OpenSourceNotebook serverless SMTJ transformation"""
    mock_aws_account.return_value = "123456789012"

    # Create comprehensive test notebook with multiple cell types
    notebook_content = {
        "cells": [
            # Header cell - should be transformed
            {
                "cell_type": "markdown",
                "metadata": {
                    "jumpStartAlterations": [
                        "openSourceTrainingJobNotebookHeaderMarkdown"
                    ]
                },
                "source": ["# Original Header"],
            },
            # Parameter substitution cells - should be transformed
            {
                "cell_type": "code",
                "metadata": {},
                "source": ['BASE_MODEL = ""'],
                "execution_count": None,
                "outputs": [],
            },
            {
                "cell_type": "code",
                "metadata": {},
                "source": ['CUSTOMIZATION_TECHNIQUE = ""'],
                "execution_count": None,
                "outputs": [],
            },
            {
                "cell_type": "code",
                "metadata": {},
                "source": ['MODEL_PACKAGE_GROUP_NAME = ""'],
                "execution_count": None,
                "outputs": [],
            },
            {
                "cell_type": "code",
                "metadata": {},
                "source": ['TRAINING_DATASET = ""'],
                "execution_count": None,
                "outputs": [],
            },
            # Trainer selection cells - DPO should remain, SFT should be removed
            {
                "cell_type": "code",
                "metadata": {
                    "jumpStartAlterations": ["trainerSelection"],
                    "trainer_type": "DPO",
                },
                "source": ["# DPO Trainer Code"],
                "execution_count": None,
                "outputs": [],
            },
            {
                "cell_type": "code",
                "metadata": {
                    "jumpStartAlterations": ["trainerSelection"],
                    "trainer_type": "SFT",
                },
                "source": ["# SFT Trainer Code"],
                "execution_count": None,
                "outputs": [],
            },
        ],
        "metadata": {"nbformat": 4, "nbformat_minor": 5},
        "nbformat": 4,
        "nbformat_minor": 5,
    }

    notebook_str = json.dumps(notebook_content)

    # Transform with serverless SMTJ parameters
    transformer = OpenSourceNotebook()
    result = transformer.transform(
        notebook_str,
        baseModelName="meta-llama-3-2-1b-instruct",
        customizationTechnique="DPO",
        modelPackageGroupName="test-dpo-model-group",
        dataSetName="dpo-preference-dataset",
        dataSetVersion="2.1",
    )

    result_json = json.loads(result)

    # Test 1: Header transformation
    header_cell = result_json["cells"][0]
    expected_header = (
        "# 🚀 Meta-llama-3-2-1b-instruct | Fine-tuning using SageMaker Training Job"
    )
    assert header_cell["source"][0] == expected_header

    # Test 2: Parameter substitutions
    assert (
        'BASE_MODEL = "meta-llama-3-2-1b-instruct"'
        == result_json["cells"][1]["source"][0]
    )
    assert 'CUSTOMIZATION_TECHNIQUE = "DPO"' == result_json["cells"][2]["source"][0]
    assert (
        'MODEL_PACKAGE_GROUP_NAME = "test-dpo-model-group"'
        == result_json["cells"][3]["source"][0]
    )
    assert (
        'TRAINING_DATASET = "arn:aws:sagemaker:us-west-2:123456789012:hub-content/AIRegistry/DataSet/dpo-preference-dataset/2.1"'
        in result_json["cells"][4]["source"][0]
    )

    # Test 3: Trainer selection (cell removal)
    # Should have 6 cells total: header + 4 parameter cells + 1 DPO trainer (SFT trainer removed)
    assert len(result_json["cells"]) == 6

    # Find the remaining trainer cell
    trainer_cells = [
        cell
        for cell in result_json["cells"]
        if "Trainer Code" in str(cell.get("source", []))
    ]
    assert len(trainer_cells) == 1
    assert trainer_cells[0]["source"] == ["# DPO Trainer Code"]


def test_open_source_notebook_hyperpod_mode():
    """Test OpenSourceNotebook transform with HyperPod parameters - full e2e"""

    notebook_content = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {
                    "jumpStartAlterations": ["openSourceHyperpodNotebookHeaderMarkdown"]
                },
                "source": ["# Original Header"],
            },
            {
                "cell_type": "code",
                "metadata": {"jumpStartAlterations": ["hyperPodStudio"]},
                "source": ['HYPERPOD_CLUSTER_NAME = ""'],
                "execution_count": None,
                "outputs": [],
            },
            {
                "cell_type": "code",
                "metadata": {"jumpStartAlterations": ["getRecipePath"]},
                "source": ['recipe_path = ""'],
                "execution_count": None,
                "outputs": [],
            },
            {
                "cell_type": "code",
                "metadata": {},
                "source": ['hyperpod_launcher_path = ""'],
                "execution_count": None,
                "outputs": [],
            },
        ],
        "metadata": {"nbformat": 4, "nbformat_minor": 5},
        "nbformat": 4,
        "nbformat_minor": 5,
    }

    transformer = OpenSourceNotebook()
    result = transformer.transform(
        json.dumps(notebook_content),
        clusterId="test-hyperpod-cluster",
        connectionId="test-connection-id",
        domain="test-domain",
        recipePath="/recipes/fine-tuning/llama/llmft_llama3_2_1b_instruct_seq4k_gpu_dpo.yaml",
    )

    result_json = json.loads(result)

    # Test header transformation
    assert (
        "# 🚀 Llama | Fine-tuning using SageMaker HyperPod"
        == result_json["cells"][0]["source"][0]
    )

    # Test HyperPod cluster name substitution
    assert (
        'HYPERPOD_CLUSTER_NAME = "test-hyperpod-cluster"'
        == result_json["cells"][1]["source"][0]
    )

    # Test recipe path transformation
    assert (
        'recipe_path = "./sagemaker-hyperpod-recipes/recipes_collection/recipes/fine-tuning/llama/llmft_llama3_2_1b_instruct_seq4k_gpu_dpo.yaml"'
        == result_json["cells"][2]["source"][0]
    )

    # Test launcher path transformation
    assert (
        'hyperpod_launcher_path = "llama/run_llmft_llama3_2_1b_instruct_seq4k_gpu_dpo.sh"'
        == result_json["cells"][3]["source"][0]
    )


def test_open_source_notebook_serverless_optional_parameters():
    """Test OpenSourceNotebook with optional serverless parameters - some missing"""

    notebook_content = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {
                    "jumpStartAlterations": [
                        "openSourceTrainingJobNotebookHeaderMarkdown"
                    ]
                },
                "source": ["# Original Header"],
            },
            {
                "cell_type": "code",
                "metadata": {},
                "source": ['BASE_MODEL = ""'],
                "execution_count": None,
                "outputs": [],
            },
            {
                "cell_type": "code",
                "metadata": {},
                "source": ['CUSTOMIZATION_TECHNIQUE = ""'],
                "execution_count": None,
                "outputs": [],
            },
            {
                "cell_type": "code",
                "metadata": {},
                "source": ['MODEL_PACKAGE_GROUP_NAME = ""'],
                "execution_count": None,
                "outputs": [],
            },
            {
                "cell_type": "code",
                "metadata": {},
                "source": ['TRAINING_DATASET = ""'],
                "execution_count": None,
                "outputs": [],
            },
        ],
        "metadata": {"nbformat": 4, "nbformat_minor": 5},
        "nbformat": 4,
        "nbformat_minor": 5,
    }

    notebook_str = json.dumps(notebook_content)

    # Transform with only some serverless SMTJ parameters (others are None)
    transformer = OpenSourceNotebook()
    result = transformer.transform(
        notebook_str,
        baseModelName="llama-3-1-8b",  # Provided
        customizationTechnique=None,  # Not provided
        modelPackageGroupName=None,  # Not provided
        dataSetName="my-dataset",  # Provided
        dataSetVersion=None,  # Not provided (so no dataset ARN)
    )

    result_json = json.loads(result)

    # Test: Only provided parameters should be substituted
    # baseModelName was provided - should be substituted
    assert 'BASE_MODEL = "llama-3-1-8b"' == result_json["cells"][1]["source"][0]

    # customizationTechnique was None - should keep original value
    assert 'CUSTOMIZATION_TECHNIQUE = ""' == result_json["cells"][2]["source"][0]

    # modelPackageGroupName was None - should keep original value
    assert 'MODEL_PACKAGE_GROUP_NAME = ""' == result_json["cells"][3]["source"][0]

    # dataSetName provided but dataSetVersion None - should keep original value
    assert 'TRAINING_DATASET = ""' == result_json["cells"][4]["source"][0]


def test_open_source_notebook_serverless_no_parameters():
    """Test OpenSourceNotebook with no serverless parameters - should not error"""

    notebook_content = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {
                    "jumpStartAlterations": [
                        "openSourceTrainingJobNotebookHeaderMarkdown"
                    ]
                },
                "source": ["# Original Header"],
            },
            {
                "cell_type": "code",
                "metadata": {},
                "source": ['BASE_MODEL = ""'],
                "execution_count": None,
                "outputs": [],
            },
        ],
        "metadata": {"nbformat": 4, "nbformat_minor": 5},
        "nbformat": 4,
        "nbformat_minor": 5,
    }

    notebook_str = json.dumps(notebook_content)

    # Transform with NO serverless SMTJ parameters (all None)
    transformer = OpenSourceNotebook()
    result = transformer.transform(
        notebook_str,
        baseModelName=None,
        customizationTechnique=None,
        modelPackageGroupName=None,
        dataSetName=None,
        dataSetVersion=None,
    )

    result_json = json.loads(result)

    # Test: Should not error and should keep original template values
    assert 'BASE_MODEL = ""' == result_json["cells"][1]["source"][0]

    # Header should preserve original template since no model_name provided
    assert result_json["cells"][0]["source"][0] == "# Original Header"
