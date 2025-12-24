# sagemaker_jupyterlab_extension_common

This package includes the common extensions built by SageMaker team that includes tools and utilities that can be shared by different extensions built by SageMaker. 

## Requirements
* JupyterLab >= 4
* aiobotocore
* aws_embedded_metrics

## Installing the extension
To install the extension within local Jupyter environment, a Docker image/container or in SageMaker Studio, run:
```
pip install sagemaker_jupyterlab_extension_common-<version>-py3-none-any.whl`
```

## Uninstalling the extension
To uninstall this extension, run:
```
pip uninstall sagemaker_jupyterlab_extension_common`
```

### Troubleshooting
If you are seeing the frontend extension, but it is not working, check that the server extension is enabled:

```
jupyter serverextension list
```

If the server extension is installed and enabled, but you are not seeing the frontend extension, check the frontend extension is installed:
```
jupyter labextension list
```

If the frontend extension is installed and enabled, open Browser console and see if there are any JavaScript error that is related to the extension in Browser console.

## See DEVELOPING.md for more instructions on dev setup and contributing guidelines


### Deployment

- Publishing to Conda happens through the Conda Forge feedstock repository. Once new version has been deployed to Pypi, create a new Github issue similar to this one https://github.com/conda-forge/sagemaker-jupyterlab-extension-common-feedstock/issues/30 and it will trigger new Conda Forge version release as a Pull Request.


### Links

- Pypi -> https://pypi.org/project/sagemaker-jupyterlab-extension-common
- Conda Forge -> https://anaconda.org/conda-forge/sagemaker-jupyterlab-extension-common
