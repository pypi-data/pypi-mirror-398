"""This notebook util is translated based on
https://code.amazon.com/packages/RhinestoneSagemakerUI/blobs/mainline/--/packages/sagemaker-ui-graphql-server/src/services/penny/utils/notebookUtils.ts
https://code.amazon.com/packages/SageMakerHubJavascriptSDK/blobs/mainline/--/src/utils/notebookUtils.ts

TODO: refactor the update notebook logic to make it more clear and efficient
"""

import json
import os
import re
import logging
from typing import List, Optional
from sagemaker_jupyterlab_extension_common.jumpstart.constants import (
    DEFAULT_PYTHON3_KERNEL_SPEC,
    JUMPSTART_ALTERATIONS,
    REMOVAL_OPERATIONS,
    FETCH_CODE_COMMIT_CREDENTIALS,
    CODE_COMMIT_CLONE_TEMPLATE,
    PUBLIC_REPO_CLONE_TEMPLATE,
)
from sagemaker_jupyterlab_extension_common.jumpstart.notebook_types import (
    JumpStartModelNotebookAlterationType,
    JumpStartModelNotebookGlobalActionType,
    JumpStartModelNotebookSubstitution,
    JumpStartModelNotebookSubstitutionTarget,
    JumpStartModelNotebookMetadataUpdateType,
    JumpStartNotebookNames,
    UpdateHubNotebookUpdateOptions,
)
from abc import ABC, abstractmethod
import nbformat
from sagemaker_jupyterlab_extension_common.jumpstart.nova_prime_validator import (
    check_prime_status,
)

from sagemaker_jupyterlab_extension_common.util.app_metadata import (
    get_region_name,
    get_aws_account_id,
)


def _replace_line_with_none(line: str, find: str, replace: Optional[str]) -> str:
    if replace:
        return line.replace(find, replace)
    else:
        return line.replace(f'"{find}"', str(None))


def _is_cell_replacement(alteration: JumpStartModelNotebookAlterationType) -> bool:
    if (
        alteration == JumpStartModelNotebookAlterationType.modelIdVersion
        or alteration == JumpStartModelNotebookAlterationType.modelIdOnly
        or alteration == JumpStartModelNotebookAlterationType.clusterName
        or alteration == JumpStartModelNotebookAlterationType.clusterId
        or alteration == JumpStartModelNotebookAlterationType.hyperPodStudio
        or alteration == JumpStartModelNotebookAlterationType.hyperPodUnifiedStudio
        or alteration == JumpStartModelNotebookAlterationType.estimatorInitHubName
        or alteration == JumpStartModelNotebookAlterationType.modelInitHubName
        or alteration == JumpStartModelNotebookAlterationType.getRecipePath
        or alteration == JumpStartModelNotebookAlterationType.getExtractedRecipePath
        or alteration == JumpStartModelNotebookAlterationType.cloneRepository
        or alteration == JumpStartModelNotebookAlterationType.fetchCodeCommitCredentials
        or alteration
        == JumpStartModelNotebookAlterationType.novaTrainingJobNotebookHeaderMarkdown
        or alteration
        == JumpStartModelNotebookAlterationType.novaHyperpodNotebookHeaderMarkdown
        or alteration
        == JumpStartModelNotebookAlterationType.openSourceTrainingJobNotebookHeaderMarkdown
        or alteration
        == JumpStartModelNotebookAlterationType.openSourceHyperpodNotebookHeaderMarkdown
    ):
        return True
    return False


def _is_cell_removal(alteration: JumpStartModelNotebookAlterationType) -> bool:
    if (
        alteration == JumpStartModelNotebookAlterationType.dropModelSelection
        or alteration == JumpStartModelNotebookAlterationType.dropForDeploy
        or alteration == JumpStartModelNotebookAlterationType.dropForTraining
    ):
        return True
    return False


def _should_remove_cell(notebook_cell: dict) -> bool:
    cell_alterations = notebook_cell["metadata"].get(JUMPSTART_ALTERATIONS)
    if not cell_alterations:
        return False
    try:
        return any(
            JumpStartModelNotebookAlterationType(alteration) in REMOVAL_OPERATIONS
            for alteration in cell_alterations
        )
    except ValueError:
        return False


def _should_remove_trainer_cell(notebook_cell: dict, selected_technique: str) -> bool:
    """Remove trainer cells that don't match the selected technique"""
    cell_alterations = notebook_cell["metadata"].get(JUMPSTART_ALTERATIONS)
    if not cell_alterations:
        return False

    if (
        JumpStartModelNotebookAlterationType.trainerSelection.value
        not in cell_alterations
    ):
        return False

    trainer_type = notebook_cell["metadata"].get("trainer_type")
    return trainer_type is not None and trainer_type != selected_technique


def _get_substitute_cell(
    model_id: str,
    current_cell: dict,
    cluster_id: Optional[str] = None,
    model_name: Optional[str] = None,
    hub_name: Optional[str] = None,
    connection_id: Optional[str] = None,
    domain: Optional[str] = None,
    training_type: Optional[str] = None,
    nova_model_name: Optional[str] = None,
    recipe_path: Optional[str] = None,
    git_clone_url: Optional[str] = None,
    is_prime: Optional[bool] = None,
) -> dict:
    current_alterations = current_cell.get("metadata", {}).get(
        JUMPSTART_ALTERATIONS, []
    )
    if not current_alterations:
        return current_cell
    # currently for each cell we only support one alteration
    current_alteration = current_alterations[0]
    if current_alteration == JumpStartModelNotebookAlterationType.modelIdVersion.value:
        current_cell["source"] = [f'model_id, model_version = "{model_id}", "*"']
    elif current_alteration == JumpStartModelNotebookAlterationType.modelIdOnly.value:
        current_cell["source"] = [f'model_id = "{model_id}"']
    elif current_alteration == JumpStartModelNotebookAlterationType.clusterId.value:
        current_cell["source"] = [
            "%%bash\n",
            f"aws ssm start-session --target sagemaker-cluster:{cluster_id} --region {get_region_name()}",
        ]
    elif current_alteration == JumpStartModelNotebookAlterationType.clusterName.value:
        current_cell["source"] = [
            f"!hyperpod connect-cluster --cluster-name {cluster_id}"
        ]
    elif (
        current_alteration
        == JumpStartModelNotebookAlterationType.estimatorInitHubName.value
        and hub_name
    ):
        substitution = (
            "estimator = JumpStartEstimator(\n"
            "        model_id=train_model_id,\n"
            "        hyperparameters=hyperparameters,\n"
            "        instance_type=training_instance_type,\n"
            f'        hub_name="{hub_name}",\n'
            ")"
        )
        current_cell["source"] = [substitution]
    elif (
        current_alteration
        == JumpStartModelNotebookAlterationType.modelInitHubName.value
        and hub_name
    ):
        substitution = f'model = JumpStartModel(model_id=model_id, model_version=model_version, hub_name="{hub_name}")'
        current_cell["source"] = [substitution]
    elif (
        current_alteration == JumpStartModelNotebookAlterationType.hyperPodStudio.value
    ):
        current_cell["source"] = [f'HYPERPOD_CLUSTER_NAME = "{cluster_id}"']
    elif (
        current_alteration
        == JumpStartModelNotebookAlterationType.hyperPodUnifiedStudio.value
    ):
        current_cell["source"] = [
            f'HYPERPOD_CLUSTER_NAME = "{cluster_id}"\n',
            f'DOMAIN_ID = "{domain}"\n',
            f'CONNECTION_ID = "{connection_id}"',
        ]
    # For SageMaker Training Job pass the recipe path
    elif current_alteration == JumpStartModelNotebookAlterationType.getRecipePath.value:
        if recipe_path is None:
            raise ValueError("recipe_path cannot be None for getRecipePath alteration")
        current_cell["source"] = [
            f'recipe_path = "./sagemaker-hyperpod-recipes/recipes_collection{recipe_path}"'
        ]
    # For hyperpod start-job pass the extracted recipe path
    elif (
        current_alteration
        == JumpStartModelNotebookAlterationType.getExtractedRecipePath.value
    ):
        if recipe_path is None:
            raise ValueError(
                "recipe_path cannot be None for getExtractedRecipePath alteration"
            )
        extracted_recipe_name = os.path.splitext(
            recipe_path.replace("/recipes/", "", 1)
        )[0]
        current_cell["source"] = [f'os.environ["RECIPE"] = "{extracted_recipe_name}"']
    elif (
        current_alteration
        == JumpStartModelNotebookAlterationType.novaTrainingJobNotebookHeaderMarkdown.value
    ):
        current_cell["source"] = [
            f"# 🚀 {nova_model_name.capitalize()} | {training_type.capitalize()} using SageMaker Training Job"
        ]
    elif (
        current_alteration
        == JumpStartModelNotebookAlterationType.novaTrainingJobNotebookEstimatorCode.value
        and training_type.lower() == JumpStartNotebookNames.evaluation.value
    ):
        current_cell["source"] = [
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
    elif (
        current_alteration
        == JumpStartModelNotebookAlterationType.openSourceTrainingJobNotebookHeaderMarkdown.value
    ):
        if model_name:
            current_cell["source"] = [
                f"# 🚀 {model_name.capitalize()} | Fine-tuning using SageMaker Training Job"
            ]
        # If model_name is None, keep original header from notebook template
    elif (
        current_alteration
        == JumpStartModelNotebookAlterationType.openSourceHyperpodNotebookHeaderMarkdown.value
    ):
        if model_name:
            current_cell["source"] = [
                f"# 🚀 {model_name.capitalize()} | Fine-tuning using SageMaker HyperPod"
            ]
        # If model_name is None, keep original header from notebook template
    elif (
        current_alteration == JumpStartModelNotebookAlterationType.cloneRepository.value
    ):
        current_cell["source"] = [git_clone_url]
    elif (
        current_alteration
        == JumpStartModelNotebookAlterationType.fetchCodeCommitCredentials.value
        and is_prime
    ):
        current_cell["source"] = [FETCH_CODE_COMMIT_CREDENTIALS]
    elif (
        current_alteration
        == JumpStartModelNotebookAlterationType.novaHyperpodNotebookHeaderMarkdown.value
    ):
        current_cell["source"] = [
            f"# 🚀 {nova_model_name.capitalize()} | {training_type.capitalize()} using SageMaker HyperPod"
        ]
    return current_cell


def update_notebook(
    content: str,
    modelId: Optional[str],
    options: UpdateHubNotebookUpdateOptions,
    modelName: Optional[str] = None,
    clusterId: Optional[str] = None,
    hubName: Optional[str] = None,
    connectionId: Optional[str] = None,
    domain: Optional[str] = None,
    trainingType: Optional[str] = None,
    novaModelName: Optional[str] = None,
    recipePath: Optional[str] = None,
    gitCloneUrl: Optional[str] = None,
    isPrime: Optional[bool] = None,
) -> str:
    """notebook transformation logic. it contains 3 options types to transform the notebook.
    1. remove cells required to be dropped.
    2. replace cells required to be replaced.
    3. substitute part of the cells based on endpoint_name and/or inference_component_name

    :param content: notebook content
    :param modelId: model id
    :param options: update notebook options
    :param clusterId: cluster id
    :param hubName: private hub name
    :param connectionId: connectionid for Unified Studio
    :param domain: domain for Unified Studio
    :param trainingType: training strategy for the model
    :param novaModelName: name of the nova model
    :param recipePath: path to the recipe in the repository
    :param gitCloneUrl: url that clones either codecommit or github repo
    :param isPrime: True if prime verified
    :return: transformed notebook content.
    :raises ValueError: if notebook is not a valid JSON or if notebook validation fails.
    """
    try:
        nb = json.loads(content)
    except json.decoder.JSONDecodeError as je:
        raise ValueError(f"Notebook is not a valid JSON: {je}")

    # validate notebook by using nbformat version 4 schema
    # https://github.com/jupyter/nbformat/blob/main/nbformat/v4/nbformat.v4.schema.json
    try:
        nbformat.validate(nb, version=4)
    except nbformat.reader.ValidationError as ve:
        raise ValueError(f"Notebook validation failed: {ve}")

    completedSubstitutions = set()
    remove_alterations = [
        alteration for alteration in options.alterations if _is_cell_removal(alteration)
    ]
    replace_alterations = [
        alteration
        for alteration in options.alterations
        if _is_cell_replacement(alteration)
    ]

    # first: remove cells required to be dropped.
    if remove_alterations:
        nb["cells"] = [cell for cell in nb["cells"] if not _should_remove_cell(cell)]

    # trainer-specific removal: remove non-matching trainer cells
    if trainingType:
        nb["cells"] = [
            cell
            for cell in nb["cells"]
            if not _should_remove_trainer_cell(cell, trainingType)
        ]

    if JumpStartModelNotebookGlobalActionType.dropAllMarkdown in options.globalActions:
        nb["cells"] = [cell for cell in nb["cells"] if cell["cell_type"] != "markdown"]

    # second: perform alteration, ie remove or replace whole code cell.
    if replace_alterations:
        new_cells = []
        for cell in nb["cells"]:
            # Determine if this cell is a code cell, or a markdown cell targeted by specific header alterations
            should_process_cell_for_alteration = cell["cell_type"] == "code" or (
                cell["cell_type"] == "markdown"
                and any(
                    alt.value in cell.get("metadata", {}).get(JUMPSTART_ALTERATIONS, [])
                    for alt in [
                        JumpStartModelNotebookAlterationType.novaTrainingJobNotebookHeaderMarkdown,
                        JumpStartModelNotebookAlterationType.novaHyperpodNotebookHeaderMarkdown,
                        JumpStartModelNotebookAlterationType.openSourceTrainingJobNotebookHeaderMarkdown,
                        JumpStartModelNotebookAlterationType.openSourceHyperpodNotebookHeaderMarkdown,
                    ]
                )
            )

            if should_process_cell_for_alteration:
                # Pass ALL relevant parameters from update_notebook to _get_substitute_cell.
                # _get_substitute_cell will then use the one matching the cell's alteration metadata.
                substituted_cell = _get_substitute_cell(
                    model_id=modelId,
                    current_cell=cell,
                    model_name=modelName,
                    cluster_id=clusterId,
                    hub_name=hubName,
                    connection_id=connectionId,
                    domain=domain,
                    training_type=trainingType,
                    nova_model_name=novaModelName,
                    recipe_path=recipePath,
                    git_clone_url=gitCloneUrl,
                    is_prime=isPrime,
                )
                new_cells.append(substituted_cell)
            else:
                new_cells.append(cell)  # Keep cell as is if no alteration applies
        nb["cells"] = new_cells

    #  third: perform the substitutions, ie find/replace inside a code cells.
    if options.substitutions:
        for substitution in options.substitutions:
            for cell in nb["cells"]:
                if cell["cell_type"] == "code":
                    for i, line in enumerate(cell["source"]):
                        if substitution.find.value in line:
                            line = _replace_line_with_none(
                                line, substitution.find.value, substitution.replace
                            )
                            cell["source"][i] = line
                            if substitution.onlyOnce:
                                completedSubstitutions.add(substitution.find)
                                break
                if substitution.find in completedSubstitutions:
                    break

    # fourth: perform metadata updates (note: this can only replace keys at the top-level)
    for metadata_update in options.metadataUpdates:
        nb["metadata"][metadata_update.key] = metadata_update.value

    # fifth: clean notebook by clearing any output
    for cell in nb["cells"]:
        cell["outputs"] = []

    return json.dumps(nb)


class Notebook(ABC):
    @abstractmethod
    def transform(self, notebook: str, *args, **kwargs) -> str:
        """
        Transform the notebook.
        Args:
            notebook (str): The notebook to transform.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.
        Returns:
            str: The transformed notebook.
        """
        pass


class InferNotebook(Notebook):
    def transform(
        self,
        notebook: str,
        endpoint_name: str,
        inference_component_name: Optional[str] = None,
        set_default_kernel: Optional[bool] = False,
    ) -> str:
        substitutions = self._prepare_substitutions(
            notebook, endpoint_name, inference_component_name
        )
        metadata_updates = self._prepare_metadata_updates(set_default_kernel)

        options = UpdateHubNotebookUpdateOptions(
            substitutions=substitutions,
            alterations=[],
            globalActions=[],
            metadataUpdates=metadata_updates,
        )

        return update_notebook(notebook, None, options)

    def _prepare_substitutions(
        self, notebook: str, endpoint_name: str, inference_component_name: Optional[str]
    ) -> List[JumpStartModelNotebookSubstitution]:
        substitutions = [
            self._create_substitution(
                JumpStartModelNotebookSubstitutionTarget.endpointName, endpoint_name
            )
        ]
        if self._has_placeholder(
            notebook, JumpStartModelNotebookSubstitutionTarget.inferenceComponent
        ):
            substitutions.append(
                self._create_substitution(
                    JumpStartModelNotebookSubstitutionTarget.inferenceComponent,
                    inference_component_name,
                )
            )
        elif inference_component_name:
            substitutions.extend(
                self._handle_inference_component_substitutions(
                    notebook, inference_component_name
                )
            )
        return substitutions

    def _prepare_metadata_updates(
        self, set_default_kernel: Optional[bool]
    ) -> List[JumpStartModelNotebookMetadataUpdateType]:
        return (
            [
                JumpStartModelNotebookMetadataUpdateType(
                    key="kernelspec",
                    value=DEFAULT_PYTHON3_KERNEL_SPEC,
                )
            ]
            if set_default_kernel
            else []
        )

    def _has_placeholder(
        self, notebook: str, target: JumpStartModelNotebookSubstitutionTarget
    ) -> bool:
        """Check if the notebook contains the given placeholder."""
        return target.value in notebook

    def _create_substitution(
        self,
        target: JumpStartModelNotebookSubstitutionTarget,
        replacement: str,
        onlyOnce: bool = True,
    ) -> JumpStartModelNotebookSubstitution:
        """Create a substitution object for the given target and replacement."""
        return JumpStartModelNotebookSubstitution(target, replacement, onlyOnce)

    def _handle_inference_component_substitutions(
        self, notebook: str, component_name: str
    ) -> List[JumpStartModelNotebookSubstitution]:
        """Create substitutions for inference component based on the notebook's content."""
        substitutions = []
        for target in [
            JumpStartModelNotebookSubstitutionTarget.inferenceComponentBoto3,
            JumpStartModelNotebookSubstitutionTarget.inferenceComponentSdk,
        ]:
            if self._has_placeholder(notebook, target):
                if (
                    target
                    == JumpStartModelNotebookSubstitutionTarget.inferenceComponentSdk
                ):
                    replacement = f"(endpoint_name=endpoint_name, inference_component_name='{component_name}')"
                else:
                    replacement = (
                        f"{target.value}, InferenceComponentName='{component_name}'"
                    )
                substitutions.append(self._create_substitution(target, replacement))
        return substitutions


class ModelSdkNotebook(Notebook):
    def transform(
        self, notebook: str, modelId: str, hubName: Optional[str] = None
    ) -> str:
        alterations = [
            JumpStartModelNotebookAlterationType.dropModelSelection,
            JumpStartModelNotebookAlterationType.modelIdOnly,
            JumpStartModelNotebookAlterationType.modelIdVersion,
            JumpStartModelNotebookAlterationType.modelInitHubName,
            JumpStartModelNotebookAlterationType.estimatorInitHubName,
        ]
        options = UpdateHubNotebookUpdateOptions([], alterations, [])
        notebook = update_notebook(notebook, modelId, options, hubName=hubName)
        return notebook


class HyperpodNotebook(Notebook):
    def transform(
        self,
        notebook: str,
        clusterId: str,
        connectionId: str = None,
        domain: str = None,
    ) -> str:
        alterations = [
            JumpStartModelNotebookAlterationType.clusterName,
            JumpStartModelNotebookAlterationType.clusterId,
            JumpStartModelNotebookAlterationType.hyperPodStudio,
            JumpStartModelNotebookAlterationType.hyperPodUnifiedStudio,
        ]
        options = UpdateHubNotebookUpdateOptions([], alterations, [])
        notebook = update_notebook(
            notebook,
            None,
            options,
            clusterId=clusterId,
            connectionId=connectionId,
            domain=domain,
        )
        return notebook


class NovaNotebook(Notebook):
    def transform(
        self,
        notebook: str,
        recipePath: str,
        clusterId: str = None,
        connectionId: str = None,
        domain: str = None,
    ) -> str:

        if not notebook or not recipePath:
            raise ValueError(
                "Required parameters (notebook, recipePath) cannot be None or empty"
            )
        alterations = [
            JumpStartModelNotebookAlterationType.clusterName,
            JumpStartModelNotebookAlterationType.clusterId,
            JumpStartModelNotebookAlterationType.hyperPodStudio,
            JumpStartModelNotebookAlterationType.hyperPodUnifiedStudio,
            JumpStartModelNotebookAlterationType.getRecipePath,
            JumpStartModelNotebookAlterationType.getExtractedRecipePath,
            JumpStartModelNotebookAlterationType.novaTrainingJobNotebookHeaderMarkdown,
            JumpStartModelNotebookAlterationType.novaHyperpodNotebookHeaderMarkdown,
            JumpStartModelNotebookAlterationType.cloneRepository,
        ]
        region = get_region_name()
        git_command = ""

        normalized_path = recipePath.replace(os.sep, "/")
        match = re.search(r"/recipes/([^/]+)/([^/]+)/([^/]+)$", normalized_path)

        if match:
            # Extract trainingType and novaModelName from recipePath
            trainingType = match.group(1)
            novaModelName = match.group(2)
        else:
            error_msg = f"Error: Could not extract trainingType or novaModelName from recipePath: {recipePath}. Unexpected format."
            logging.error(error_msg)
            raise ValueError(error_msg)

        is_prime = check_prime_status(
            model_id=novaModelName,
            region=region,
            domain=domain,
            connection_id=connectionId,
        )

        if is_prime:
            alterations.append(
                JumpStartModelNotebookAlterationType.fetchCodeCommitCredentials,
            )
            git_command = CODE_COMMIT_CLONE_TEMPLATE
        else:
            git_command = PUBLIC_REPO_CLONE_TEMPLATE

        options = UpdateHubNotebookUpdateOptions([], alterations, [])
        if clusterId:
            notebook = update_notebook(
                notebook,
                None,
                options,
                clusterId=clusterId,
                connectionId=connectionId,
                domain=domain,
                trainingType=trainingType,
                novaModelName=novaModelName,
                recipePath=recipePath,
                gitCloneUrl=git_command,
                isPrime=is_prime,
            )
            return notebook
        else:
            notebook = update_notebook(
                notebook,
                None,
                options,
                trainingType=trainingType,
                novaModelName=novaModelName,
                recipePath=recipePath,
                gitCloneUrl=git_command,
                isPrime=is_prime,
            )
            return notebook


class OpenSourceNotebook(Notebook):
    def transform(
        self,
        notebook: str,
        # HyperPod parameters
        clusterId: str = None,
        connectionId: str = None,
        domain: str = None,
        recipePath: str = None,
        # Serverless SMTJ parameters
        baseModelName: str = None,
        customizationTechnique: str = None,
        modelPackageGroupName: str = None,
        dataSetName: str = None,
        dataSetVersion: str = None,
    ) -> str:

        if not notebook:
            raise ValueError("notebook parameter cannot be None or empty")

        # Validate parameter mutual exclusivity
        if clusterId and any(
            [
                baseModelName,
                customizationTechnique,
                modelPackageGroupName,
                dataSetName,
                dataSetVersion,
            ]
        ):
            raise ValueError(
                "Cannot provide both HyperPod parameters (clusterId) and Serverless SMTJ parameters. "
                "Please provide only one set of parameters."
            )

        # HyperPod mode
        if clusterId:
            if not recipePath:
                raise ValueError("recipePath is required for HyperPod mode")
            return self._transform_hyperpod(
                notebook, clusterId, connectionId, domain, recipePath
            )

        # Serverless SMTJ mode
        else:
            return self._transform_serverless_smtj(
                notebook,
                baseModelName,
                customizationTechnique,
                modelPackageGroupName,
                dataSetName,
                dataSetVersion,
            )

    def _transform_hyperpod(
        self,
        notebook: str,
        clusterId: str,
        connectionId: str,
        domain: str,
        recipePath: str,
    ) -> str:
        """Transform notebook for HyperPod execution"""
        # Extract trainingType and modelName from recipePath
        normalized_path = recipePath.replace(os.sep, "/")
        match = re.search(r"/recipes/([^/]+)/([^/]+)/([^/]+)$", normalized_path)
        if not match:
            raise ValueError(
                f"Could not extract trainingType or modelName from recipePath: {recipePath}"
            )

        trainingType = match.group(1)
        modelName = match.group(2)

        # HyperPod alterations
        alterations = [
            JumpStartModelNotebookAlterationType.clusterName,
            JumpStartModelNotebookAlterationType.clusterId,
            JumpStartModelNotebookAlterationType.hyperPodStudio,
            JumpStartModelNotebookAlterationType.hyperPodUnifiedStudio,
            JumpStartModelNotebookAlterationType.getRecipePath,
            JumpStartModelNotebookAlterationType.getExtractedRecipePath,
            JumpStartModelNotebookAlterationType.openSourceHyperpodNotebookHeaderMarkdown,
            JumpStartModelNotebookAlterationType.cloneRepository,
        ]

        # HyperPod launcher path substitution
        path_components = recipePath.split("/")
        if len(path_components) < 2:
            raise ValueError(
                f"Invalid recipePath format '{recipePath}'. Path must end with 'model_name/recipe_file.yaml'"
            )
        script_directory = path_components[-2]
        recipe_base_name = path_components[-1].rsplit(".", 1)[0]
        launcher_script_name = f"run_{recipe_base_name}.sh"
        hyperpod_launcher_path_value = f"{script_directory}/{launcher_script_name}"

        substitutions = [
            JumpStartModelNotebookSubstitution(
                JumpStartModelNotebookSubstitutionTarget.hpLauncherPath,
                f'hyperpod_launcher_path = "{hyperpod_launcher_path_value}"',
                True,
            )
        ]

        options = UpdateHubNotebookUpdateOptions(substitutions, alterations, [])
        return update_notebook(
            notebook,
            None,
            options,
            clusterId=clusterId,
            connectionId=connectionId,
            domain=domain,
            trainingType=trainingType,
            modelName=modelName,
            recipePath=recipePath,
        )

    def _transform_serverless_smtj(
        self,
        notebook: str,
        baseModelName: str,
        customizationTechnique: str,
        modelPackageGroupName: str,
        dataSetName: str,
        dataSetVersion: str,
    ) -> str:
        """Transform notebook for Serverless SageMaker Training Job"""
        # Serverless alterations
        alterations = [
            JumpStartModelNotebookAlterationType.openSourceTrainingJobNotebookHeaderMarkdown,
        ]

        # Only add trainer selection if we have a customization technique
        if customizationTechnique:
            alterations.append(JumpStartModelNotebookAlterationType.trainerSelection)

        # Serverless substitutions - only add if parameter is provided
        substitutions = []

        # Base model name substitution
        if baseModelName:
            substitutions.append(
                JumpStartModelNotebookSubstitution(
                    JumpStartModelNotebookSubstitutionTarget.baseModelName,
                    f'BASE_MODEL = "{baseModelName}"',
                    True,
                )
            )

        # Customization technique substitution
        if customizationTechnique:
            substitutions.append(
                JumpStartModelNotebookSubstitution(
                    JumpStartModelNotebookSubstitutionTarget.customizationTechnique,
                    f'CUSTOMIZATION_TECHNIQUE = "{customizationTechnique}"',
                    True,
                )
            )

        # Model package group name substitution
        if modelPackageGroupName:
            substitutions.append(
                JumpStartModelNotebookSubstitution(
                    JumpStartModelNotebookSubstitutionTarget.modelPackageGroupName,
                    f'MODEL_PACKAGE_GROUP_NAME = "{modelPackageGroupName}"',
                    True,
                )
            )

        # Dataset ARN substitution - only if both dataSetName and dataSetVersion are provided
        if dataSetName and dataSetVersion:
            dataset_arn = f"arn:aws:sagemaker:{get_region_name()}:{get_aws_account_id()}:hub-content/AIRegistry/DataSet/{dataSetName}/{dataSetVersion}"
            substitutions.append(
                JumpStartModelNotebookSubstitution(
                    JumpStartModelNotebookSubstitutionTarget.dataSetArn,
                    f'TRAINING_DATASET = "{dataset_arn}"',
                    True,
                )
            )

        options = UpdateHubNotebookUpdateOptions(substitutions, alterations, [])
        return update_notebook(
            notebook,
            None,
            options,
            trainingType=customizationTechnique,
            modelName=baseModelName,
        )
