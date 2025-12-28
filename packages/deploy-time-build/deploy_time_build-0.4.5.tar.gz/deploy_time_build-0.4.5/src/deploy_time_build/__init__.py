r'''
# Deploy-time Build

AWS CDK L3 construct that allows you to run a build job for specific purposes. Currently this library supports the following use cases:

* Build web frontend static files
* Build a container image
* Build Seekable OCI (SOCI) indices for container images

[![View on Construct Hub](https://constructs.dev/badge?package=deploy-time-build)](https://constructs.dev/packages/deploy-time-build)

## Usage

Install from npm:

```sh
npm i deploy-time-build
```

This library defines several L3 constructs for specific use cases. Here is the usage for each case.

### Build Node.js apps

You can build a Node.js app such as a React frontend app on deploy time by the `NodejsBuild` construct.

![architecture](./imgs/architecture.png)

The following code is an example to use the construct:

```python
import { NodejsBuild } from 'deploy-time-build';

declare const api: apigateway.RestApi;
declare const destinationBucket: s3.IBucket;
declare const distribution: cloudfront.IDistribution;
new NodejsBuild(this, 'ExampleBuild', {
    assets: [
        {
            path: 'example-app',
            exclude: ['dist', 'node_modules'],
        },
    ],
    destinationBucket,
    distribution,
    outputSourceDirectory: 'dist',
    buildCommands: ['npm ci', 'npm run build'],
    buildEnvironment: {
        VITE_API_ENDPOINT: api.url,
    },
});
```

Note that it is possible to pass environment variable `VITE_API_ENDPOINT: api.url` to the construct, which is resolved on deploy time, and injected to the build environment (a vite process in this case.)
The resulting build artifacts will be deployed to `destinationBucket` from CodeBuild.

You can specify multiple input assets by `assets` property. These assets are extracted to respective sub directories. For example, assume you specified assets like the following:

```python
assets: [
    {
        // directory containing source code and package.json
        path: 'example-app',
        exclude: ['dist', 'node_modules'],
        commands: ['npm install'],
    },
    {
        // directory that is also required for the build
        path: 'module1',
    },
],
```

Then, the extracted directories will be located as the following:

```sh
.                         # a temporary directory (automatically created)
├── example-app           # extracted example-app assets
│   ├── src/              # dist or node_modules directories are excluded even if they exist locally.
│   ├── package.json      # npm install will be executed since its specified in `commands` property.
│   └── package-lock.json
└── module1               # extracted module1 assets
```

You can also override the path where assets are extracted by `extractPath` property for each asset.

With `outputEnvFile` property enabled, a `.env` file is automatically generated and uploaded to your S3 bucket. This file can be used running you frontend project locally. You can download the file to your local machine by running the command added in the stack output.

Please also check [the example directory](./example/) for a complete example.

#### Allowing access from the build environment to other AWS resources

Since `NodejsBuild` construct implements [`iam.IGrantable`](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_iam.IGrantable.html) interface, you can use `grant*` method of other constructs to allow access from the build environment.

```python
declare const someBucket: s3.IBucket;
declare const build: NodejsBuild;
someBucket.grantReadWrite(build);
```

You can also use [`iam.Grant`](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_iam.Grant.html) class to allow any actions and resources.

```python
declare const build: NodejsBuild;
iam.Grant.addToPrincipal({ grantee: build, actions: ['s3:ListBucket'], resources:['*'] })
```

#### Motivation - why do we need the `NodejsBuild` construct?

I talked about why this construct can be useful in some situations at CDK Day 2023. See the recording or slides below:

[Recording](https://www.youtube.com/live/b-nSH18gFQk?si=ogEZ2x1NixOj6J6j&t=373) | [Slides](https://speakerdeck.com/tmokmss/deploy-web-frontend-apps-with-aws-cdk)

#### Considerations

Since this construct builds your frontend apps every time you deploy the stack and there is any change in input assets (and currently there's even no build cache in the Lambda function!), the time a deployment takes tends to be longer (e.g. a few minutes even for the simple app in `example` directory.) This might results in worse developer experience if you want to deploy changes frequently (imagine `cdk watch` deployment always re-build your frontend app).

To mitigate this issue, you can separate the stack for frontend construct from other stacks especially for a dev environment. Another solution would be to set a fixed string as an asset hash, and avoid builds on every deployment.

```python
      assets: [
        {
          path: '../frontend',
          exclude: ['node_modules', 'dist'],
          commands: ['npm ci'],
          // Set a fixed string as a asset hash to prevent deploying changes.
          // This can be useful for an environment you use to develop locally.
          assetHash: 'frontend_asset',
        },
      ],
```

### Build a container image

You can build a container image at deploy time by the following code:

```python
import { ContainerImageBuild } from 'deploy-time-build';

const image = new ContainerImageBuild(this, 'Build', {
    directory: 'example-image',
    buildArgs: { DUMMY_FILE_SIZE_MB: '15' },
    tag: 'my-image-tag',
});
new DockerImageFunction(this, 'Function', {
    code: image.toLambdaDockerImageCode(),
});
const armImage = new ContainerImageBuild(this, 'BuildArm', {
    directory: 'example-image',
    platform: Platform.LINUX_ARM64,
    repository: image.repository,
    zstdCompression: true,
});
new FargateTaskDefinition(this, 'TaskDefinition', {
    runtimePlatform: { cpuArchitecture: CpuArchitecture.ARM64 }
}).addContainer('main', {
    image: armImage.toEcsDockerImageCode(),
});
```

The third argument (props) are a superset of DockerImageAsset's properties. You can set a few additional properties such as `tag`, `repository`, and `zstdCompression`.

### Build SOCI index for a container image

[Seekable OCI (SOCI)](https://aws.amazon.com/about-aws/whats-new/2022/09/introducing-seekable-oci-lazy-loading-container-images/) is a way to help start tasks faster for Amazon ECS tasks on Fargate 1.4.0. You can build and push a SOCI index using the `SociIndexV2Build` construct.

![soci-architecture](imgs/soci-architecture.png)

The following code is an example to use the construct:

```python
import { SociIndexV2Build } from 'deploy-time-build';

const asset = new DockerImageAsset(this, 'Image', { directory: 'example-image' });
const sociIndex = new SociIndexV2Build(this, 'SociV2Index', {
  repository: asset.repository,
  inputImageTag: asset.assetHash,
  outputImageTag: `${asset.assetHash}-soci`,
});

// Use with ECS Fargate
const taskDefinition = new FargateTaskDefinition(this, 'TaskDefinition');
taskDefinition.addContainer('main', {
  image: sociIndex.toEcsDockerImageCode(),
});

// Or create from DockerImageAsset using utility method
const sociIndexFromAsset = SociIndexV2Build.fromDockerImageAsset(this, 'SociV2Index2', asset);
```

The `SociIndexV2Build` construct:

* Takes an input container image and builds a SOCI v2 index for it
* Outputs a new image tag with the embedded SOCI index
* Provides `toEcsDockerImageCode()` method to easily use with ECS tasks
* Uses the same ECR repository for input and output images

We currently use [`soci-wrapper`](https://github.com/tmokmss/soci-wrapper) to build and push SOCI indices.

> [!WARNING]
> The previous `SocideIndexBuild` construct is now deprecated. Customers new to SOCI on AWS Fargate can only use SOCI index manifest v2. See [this article](https://aws.amazon.com/blogs/containers/improving-amazon-ecs-deployment-consistency-with-soci-index-manifest-v2/) for more details.

#### Motivation - why do we need the `SociIndexBuild` construct?

Currently there are several other ways to build a SOCI index; 1. use `soci-snapshotter` CLI, or 2. use [cfn-ecr-aws-soci-index-builder](https://github.com/aws-ia/cfn-ecr-aws-soci-index-builder) solution, none of which can be directly used from AWS CDK. If you are familiar with CDK, you should often deploy container images as CDK assets, which is an ideal way to integrate with other L2 constructs such as ECS. To make the developer experience for SOCI as close as the ordinary container images, the `SociIndexBuild` allows you to deploying a SOCI index directly from CDK, without any dependencies outside of CDK context.

## Development

Commands for maintainers:

```sh
# run test locally
npx tsc -p tsconfig.dev.json
npx integ-runner
npx integ-runner --update-on-failed
```
'''
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

import abc
import builtins
import datetime
import enum
import typing

import jsii
import publication
import typing_extensions

import typeguard
from importlib.metadata import version as _metadata_package_version
TYPEGUARD_MAJOR_VERSION = int(_metadata_package_version('typeguard').split('.')[0])

def check_type(argname: str, value: object, expected_type: typing.Any) -> typing.Any:
    if TYPEGUARD_MAJOR_VERSION <= 2:
        return typeguard.check_type(argname=argname, value=value, expected_type=expected_type) # type:ignore
    else:
        if isinstance(value, jsii._reference_map.InterfaceDynamicProxy): # pyright: ignore [reportAttributeAccessIssue]
           pass
        else:
            if TYPEGUARD_MAJOR_VERSION == 3:
                typeguard.config.collection_check_strategy = typeguard.CollectionCheckStrategy.ALL_ITEMS # type:ignore
                typeguard.check_type(value=value, expected_type=expected_type) # type:ignore
            else:
                typeguard.check_type(value=value, expected_type=expected_type, collection_check_strategy=typeguard.CollectionCheckStrategy.ALL_ITEMS) # type:ignore

from ._jsii import *

import aws_cdk as _aws_cdk_ceddda9d
import aws_cdk.aws_cloudfront as _aws_cdk_aws_cloudfront_ceddda9d
import aws_cdk.aws_ec2 as _aws_cdk_aws_ec2_ceddda9d
import aws_cdk.aws_ecr as _aws_cdk_aws_ecr_ceddda9d
import aws_cdk.aws_ecr_assets as _aws_cdk_aws_ecr_assets_ceddda9d
import aws_cdk.aws_ecs as _aws_cdk_aws_ecs_ceddda9d
import aws_cdk.aws_iam as _aws_cdk_aws_iam_ceddda9d
import aws_cdk.aws_kms as _aws_cdk_aws_kms_ceddda9d
import aws_cdk.aws_lambda as _aws_cdk_aws_lambda_ceddda9d
import aws_cdk.aws_s3 as _aws_cdk_aws_s3_ceddda9d
import aws_cdk.aws_s3_assets as _aws_cdk_aws_s3_assets_ceddda9d
import constructs as _constructs_77d1e7e8


@jsii.data_type(
    jsii_type="deploy-time-build.AssetConfig",
    jsii_struct_bases=[_aws_cdk_aws_s3_assets_ceddda9d.AssetProps],
    name_mapping={
        "asset_hash": "assetHash",
        "asset_hash_type": "assetHashType",
        "bundling": "bundling",
        "exclude": "exclude",
        "follow_symlinks": "followSymlinks",
        "ignore_mode": "ignoreMode",
        "deploy_time": "deployTime",
        "display_name": "displayName",
        "readers": "readers",
        "source_kms_key": "sourceKMSKey",
        "path": "path",
        "commands": "commands",
        "extract_path": "extractPath",
    },
)
class AssetConfig(_aws_cdk_aws_s3_assets_ceddda9d.AssetProps):
    def __init__(
        self,
        *,
        asset_hash: typing.Optional[builtins.str] = None,
        asset_hash_type: typing.Optional[_aws_cdk_ceddda9d.AssetHashType] = None,
        bundling: typing.Optional[typing.Union[_aws_cdk_ceddda9d.BundlingOptions, typing.Dict[builtins.str, typing.Any]]] = None,
        exclude: typing.Optional[typing.Sequence[builtins.str]] = None,
        follow_symlinks: typing.Optional[_aws_cdk_ceddda9d.SymlinkFollowMode] = None,
        ignore_mode: typing.Optional[_aws_cdk_ceddda9d.IgnoreMode] = None,
        deploy_time: typing.Optional[builtins.bool] = None,
        display_name: typing.Optional[builtins.str] = None,
        readers: typing.Optional[typing.Sequence[_aws_cdk_aws_iam_ceddda9d.IGrantable]] = None,
        source_kms_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey] = None,
        path: builtins.str,
        commands: typing.Optional[typing.Sequence[builtins.str]] = None,
        extract_path: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param asset_hash: Specify a custom hash for this asset. If ``assetHashType`` is set it must be set to ``AssetHashType.CUSTOM``. For consistency, this custom hash will be SHA256 hashed and encoded as hex. The resulting hash will be the asset hash. NOTE: the hash is used in order to identify a specific revision of the asset, and used for optimizing and caching deployment activities related to this asset such as packaging, uploading to Amazon S3, etc. If you chose to customize the hash, you will need to make sure it is updated every time the asset changes, or otherwise it is possible that some deployments will not be invalidated. Default: - based on ``assetHashType``
        :param asset_hash_type: Specifies the type of hash to calculate for this asset. If ``assetHash`` is configured, this option must be ``undefined`` or ``AssetHashType.CUSTOM``. Default: - the default is ``AssetHashType.SOURCE``, but if ``assetHash`` is explicitly specified this value defaults to ``AssetHashType.CUSTOM``.
        :param bundling: Bundle the asset by executing a command in a Docker container or a custom bundling provider. The asset path will be mounted at ``/asset-input``. The Docker container is responsible for putting content at ``/asset-output``. The content at ``/asset-output`` will be zipped and used as the final asset. Default: - uploaded as-is to S3 if the asset is a regular file or a .zip file, archived into a .zip file and uploaded to S3 otherwise
        :param exclude: File paths matching the patterns will be excluded. See ``ignoreMode`` to set the matching behavior. Has no effect on Assets bundled using the ``bundling`` property. Default: - nothing is excluded
        :param follow_symlinks: A strategy for how to handle symlinks. Default: SymlinkFollowMode.NEVER
        :param ignore_mode: The ignore behavior to use for ``exclude`` patterns. Default: IgnoreMode.GLOB
        :param deploy_time: Whether or not the asset needs to exist beyond deployment time; i.e. are copied over to a different location and not needed afterwards. Setting this property to true has an impact on the lifecycle of the asset, because we will assume that it is safe to delete after the CloudFormation deployment succeeds. For example, Lambda Function assets are copied over to Lambda during deployment. Therefore, it is not necessary to store the asset in S3, so we consider those deployTime assets. Default: false
        :param display_name: A display name for this asset. If supplied, the display name will be used in locations where the asset identifier is printed, like in the CLI progress information. If the same asset is added multiple times, the display name of the first occurrence is used. The default is the construct path of the Asset construct, with respect to the enclosing stack. If the asset is produced by a construct helper function (such as ``lambda.Code.fromAsset()``), this will look like ``MyFunction/Code``. We use the stack-relative construct path so that in the common case where you have multiple stacks with the same asset, we won't show something like ``/MyBetaStack/MyFunction/Code`` when you are actually deploying to production. Default: - Stack-relative construct path
        :param readers: A list of principals that should be able to read this asset from S3. You can use ``asset.grantRead(principal)`` to grant read permissions later. Default: - No principals that can read file asset.
        :param source_kms_key: The ARN of the KMS key used to encrypt the handler code. Default: - the default server-side encryption with Amazon S3 managed keys(SSE-S3) key will be used.
        :param path: The disk location of the asset. The path should refer to one of the following: - A regular file or a .zip file, in which case the file will be uploaded as-is to S3. - A directory, in which case it will be archived into a .zip file and uploaded to S3.
        :param commands: Shell commands executed right after the asset zip is extracted to the build environment. Default: No command is executed.
        :param extract_path: Relative path from a build directory to the directory where the asset is extracted. Default: basename of the asset path.
        '''
        if isinstance(bundling, dict):
            bundling = _aws_cdk_ceddda9d.BundlingOptions(**bundling)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b8e57ab5756054ba32d3c99212a85d1a9c6d99aadd68fa6b763c12872e443675)
            check_type(argname="argument asset_hash", value=asset_hash, expected_type=type_hints["asset_hash"])
            check_type(argname="argument asset_hash_type", value=asset_hash_type, expected_type=type_hints["asset_hash_type"])
            check_type(argname="argument bundling", value=bundling, expected_type=type_hints["bundling"])
            check_type(argname="argument exclude", value=exclude, expected_type=type_hints["exclude"])
            check_type(argname="argument follow_symlinks", value=follow_symlinks, expected_type=type_hints["follow_symlinks"])
            check_type(argname="argument ignore_mode", value=ignore_mode, expected_type=type_hints["ignore_mode"])
            check_type(argname="argument deploy_time", value=deploy_time, expected_type=type_hints["deploy_time"])
            check_type(argname="argument display_name", value=display_name, expected_type=type_hints["display_name"])
            check_type(argname="argument readers", value=readers, expected_type=type_hints["readers"])
            check_type(argname="argument source_kms_key", value=source_kms_key, expected_type=type_hints["source_kms_key"])
            check_type(argname="argument path", value=path, expected_type=type_hints["path"])
            check_type(argname="argument commands", value=commands, expected_type=type_hints["commands"])
            check_type(argname="argument extract_path", value=extract_path, expected_type=type_hints["extract_path"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "path": path,
        }
        if asset_hash is not None:
            self._values["asset_hash"] = asset_hash
        if asset_hash_type is not None:
            self._values["asset_hash_type"] = asset_hash_type
        if bundling is not None:
            self._values["bundling"] = bundling
        if exclude is not None:
            self._values["exclude"] = exclude
        if follow_symlinks is not None:
            self._values["follow_symlinks"] = follow_symlinks
        if ignore_mode is not None:
            self._values["ignore_mode"] = ignore_mode
        if deploy_time is not None:
            self._values["deploy_time"] = deploy_time
        if display_name is not None:
            self._values["display_name"] = display_name
        if readers is not None:
            self._values["readers"] = readers
        if source_kms_key is not None:
            self._values["source_kms_key"] = source_kms_key
        if commands is not None:
            self._values["commands"] = commands
        if extract_path is not None:
            self._values["extract_path"] = extract_path

    @builtins.property
    def asset_hash(self) -> typing.Optional[builtins.str]:
        '''Specify a custom hash for this asset.

        If ``assetHashType`` is set it must
        be set to ``AssetHashType.CUSTOM``. For consistency, this custom hash will
        be SHA256 hashed and encoded as hex. The resulting hash will be the asset
        hash.

        NOTE: the hash is used in order to identify a specific revision of the asset, and
        used for optimizing and caching deployment activities related to this asset such as
        packaging, uploading to Amazon S3, etc. If you chose to customize the hash, you will
        need to make sure it is updated every time the asset changes, or otherwise it is
        possible that some deployments will not be invalidated.

        :default: - based on ``assetHashType``
        '''
        result = self._values.get("asset_hash")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def asset_hash_type(self) -> typing.Optional[_aws_cdk_ceddda9d.AssetHashType]:
        '''Specifies the type of hash to calculate for this asset.

        If ``assetHash`` is configured, this option must be ``undefined`` or
        ``AssetHashType.CUSTOM``.

        :default:

        - the default is ``AssetHashType.SOURCE``, but if ``assetHash`` is
        explicitly specified this value defaults to ``AssetHashType.CUSTOM``.
        '''
        result = self._values.get("asset_hash_type")
        return typing.cast(typing.Optional[_aws_cdk_ceddda9d.AssetHashType], result)

    @builtins.property
    def bundling(self) -> typing.Optional[_aws_cdk_ceddda9d.BundlingOptions]:
        '''Bundle the asset by executing a command in a Docker container or a custom bundling provider.

        The asset path will be mounted at ``/asset-input``. The Docker
        container is responsible for putting content at ``/asset-output``.
        The content at ``/asset-output`` will be zipped and used as the
        final asset.

        :default:

        - uploaded as-is to S3 if the asset is a regular file or a .zip file,
        archived into a .zip file and uploaded to S3 otherwise
        '''
        result = self._values.get("bundling")
        return typing.cast(typing.Optional[_aws_cdk_ceddda9d.BundlingOptions], result)

    @builtins.property
    def exclude(self) -> typing.Optional[typing.List[builtins.str]]:
        '''File paths matching the patterns will be excluded.

        See ``ignoreMode`` to set the matching behavior.
        Has no effect on Assets bundled using the ``bundling`` property.

        :default: - nothing is excluded
        '''
        result = self._values.get("exclude")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def follow_symlinks(self) -> typing.Optional[_aws_cdk_ceddda9d.SymlinkFollowMode]:
        '''A strategy for how to handle symlinks.

        :default: SymlinkFollowMode.NEVER
        '''
        result = self._values.get("follow_symlinks")
        return typing.cast(typing.Optional[_aws_cdk_ceddda9d.SymlinkFollowMode], result)

    @builtins.property
    def ignore_mode(self) -> typing.Optional[_aws_cdk_ceddda9d.IgnoreMode]:
        '''The ignore behavior to use for ``exclude`` patterns.

        :default: IgnoreMode.GLOB
        '''
        result = self._values.get("ignore_mode")
        return typing.cast(typing.Optional[_aws_cdk_ceddda9d.IgnoreMode], result)

    @builtins.property
    def deploy_time(self) -> typing.Optional[builtins.bool]:
        '''Whether or not the asset needs to exist beyond deployment time;

        i.e.
        are copied over to a different location and not needed afterwards.
        Setting this property to true has an impact on the lifecycle of the asset,
        because we will assume that it is safe to delete after the CloudFormation
        deployment succeeds.

        For example, Lambda Function assets are copied over to Lambda during
        deployment. Therefore, it is not necessary to store the asset in S3, so
        we consider those deployTime assets.

        :default: false
        '''
        result = self._values.get("deploy_time")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def display_name(self) -> typing.Optional[builtins.str]:
        '''A display name for this asset.

        If supplied, the display name will be used in locations where the asset
        identifier is printed, like in the CLI progress information. If the same
        asset is added multiple times, the display name of the first occurrence is
        used.

        The default is the construct path of the Asset construct, with respect to
        the enclosing stack. If the asset is produced by a construct helper
        function (such as ``lambda.Code.fromAsset()``), this will look like
        ``MyFunction/Code``.

        We use the stack-relative construct path so that in the common case where
        you have multiple stacks with the same asset, we won't show something like
        ``/MyBetaStack/MyFunction/Code`` when you are actually deploying to
        production.

        :default: - Stack-relative construct path
        '''
        result = self._values.get("display_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def readers(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_iam_ceddda9d.IGrantable]]:
        '''A list of principals that should be able to read this asset from S3.

        You can use ``asset.grantRead(principal)`` to grant read permissions later.

        :default: - No principals that can read file asset.
        '''
        result = self._values.get("readers")
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_iam_ceddda9d.IGrantable]], result)

    @builtins.property
    def source_kms_key(self) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey]:
        '''The ARN of the KMS key used to encrypt the handler code.

        :default: - the default server-side encryption with Amazon S3 managed keys(SSE-S3) key will be used.
        '''
        result = self._values.get("source_kms_key")
        return typing.cast(typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey], result)

    @builtins.property
    def path(self) -> builtins.str:
        '''The disk location of the asset.

        The path should refer to one of the following:

        - A regular file or a .zip file, in which case the file will be uploaded as-is to S3.
        - A directory, in which case it will be archived into a .zip file and uploaded to S3.
        '''
        result = self._values.get("path")
        assert result is not None, "Required property 'path' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def commands(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Shell commands executed right after the asset zip is extracted to the build environment.

        :default: No command is executed.
        '''
        result = self._values.get("commands")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def extract_path(self) -> typing.Optional[builtins.str]:
        '''Relative path from a build directory to the directory where the asset is extracted.

        :default: basename of the asset path.
        '''
        result = self._values.get("extract_path")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AssetConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.implements(_aws_cdk_aws_iam_ceddda9d.IGrantable)
class ContainerImageBuild(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="deploy-time-build.ContainerImageBuild",
):
    '''Build a container image and push it to an ECR repository on deploy-time.'''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        repository: typing.Optional[_aws_cdk_aws_ecr_ceddda9d.IRepository] = None,
        tag: typing.Optional[builtins.str] = None,
        tag_prefix: typing.Optional[builtins.str] = None,
        vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
        zstd_compression: typing.Optional[builtins.bool] = None,
        directory: builtins.str,
        asset_name: typing.Optional[builtins.str] = None,
        build_args: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        build_secrets: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        build_ssh: typing.Optional[builtins.str] = None,
        cache_disabled: typing.Optional[builtins.bool] = None,
        cache_from: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_ecr_assets_ceddda9d.DockerCacheOption, typing.Dict[builtins.str, typing.Any]]]] = None,
        cache_to: typing.Optional[typing.Union[_aws_cdk_aws_ecr_assets_ceddda9d.DockerCacheOption, typing.Dict[builtins.str, typing.Any]]] = None,
        display_name: typing.Optional[builtins.str] = None,
        file: typing.Optional[builtins.str] = None,
        invalidation: typing.Optional[typing.Union[_aws_cdk_aws_ecr_assets_ceddda9d.DockerImageAssetInvalidationOptions, typing.Dict[builtins.str, typing.Any]]] = None,
        network_mode: typing.Optional[_aws_cdk_aws_ecr_assets_ceddda9d.NetworkMode] = None,
        outputs: typing.Optional[typing.Sequence[builtins.str]] = None,
        platform: typing.Optional[_aws_cdk_aws_ecr_assets_ceddda9d.Platform] = None,
        target: typing.Optional[builtins.str] = None,
        extra_hash: typing.Optional[builtins.str] = None,
        exclude: typing.Optional[typing.Sequence[builtins.str]] = None,
        follow_symlinks: typing.Optional[_aws_cdk_ceddda9d.SymlinkFollowMode] = None,
        ignore_mode: typing.Optional[_aws_cdk_ceddda9d.IgnoreMode] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param repository: The ECR repository to push the image. Default: create a new ECR repository
        :param tag: The tag when to push the image. Default: use assetHash as tag
        :param tag_prefix: Prefix to add to the image tag. Default: no prefix
        :param vpc: The VPC where your build job will be deployed. This VPC must have private subnets with NAT Gateways. Use this property when you want to control the outbound IP addresses that base images are pulled from. Default: No VPC used.
        :param zstd_compression: Use zstd for compressing a container image. Default: false
        :param directory: The directory where the Dockerfile is stored. Any directory inside with a name that matches the CDK output folder (cdk.out by default) will be excluded from the asset
        :param asset_name: Unique identifier of the docker image asset and its potential revisions. Required if using AppScopedStagingSynthesizer. Default: - no asset name
        :param build_args: Build args to pass to the ``docker build`` command. Since Docker build arguments are resolved before deployment, keys and values cannot refer to unresolved tokens (such as ``lambda.functionArn`` or ``queue.queueUrl``). Default: - no build args are passed
        :param build_secrets: Build secrets. Docker BuildKit must be enabled to use build secrets. Default: - no build secrets
        :param build_ssh: SSH agent socket or keys to pass to the ``docker build`` command. Docker BuildKit must be enabled to use the ssh flag Default: - no --ssh flag
        :param cache_disabled: Disable the cache and pass ``--no-cache`` to the ``docker build`` command. Default: - cache is used
        :param cache_from: Cache from options to pass to the ``docker build`` command. Default: - no cache from options are passed to the build command
        :param cache_to: Cache to options to pass to the ``docker build`` command. Default: - no cache to options are passed to the build command
        :param display_name: A display name for this asset. If supplied, the display name will be used in locations where the asset identifier is printed, like in the CLI progress information. If the same asset is added multiple times, the display name of the first occurrence is used. If ``assetName`` is given, it will also be used as the default ``displayName``. Otherwise, the default is the construct path of the ImageAsset construct, with respect to the enclosing stack. If the asset is produced by a construct helper function (such as ``lambda.Code.fromAssetImage()``), this will look like ``MyFunction/AssetImage``. We use the stack-relative construct path so that in the common case where you have multiple stacks with the same asset, we won't show something like ``/MyBetaStack/MyFunction/Code`` when you are actually deploying to production. Default: - Stack-relative construct path
        :param file: Path to the Dockerfile (relative to the directory). Default: 'Dockerfile'
        :param invalidation: Options to control which parameters are used to invalidate the asset hash. Default: - hash all parameters
        :param network_mode: Networking mode for the RUN commands during build. Support docker API 1.25+. Default: - no networking mode specified (the default networking mode ``NetworkMode.DEFAULT`` will be used)
        :param outputs: Outputs to pass to the ``docker build`` command. Default: - no outputs are passed to the build command (default outputs are used)
        :param platform: Platform to build for. *Requires Docker Buildx*. Default: - no platform specified (the current machine architecture will be used)
        :param target: Docker target to build to. Default: - no target
        :param extra_hash: Extra information to encode into the fingerprint (e.g. build instructions and other inputs). Default: - hash is only based on source content
        :param exclude: File paths matching the patterns will be excluded. See ``ignoreMode`` to set the matching behavior. Has no effect on Assets bundled using the ``bundling`` property. Default: - nothing is excluded
        :param follow_symlinks: A strategy for how to handle symlinks. Default: SymlinkFollowMode.NEVER
        :param ignore_mode: The ignore behavior to use for ``exclude`` patterns. Default: IgnoreMode.GLOB
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c8d9ec5e24290134189760e6d1b810fb7ee3324a2867dc530f78668f65c292d3)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = ContainerImageBuildProps(
            repository=repository,
            tag=tag,
            tag_prefix=tag_prefix,
            vpc=vpc,
            zstd_compression=zstd_compression,
            directory=directory,
            asset_name=asset_name,
            build_args=build_args,
            build_secrets=build_secrets,
            build_ssh=build_ssh,
            cache_disabled=cache_disabled,
            cache_from=cache_from,
            cache_to=cache_to,
            display_name=display_name,
            file=file,
            invalidation=invalidation,
            network_mode=network_mode,
            outputs=outputs,
            platform=platform,
            target=target,
            extra_hash=extra_hash,
            exclude=exclude,
            follow_symlinks=follow_symlinks,
            ignore_mode=ignore_mode,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="toEcsDockerImageCode")
    def to_ecs_docker_image_code(self) -> _aws_cdk_aws_ecs_ceddda9d.EcrImage:
        '''Get the instance of {@link ContainerImage} for an ECS task definition.'''
        return typing.cast(_aws_cdk_aws_ecs_ceddda9d.EcrImage, jsii.invoke(self, "toEcsDockerImageCode", []))

    @jsii.member(jsii_name="toLambdaDockerImageCode")
    def to_lambda_docker_image_code(
        self,
        *,
        cmd: typing.Optional[typing.Sequence[builtins.str]] = None,
        entrypoint: typing.Optional[typing.Sequence[builtins.str]] = None,
        working_directory: typing.Optional[builtins.str] = None,
    ) -> _aws_cdk_aws_lambda_ceddda9d.DockerImageCode:
        '''Get the instance of {@link DockerImageCode} for a Lambda function image.

        :param cmd: Specify or override the CMD on the specified Docker image or Dockerfile. This needs to be in the 'exec form', viz., ``[ 'executable', 'param1', 'param2' ]``. Default: - use the CMD specified in the docker image or Dockerfile.
        :param entrypoint: Specify or override the ENTRYPOINT on the specified Docker image or Dockerfile. An ENTRYPOINT allows you to configure a container that will run as an executable. This needs to be in the 'exec form', viz., ``[ 'executable', 'param1', 'param2' ]``. Default: - use the ENTRYPOINT in the docker image or Dockerfile.
        :param working_directory: Specify or override the WORKDIR on the specified Docker image or Dockerfile. A WORKDIR allows you to configure the working directory the container will use. Default: - use the WORKDIR in the docker image or Dockerfile.
        '''
        options = LambdaDockerImageOptions(
            cmd=cmd, entrypoint=entrypoint, working_directory=working_directory
        )

        return typing.cast(_aws_cdk_aws_lambda_ceddda9d.DockerImageCode, jsii.invoke(self, "toLambdaDockerImageCode", [options]))

    @builtins.property
    @jsii.member(jsii_name="grantPrincipal")
    def grant_principal(self) -> _aws_cdk_aws_iam_ceddda9d.IPrincipal:
        '''The principal to grant permissions to.'''
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.IPrincipal, jsii.get(self, "grantPrincipal"))

    @builtins.property
    @jsii.member(jsii_name="imageTag")
    def image_tag(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "imageTag"))

    @builtins.property
    @jsii.member(jsii_name="imageUri")
    def image_uri(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "imageUri"))

    @builtins.property
    @jsii.member(jsii_name="repository")
    def repository(self) -> _aws_cdk_aws_ecr_ceddda9d.IRepository:
        return typing.cast(_aws_cdk_aws_ecr_ceddda9d.IRepository, jsii.get(self, "repository"))


@jsii.data_type(
    jsii_type="deploy-time-build.ContainerImageBuildProps",
    jsii_struct_bases=[_aws_cdk_aws_ecr_assets_ceddda9d.DockerImageAssetProps],
    name_mapping={
        "exclude": "exclude",
        "follow_symlinks": "followSymlinks",
        "ignore_mode": "ignoreMode",
        "extra_hash": "extraHash",
        "asset_name": "assetName",
        "build_args": "buildArgs",
        "build_secrets": "buildSecrets",
        "build_ssh": "buildSsh",
        "cache_disabled": "cacheDisabled",
        "cache_from": "cacheFrom",
        "cache_to": "cacheTo",
        "display_name": "displayName",
        "file": "file",
        "invalidation": "invalidation",
        "network_mode": "networkMode",
        "outputs": "outputs",
        "platform": "platform",
        "target": "target",
        "directory": "directory",
        "repository": "repository",
        "tag": "tag",
        "tag_prefix": "tagPrefix",
        "vpc": "vpc",
        "zstd_compression": "zstdCompression",
    },
)
class ContainerImageBuildProps(_aws_cdk_aws_ecr_assets_ceddda9d.DockerImageAssetProps):
    def __init__(
        self,
        *,
        exclude: typing.Optional[typing.Sequence[builtins.str]] = None,
        follow_symlinks: typing.Optional[_aws_cdk_ceddda9d.SymlinkFollowMode] = None,
        ignore_mode: typing.Optional[_aws_cdk_ceddda9d.IgnoreMode] = None,
        extra_hash: typing.Optional[builtins.str] = None,
        asset_name: typing.Optional[builtins.str] = None,
        build_args: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        build_secrets: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        build_ssh: typing.Optional[builtins.str] = None,
        cache_disabled: typing.Optional[builtins.bool] = None,
        cache_from: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_ecr_assets_ceddda9d.DockerCacheOption, typing.Dict[builtins.str, typing.Any]]]] = None,
        cache_to: typing.Optional[typing.Union[_aws_cdk_aws_ecr_assets_ceddda9d.DockerCacheOption, typing.Dict[builtins.str, typing.Any]]] = None,
        display_name: typing.Optional[builtins.str] = None,
        file: typing.Optional[builtins.str] = None,
        invalidation: typing.Optional[typing.Union[_aws_cdk_aws_ecr_assets_ceddda9d.DockerImageAssetInvalidationOptions, typing.Dict[builtins.str, typing.Any]]] = None,
        network_mode: typing.Optional[_aws_cdk_aws_ecr_assets_ceddda9d.NetworkMode] = None,
        outputs: typing.Optional[typing.Sequence[builtins.str]] = None,
        platform: typing.Optional[_aws_cdk_aws_ecr_assets_ceddda9d.Platform] = None,
        target: typing.Optional[builtins.str] = None,
        directory: builtins.str,
        repository: typing.Optional[_aws_cdk_aws_ecr_ceddda9d.IRepository] = None,
        tag: typing.Optional[builtins.str] = None,
        tag_prefix: typing.Optional[builtins.str] = None,
        vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
        zstd_compression: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''
        :param exclude: File paths matching the patterns will be excluded. See ``ignoreMode`` to set the matching behavior. Has no effect on Assets bundled using the ``bundling`` property. Default: - nothing is excluded
        :param follow_symlinks: A strategy for how to handle symlinks. Default: SymlinkFollowMode.NEVER
        :param ignore_mode: The ignore behavior to use for ``exclude`` patterns. Default: IgnoreMode.GLOB
        :param extra_hash: Extra information to encode into the fingerprint (e.g. build instructions and other inputs). Default: - hash is only based on source content
        :param asset_name: Unique identifier of the docker image asset and its potential revisions. Required if using AppScopedStagingSynthesizer. Default: - no asset name
        :param build_args: Build args to pass to the ``docker build`` command. Since Docker build arguments are resolved before deployment, keys and values cannot refer to unresolved tokens (such as ``lambda.functionArn`` or ``queue.queueUrl``). Default: - no build args are passed
        :param build_secrets: Build secrets. Docker BuildKit must be enabled to use build secrets. Default: - no build secrets
        :param build_ssh: SSH agent socket or keys to pass to the ``docker build`` command. Docker BuildKit must be enabled to use the ssh flag Default: - no --ssh flag
        :param cache_disabled: Disable the cache and pass ``--no-cache`` to the ``docker build`` command. Default: - cache is used
        :param cache_from: Cache from options to pass to the ``docker build`` command. Default: - no cache from options are passed to the build command
        :param cache_to: Cache to options to pass to the ``docker build`` command. Default: - no cache to options are passed to the build command
        :param display_name: A display name for this asset. If supplied, the display name will be used in locations where the asset identifier is printed, like in the CLI progress information. If the same asset is added multiple times, the display name of the first occurrence is used. If ``assetName`` is given, it will also be used as the default ``displayName``. Otherwise, the default is the construct path of the ImageAsset construct, with respect to the enclosing stack. If the asset is produced by a construct helper function (such as ``lambda.Code.fromAssetImage()``), this will look like ``MyFunction/AssetImage``. We use the stack-relative construct path so that in the common case where you have multiple stacks with the same asset, we won't show something like ``/MyBetaStack/MyFunction/Code`` when you are actually deploying to production. Default: - Stack-relative construct path
        :param file: Path to the Dockerfile (relative to the directory). Default: 'Dockerfile'
        :param invalidation: Options to control which parameters are used to invalidate the asset hash. Default: - hash all parameters
        :param network_mode: Networking mode for the RUN commands during build. Support docker API 1.25+. Default: - no networking mode specified (the default networking mode ``NetworkMode.DEFAULT`` will be used)
        :param outputs: Outputs to pass to the ``docker build`` command. Default: - no outputs are passed to the build command (default outputs are used)
        :param platform: Platform to build for. *Requires Docker Buildx*. Default: - no platform specified (the current machine architecture will be used)
        :param target: Docker target to build to. Default: - no target
        :param directory: The directory where the Dockerfile is stored. Any directory inside with a name that matches the CDK output folder (cdk.out by default) will be excluded from the asset
        :param repository: The ECR repository to push the image. Default: create a new ECR repository
        :param tag: The tag when to push the image. Default: use assetHash as tag
        :param tag_prefix: Prefix to add to the image tag. Default: no prefix
        :param vpc: The VPC where your build job will be deployed. This VPC must have private subnets with NAT Gateways. Use this property when you want to control the outbound IP addresses that base images are pulled from. Default: No VPC used.
        :param zstd_compression: Use zstd for compressing a container image. Default: false
        '''
        if isinstance(cache_to, dict):
            cache_to = _aws_cdk_aws_ecr_assets_ceddda9d.DockerCacheOption(**cache_to)
        if isinstance(invalidation, dict):
            invalidation = _aws_cdk_aws_ecr_assets_ceddda9d.DockerImageAssetInvalidationOptions(**invalidation)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__04b8bd65bfca7b137073a2a9bdedee6b10ff714618c0018ffcc6ba5061c7bddc)
            check_type(argname="argument exclude", value=exclude, expected_type=type_hints["exclude"])
            check_type(argname="argument follow_symlinks", value=follow_symlinks, expected_type=type_hints["follow_symlinks"])
            check_type(argname="argument ignore_mode", value=ignore_mode, expected_type=type_hints["ignore_mode"])
            check_type(argname="argument extra_hash", value=extra_hash, expected_type=type_hints["extra_hash"])
            check_type(argname="argument asset_name", value=asset_name, expected_type=type_hints["asset_name"])
            check_type(argname="argument build_args", value=build_args, expected_type=type_hints["build_args"])
            check_type(argname="argument build_secrets", value=build_secrets, expected_type=type_hints["build_secrets"])
            check_type(argname="argument build_ssh", value=build_ssh, expected_type=type_hints["build_ssh"])
            check_type(argname="argument cache_disabled", value=cache_disabled, expected_type=type_hints["cache_disabled"])
            check_type(argname="argument cache_from", value=cache_from, expected_type=type_hints["cache_from"])
            check_type(argname="argument cache_to", value=cache_to, expected_type=type_hints["cache_to"])
            check_type(argname="argument display_name", value=display_name, expected_type=type_hints["display_name"])
            check_type(argname="argument file", value=file, expected_type=type_hints["file"])
            check_type(argname="argument invalidation", value=invalidation, expected_type=type_hints["invalidation"])
            check_type(argname="argument network_mode", value=network_mode, expected_type=type_hints["network_mode"])
            check_type(argname="argument outputs", value=outputs, expected_type=type_hints["outputs"])
            check_type(argname="argument platform", value=platform, expected_type=type_hints["platform"])
            check_type(argname="argument target", value=target, expected_type=type_hints["target"])
            check_type(argname="argument directory", value=directory, expected_type=type_hints["directory"])
            check_type(argname="argument repository", value=repository, expected_type=type_hints["repository"])
            check_type(argname="argument tag", value=tag, expected_type=type_hints["tag"])
            check_type(argname="argument tag_prefix", value=tag_prefix, expected_type=type_hints["tag_prefix"])
            check_type(argname="argument vpc", value=vpc, expected_type=type_hints["vpc"])
            check_type(argname="argument zstd_compression", value=zstd_compression, expected_type=type_hints["zstd_compression"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "directory": directory,
        }
        if exclude is not None:
            self._values["exclude"] = exclude
        if follow_symlinks is not None:
            self._values["follow_symlinks"] = follow_symlinks
        if ignore_mode is not None:
            self._values["ignore_mode"] = ignore_mode
        if extra_hash is not None:
            self._values["extra_hash"] = extra_hash
        if asset_name is not None:
            self._values["asset_name"] = asset_name
        if build_args is not None:
            self._values["build_args"] = build_args
        if build_secrets is not None:
            self._values["build_secrets"] = build_secrets
        if build_ssh is not None:
            self._values["build_ssh"] = build_ssh
        if cache_disabled is not None:
            self._values["cache_disabled"] = cache_disabled
        if cache_from is not None:
            self._values["cache_from"] = cache_from
        if cache_to is not None:
            self._values["cache_to"] = cache_to
        if display_name is not None:
            self._values["display_name"] = display_name
        if file is not None:
            self._values["file"] = file
        if invalidation is not None:
            self._values["invalidation"] = invalidation
        if network_mode is not None:
            self._values["network_mode"] = network_mode
        if outputs is not None:
            self._values["outputs"] = outputs
        if platform is not None:
            self._values["platform"] = platform
        if target is not None:
            self._values["target"] = target
        if repository is not None:
            self._values["repository"] = repository
        if tag is not None:
            self._values["tag"] = tag
        if tag_prefix is not None:
            self._values["tag_prefix"] = tag_prefix
        if vpc is not None:
            self._values["vpc"] = vpc
        if zstd_compression is not None:
            self._values["zstd_compression"] = zstd_compression

    @builtins.property
    def exclude(self) -> typing.Optional[typing.List[builtins.str]]:
        '''File paths matching the patterns will be excluded.

        See ``ignoreMode`` to set the matching behavior.
        Has no effect on Assets bundled using the ``bundling`` property.

        :default: - nothing is excluded
        '''
        result = self._values.get("exclude")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def follow_symlinks(self) -> typing.Optional[_aws_cdk_ceddda9d.SymlinkFollowMode]:
        '''A strategy for how to handle symlinks.

        :default: SymlinkFollowMode.NEVER
        '''
        result = self._values.get("follow_symlinks")
        return typing.cast(typing.Optional[_aws_cdk_ceddda9d.SymlinkFollowMode], result)

    @builtins.property
    def ignore_mode(self) -> typing.Optional[_aws_cdk_ceddda9d.IgnoreMode]:
        '''The ignore behavior to use for ``exclude`` patterns.

        :default: IgnoreMode.GLOB
        '''
        result = self._values.get("ignore_mode")
        return typing.cast(typing.Optional[_aws_cdk_ceddda9d.IgnoreMode], result)

    @builtins.property
    def extra_hash(self) -> typing.Optional[builtins.str]:
        '''Extra information to encode into the fingerprint (e.g. build instructions and other inputs).

        :default: - hash is only based on source content
        '''
        result = self._values.get("extra_hash")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def asset_name(self) -> typing.Optional[builtins.str]:
        '''Unique identifier of the docker image asset and its potential revisions.

        Required if using AppScopedStagingSynthesizer.

        :default: - no asset name
        '''
        result = self._values.get("asset_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def build_args(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''Build args to pass to the ``docker build`` command.

        Since Docker build arguments are resolved before deployment, keys and
        values cannot refer to unresolved tokens (such as ``lambda.functionArn`` or
        ``queue.queueUrl``).

        :default: - no build args are passed
        '''
        result = self._values.get("build_args")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def build_secrets(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''Build secrets.

        Docker BuildKit must be enabled to use build secrets.

        :default: - no build secrets

        :see: https://docs.docker.com/build/buildkit/

        Example::

            import { DockerBuildSecret } from 'aws-cdk-lib';
            
            const buildSecrets = {
              'MY_SECRET': DockerBuildSecret.fromSrc('file.txt')
            };
        '''
        result = self._values.get("build_secrets")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def build_ssh(self) -> typing.Optional[builtins.str]:
        '''SSH agent socket or keys to pass to the ``docker build`` command.

        Docker BuildKit must be enabled to use the ssh flag

        :default: - no --ssh flag

        :see: https://docs.docker.com/build/buildkit/
        '''
        result = self._values.get("build_ssh")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def cache_disabled(self) -> typing.Optional[builtins.bool]:
        '''Disable the cache and pass ``--no-cache`` to the ``docker build`` command.

        :default: - cache is used
        '''
        result = self._values.get("cache_disabled")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def cache_from(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_ecr_assets_ceddda9d.DockerCacheOption]]:
        '''Cache from options to pass to the ``docker build`` command.

        :default: - no cache from options are passed to the build command

        :see: https://docs.docker.com/build/cache/backends/
        '''
        result = self._values.get("cache_from")
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_ecr_assets_ceddda9d.DockerCacheOption]], result)

    @builtins.property
    def cache_to(
        self,
    ) -> typing.Optional[_aws_cdk_aws_ecr_assets_ceddda9d.DockerCacheOption]:
        '''Cache to options to pass to the ``docker build`` command.

        :default: - no cache to options are passed to the build command

        :see: https://docs.docker.com/build/cache/backends/
        '''
        result = self._values.get("cache_to")
        return typing.cast(typing.Optional[_aws_cdk_aws_ecr_assets_ceddda9d.DockerCacheOption], result)

    @builtins.property
    def display_name(self) -> typing.Optional[builtins.str]:
        '''A display name for this asset.

        If supplied, the display name will be used in locations where the asset
        identifier is printed, like in the CLI progress information. If the same
        asset is added multiple times, the display name of the first occurrence is
        used.

        If ``assetName`` is given, it will also be used as the default ``displayName``.
        Otherwise, the default is the construct path of the ImageAsset construct,
        with respect to the enclosing stack. If the asset is produced by a
        construct helper function (such as ``lambda.Code.fromAssetImage()``), this
        will look like ``MyFunction/AssetImage``.

        We use the stack-relative construct path so that in the common case where
        you have multiple stacks with the same asset, we won't show something like
        ``/MyBetaStack/MyFunction/Code`` when you are actually deploying to
        production.

        :default: - Stack-relative construct path
        '''
        result = self._values.get("display_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def file(self) -> typing.Optional[builtins.str]:
        '''Path to the Dockerfile (relative to the directory).

        :default: 'Dockerfile'
        '''
        result = self._values.get("file")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def invalidation(
        self,
    ) -> typing.Optional[_aws_cdk_aws_ecr_assets_ceddda9d.DockerImageAssetInvalidationOptions]:
        '''Options to control which parameters are used to invalidate the asset hash.

        :default: - hash all parameters
        '''
        result = self._values.get("invalidation")
        return typing.cast(typing.Optional[_aws_cdk_aws_ecr_assets_ceddda9d.DockerImageAssetInvalidationOptions], result)

    @builtins.property
    def network_mode(
        self,
    ) -> typing.Optional[_aws_cdk_aws_ecr_assets_ceddda9d.NetworkMode]:
        '''Networking mode for the RUN commands during build.

        Support docker API 1.25+.

        :default: - no networking mode specified (the default networking mode ``NetworkMode.DEFAULT`` will be used)
        '''
        result = self._values.get("network_mode")
        return typing.cast(typing.Optional[_aws_cdk_aws_ecr_assets_ceddda9d.NetworkMode], result)

    @builtins.property
    def outputs(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Outputs to pass to the ``docker build`` command.

        :default: - no outputs are passed to the build command (default outputs are used)

        :see: https://docs.docker.com/engine/reference/commandline/build/#custom-build-outputs
        '''
        result = self._values.get("outputs")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def platform(self) -> typing.Optional[_aws_cdk_aws_ecr_assets_ceddda9d.Platform]:
        '''Platform to build for.

        *Requires Docker Buildx*.

        :default: - no platform specified (the current machine architecture will be used)
        '''
        result = self._values.get("platform")
        return typing.cast(typing.Optional[_aws_cdk_aws_ecr_assets_ceddda9d.Platform], result)

    @builtins.property
    def target(self) -> typing.Optional[builtins.str]:
        '''Docker target to build to.

        :default: - no target
        '''
        result = self._values.get("target")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def directory(self) -> builtins.str:
        '''The directory where the Dockerfile is stored.

        Any directory inside with a name that matches the CDK output folder (cdk.out by default) will be excluded from the asset
        '''
        result = self._values.get("directory")
        assert result is not None, "Required property 'directory' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def repository(self) -> typing.Optional[_aws_cdk_aws_ecr_ceddda9d.IRepository]:
        '''The ECR repository to push the image.

        :default: create a new ECR repository
        '''
        result = self._values.get("repository")
        return typing.cast(typing.Optional[_aws_cdk_aws_ecr_ceddda9d.IRepository], result)

    @builtins.property
    def tag(self) -> typing.Optional[builtins.str]:
        '''The tag when to push the image.

        :default: use assetHash as tag
        '''
        result = self._values.get("tag")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def tag_prefix(self) -> typing.Optional[builtins.str]:
        '''Prefix to add to the image tag.

        :default: no prefix
        '''
        result = self._values.get("tag_prefix")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def vpc(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc]:
        '''The VPC where your build job will be deployed. This VPC must have private subnets with NAT Gateways.

        Use this property when you want to control the outbound IP addresses that base images are pulled from.

        :default: No VPC used.
        '''
        result = self._values.get("vpc")
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc], result)

    @builtins.property
    def zstd_compression(self) -> typing.Optional[builtins.bool]:
        '''Use zstd for compressing a container image.

        :default: false
        '''
        result = self._values.get("zstd_compression")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ContainerImageBuildProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="deploy-time-build.LambdaDockerImageOptions",
    jsii_struct_bases=[],
    name_mapping={
        "cmd": "cmd",
        "entrypoint": "entrypoint",
        "working_directory": "workingDirectory",
    },
)
class LambdaDockerImageOptions:
    def __init__(
        self,
        *,
        cmd: typing.Optional[typing.Sequence[builtins.str]] = None,
        entrypoint: typing.Optional[typing.Sequence[builtins.str]] = None,
        working_directory: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Options for configuring Lambda Docker image code.

        :param cmd: Specify or override the CMD on the specified Docker image or Dockerfile. This needs to be in the 'exec form', viz., ``[ 'executable', 'param1', 'param2' ]``. Default: - use the CMD specified in the docker image or Dockerfile.
        :param entrypoint: Specify or override the ENTRYPOINT on the specified Docker image or Dockerfile. An ENTRYPOINT allows you to configure a container that will run as an executable. This needs to be in the 'exec form', viz., ``[ 'executable', 'param1', 'param2' ]``. Default: - use the ENTRYPOINT in the docker image or Dockerfile.
        :param working_directory: Specify or override the WORKDIR on the specified Docker image or Dockerfile. A WORKDIR allows you to configure the working directory the container will use. Default: - use the WORKDIR in the docker image or Dockerfile.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__75351adc28bf90e2070c8c4b8712f8b6a18be2f433af14f5004f50b4ac0fe6bd)
            check_type(argname="argument cmd", value=cmd, expected_type=type_hints["cmd"])
            check_type(argname="argument entrypoint", value=entrypoint, expected_type=type_hints["entrypoint"])
            check_type(argname="argument working_directory", value=working_directory, expected_type=type_hints["working_directory"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if cmd is not None:
            self._values["cmd"] = cmd
        if entrypoint is not None:
            self._values["entrypoint"] = entrypoint
        if working_directory is not None:
            self._values["working_directory"] = working_directory

    @builtins.property
    def cmd(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Specify or override the CMD on the specified Docker image or Dockerfile.

        This needs to be in the 'exec form', viz., ``[ 'executable', 'param1', 'param2' ]``.

        :default: - use the CMD specified in the docker image or Dockerfile.

        :see: `https://docs.docker.com/engine/reference/builder/#cmd <https://docs.docker.com/engine/reference/builder/#cmd>`_
        '''
        result = self._values.get("cmd")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def entrypoint(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Specify or override the ENTRYPOINT on the specified Docker image or Dockerfile.

        An ENTRYPOINT allows you to configure a container that will run as an executable.
        This needs to be in the 'exec form', viz., ``[ 'executable', 'param1', 'param2' ]``.

        :default: - use the ENTRYPOINT in the docker image or Dockerfile.

        :see: `https://docs.docker.com/engine/reference/builder/#entrypoint <https://docs.docker.com/engine/reference/builder/#entrypoint>`_
        '''
        result = self._values.get("entrypoint")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def working_directory(self) -> typing.Optional[builtins.str]:
        '''Specify or override the WORKDIR on the specified Docker image or Dockerfile.

        A WORKDIR allows you to configure the working directory the container will use.

        :default: - use the WORKDIR in the docker image or Dockerfile.

        :see: `https://docs.docker.com/engine/reference/builder/#workdir <https://docs.docker.com/engine/reference/builder/#workdir>`_
        '''
        result = self._values.get("working_directory")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "LambdaDockerImageOptions(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.implements(_aws_cdk_aws_iam_ceddda9d.IGrantable)
class NodejsBuild(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="deploy-time-build.NodejsBuild",
):
    '''Build Node.js app and optionally publish the artifact to an S3 bucket.'''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        assets: typing.Sequence[typing.Union[AssetConfig, typing.Dict[builtins.str, typing.Any]]],
        destination_bucket: _aws_cdk_aws_s3_ceddda9d.IBucket,
        output_source_directory: builtins.str,
        build_commands: typing.Optional[typing.Sequence[builtins.str]] = None,
        build_environment: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        destination_key_prefix: typing.Optional[builtins.str] = None,
        distribution: typing.Optional[_aws_cdk_aws_cloudfront_ceddda9d.IDistribution] = None,
        exclude_common_files: typing.Optional[builtins.bool] = None,
        nodejs_version: typing.Optional[jsii.Number] = None,
        output_env_file: typing.Optional[builtins.bool] = None,
        working_directory: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param assets: The AssetProps from which s3-assets are created and copied to the build environment.
        :param destination_bucket: S3 Bucket to which your build artifacts are finally deployed.
        :param output_source_directory: Relative path from the working directory to the directory where the build artifacts are output.
        :param build_commands: Shell commands to build your project. They are executed on the working directory you specified. Default: ['npm run build']
        :param build_environment: Environment variables injected to the build environment. You can use CDK deploy-time values as well as literals. Default: {}
        :param destination_key_prefix: Key prefix to deploy your build artifact. Default: '/'
        :param distribution: The distribution you are using to publish you build artifact. If any specified, the caches are invalidated on new artifact deployments. Default: No distribution
        :param exclude_common_files: If true, common unnecessary files/directories such as .DS_Store, .git, node_modules, etc are excluded from the assets by default. Default: true
        :param nodejs_version: The version of Node.js to use in a build environment. Available versions: 12, 14, 16, 18, 20, and 22. Default: 18
        :param output_env_file: If true, a .env file is uploaded to an S3 bucket with values of ``buildEnvironment`` property. You can copy it to your local machine by running the command in the stack output. Default: false
        :param working_directory: Relative path from the build directory to the directory where build commands run. Default: assetProps[0].extractPath
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3c71280e3aba0c9512a180cd9b287eb9fa61158e0b247676de51e6b48a0b58d3)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = NodejsBuildProps(
            assets=assets,
            destination_bucket=destination_bucket,
            output_source_directory=output_source_directory,
            build_commands=build_commands,
            build_environment=build_environment,
            destination_key_prefix=destination_key_prefix,
            distribution=distribution,
            exclude_common_files=exclude_common_files,
            nodejs_version=nodejs_version,
            output_env_file=output_env_file,
            working_directory=working_directory,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property
    @jsii.member(jsii_name="grantPrincipal")
    def grant_principal(self) -> _aws_cdk_aws_iam_ceddda9d.IPrincipal:
        '''The principal to grant permissions to.'''
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.IPrincipal, jsii.get(self, "grantPrincipal"))


@jsii.data_type(
    jsii_type="deploy-time-build.NodejsBuildProps",
    jsii_struct_bases=[],
    name_mapping={
        "assets": "assets",
        "destination_bucket": "destinationBucket",
        "output_source_directory": "outputSourceDirectory",
        "build_commands": "buildCommands",
        "build_environment": "buildEnvironment",
        "destination_key_prefix": "destinationKeyPrefix",
        "distribution": "distribution",
        "exclude_common_files": "excludeCommonFiles",
        "nodejs_version": "nodejsVersion",
        "output_env_file": "outputEnvFile",
        "working_directory": "workingDirectory",
    },
)
class NodejsBuildProps:
    def __init__(
        self,
        *,
        assets: typing.Sequence[typing.Union[AssetConfig, typing.Dict[builtins.str, typing.Any]]],
        destination_bucket: _aws_cdk_aws_s3_ceddda9d.IBucket,
        output_source_directory: builtins.str,
        build_commands: typing.Optional[typing.Sequence[builtins.str]] = None,
        build_environment: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        destination_key_prefix: typing.Optional[builtins.str] = None,
        distribution: typing.Optional[_aws_cdk_aws_cloudfront_ceddda9d.IDistribution] = None,
        exclude_common_files: typing.Optional[builtins.bool] = None,
        nodejs_version: typing.Optional[jsii.Number] = None,
        output_env_file: typing.Optional[builtins.bool] = None,
        working_directory: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param assets: The AssetProps from which s3-assets are created and copied to the build environment.
        :param destination_bucket: S3 Bucket to which your build artifacts are finally deployed.
        :param output_source_directory: Relative path from the working directory to the directory where the build artifacts are output.
        :param build_commands: Shell commands to build your project. They are executed on the working directory you specified. Default: ['npm run build']
        :param build_environment: Environment variables injected to the build environment. You can use CDK deploy-time values as well as literals. Default: {}
        :param destination_key_prefix: Key prefix to deploy your build artifact. Default: '/'
        :param distribution: The distribution you are using to publish you build artifact. If any specified, the caches are invalidated on new artifact deployments. Default: No distribution
        :param exclude_common_files: If true, common unnecessary files/directories such as .DS_Store, .git, node_modules, etc are excluded from the assets by default. Default: true
        :param nodejs_version: The version of Node.js to use in a build environment. Available versions: 12, 14, 16, 18, 20, and 22. Default: 18
        :param output_env_file: If true, a .env file is uploaded to an S3 bucket with values of ``buildEnvironment`` property. You can copy it to your local machine by running the command in the stack output. Default: false
        :param working_directory: Relative path from the build directory to the directory where build commands run. Default: assetProps[0].extractPath
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3ad4ac39ec4adf96af9bc19519711c6c5d0d566e989bcafec2dac62ce03d3294)
            check_type(argname="argument assets", value=assets, expected_type=type_hints["assets"])
            check_type(argname="argument destination_bucket", value=destination_bucket, expected_type=type_hints["destination_bucket"])
            check_type(argname="argument output_source_directory", value=output_source_directory, expected_type=type_hints["output_source_directory"])
            check_type(argname="argument build_commands", value=build_commands, expected_type=type_hints["build_commands"])
            check_type(argname="argument build_environment", value=build_environment, expected_type=type_hints["build_environment"])
            check_type(argname="argument destination_key_prefix", value=destination_key_prefix, expected_type=type_hints["destination_key_prefix"])
            check_type(argname="argument distribution", value=distribution, expected_type=type_hints["distribution"])
            check_type(argname="argument exclude_common_files", value=exclude_common_files, expected_type=type_hints["exclude_common_files"])
            check_type(argname="argument nodejs_version", value=nodejs_version, expected_type=type_hints["nodejs_version"])
            check_type(argname="argument output_env_file", value=output_env_file, expected_type=type_hints["output_env_file"])
            check_type(argname="argument working_directory", value=working_directory, expected_type=type_hints["working_directory"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "assets": assets,
            "destination_bucket": destination_bucket,
            "output_source_directory": output_source_directory,
        }
        if build_commands is not None:
            self._values["build_commands"] = build_commands
        if build_environment is not None:
            self._values["build_environment"] = build_environment
        if destination_key_prefix is not None:
            self._values["destination_key_prefix"] = destination_key_prefix
        if distribution is not None:
            self._values["distribution"] = distribution
        if exclude_common_files is not None:
            self._values["exclude_common_files"] = exclude_common_files
        if nodejs_version is not None:
            self._values["nodejs_version"] = nodejs_version
        if output_env_file is not None:
            self._values["output_env_file"] = output_env_file
        if working_directory is not None:
            self._values["working_directory"] = working_directory

    @builtins.property
    def assets(self) -> typing.List[AssetConfig]:
        '''The AssetProps from which s3-assets are created and copied to the build environment.'''
        result = self._values.get("assets")
        assert result is not None, "Required property 'assets' is missing"
        return typing.cast(typing.List[AssetConfig], result)

    @builtins.property
    def destination_bucket(self) -> _aws_cdk_aws_s3_ceddda9d.IBucket:
        '''S3 Bucket to which your build artifacts are finally deployed.'''
        result = self._values.get("destination_bucket")
        assert result is not None, "Required property 'destination_bucket' is missing"
        return typing.cast(_aws_cdk_aws_s3_ceddda9d.IBucket, result)

    @builtins.property
    def output_source_directory(self) -> builtins.str:
        '''Relative path from the working directory to the directory where the build artifacts are output.'''
        result = self._values.get("output_source_directory")
        assert result is not None, "Required property 'output_source_directory' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def build_commands(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Shell commands to build your project.

        They are executed on the working directory you specified.

        :default: ['npm run build']
        '''
        result = self._values.get("build_commands")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def build_environment(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''Environment variables injected to the build environment.

        You can use CDK deploy-time values as well as literals.

        :default: {}
        '''
        result = self._values.get("build_environment")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def destination_key_prefix(self) -> typing.Optional[builtins.str]:
        '''Key prefix to deploy your build artifact.

        :default: '/'
        '''
        result = self._values.get("destination_key_prefix")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def distribution(
        self,
    ) -> typing.Optional[_aws_cdk_aws_cloudfront_ceddda9d.IDistribution]:
        '''The distribution you are using to publish you build artifact.

        If any specified, the caches are invalidated on new artifact deployments.

        :default: No distribution
        '''
        result = self._values.get("distribution")
        return typing.cast(typing.Optional[_aws_cdk_aws_cloudfront_ceddda9d.IDistribution], result)

    @builtins.property
    def exclude_common_files(self) -> typing.Optional[builtins.bool]:
        '''If true, common unnecessary files/directories such as .DS_Store, .git, node_modules, etc are excluded from the assets by default.

        :default: true
        '''
        result = self._values.get("exclude_common_files")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def nodejs_version(self) -> typing.Optional[jsii.Number]:
        '''The version of Node.js to use in a build environment. Available versions: 12, 14, 16, 18, 20, and 22.

        :default: 18
        '''
        result = self._values.get("nodejs_version")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def output_env_file(self) -> typing.Optional[builtins.bool]:
        '''If true, a .env file is uploaded to an S3 bucket with values of ``buildEnvironment`` property. You can copy it to your local machine by running the command in the stack output.

        :default: false
        '''
        result = self._values.get("output_env_file")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def working_directory(self) -> typing.Optional[builtins.str]:
        '''Relative path from the build directory to the directory where build commands run.

        :default: assetProps[0].extractPath
        '''
        result = self._values.get("working_directory")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "NodejsBuildProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class SociIndexBuild(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="deploy-time-build.SociIndexBuild",
):
    '''(deprecated) Build and publish a SOCI index for a container image.

    A SOCI index helps start Fargate tasks faster in some cases.
    Please read the following document for more details: https://docs.aws.amazon.com/AmazonECS/latest/userguide/container-considerations.html

    :deprecated:

    Use {@link SociIndexV2Build } instead. Customers new to SOCI on AWS Fargate can only use SOCI index manifest v2.
    See `this article <https://aws.amazon.com/blogs/containers/improving-amazon-ecs-deployment-consistency-with-soci-index-manifest-v2/>`_ for more details.

    :stability: deprecated
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        image_tag: builtins.str,
        repository: _aws_cdk_aws_ecr_ceddda9d.IRepository,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param image_tag: The tag of the container image you want to build index for.
        :param repository: The ECR repository your container image is stored. You can only specify a repository in the same environment (account/region). The index artifact will be uploaded to this repository.

        :stability: deprecated
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__96c9f98c6307010e55fc9821910e21e80021318519921a9cd9371c8e3551dc20)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = SociIndexBuildProps(image_tag=image_tag, repository=repository)

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="fromDockerImageAsset")
    @builtins.classmethod
    def from_docker_image_asset(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        image_asset: _aws_cdk_aws_ecr_assets_ceddda9d.DockerImageAsset,
    ) -> "SociIndexBuild":
        '''(deprecated) A utility method to create a SociIndexBuild construct from a DockerImageAsset instance.

        :param scope: -
        :param id: -
        :param image_asset: -

        :stability: deprecated
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__379044f417588697cb394f0bbb2af9baa69f581f01fe14f37a5e9f01ea6c57f3)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument image_asset", value=image_asset, expected_type=type_hints["image_asset"])
        return typing.cast("SociIndexBuild", jsii.sinvoke(cls, "fromDockerImageAsset", [scope, id, image_asset]))


@jsii.data_type(
    jsii_type="deploy-time-build.SociIndexBuildProps",
    jsii_struct_bases=[],
    name_mapping={"image_tag": "imageTag", "repository": "repository"},
)
class SociIndexBuildProps:
    def __init__(
        self,
        *,
        image_tag: builtins.str,
        repository: _aws_cdk_aws_ecr_ceddda9d.IRepository,
    ) -> None:
        '''
        :param image_tag: The tag of the container image you want to build index for.
        :param repository: The ECR repository your container image is stored. You can only specify a repository in the same environment (account/region). The index artifact will be uploaded to this repository.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8ad6c57fd92a51686139131b933189975e9f3ea79f0e01e3cdb6be816eed7cb1)
            check_type(argname="argument image_tag", value=image_tag, expected_type=type_hints["image_tag"])
            check_type(argname="argument repository", value=repository, expected_type=type_hints["repository"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "image_tag": image_tag,
            "repository": repository,
        }

    @builtins.property
    def image_tag(self) -> builtins.str:
        '''The tag of the container image you want to build index for.'''
        result = self._values.get("image_tag")
        assert result is not None, "Required property 'image_tag' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def repository(self) -> _aws_cdk_aws_ecr_ceddda9d.IRepository:
        '''The ECR repository your container image is stored.

        You can only specify a repository in the same environment (account/region).
        The index artifact will be uploaded to this repository.
        '''
        result = self._values.get("repository")
        assert result is not None, "Required property 'repository' is missing"
        return typing.cast(_aws_cdk_aws_ecr_ceddda9d.IRepository, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "SociIndexBuildProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class SociIndexV2Build(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="deploy-time-build.SociIndexV2Build",
):
    '''Build and publish a SOCI index for a container image.

    A SOCI index helps start Fargate tasks faster in some cases.
    Please read the following document for more details: https://docs.aws.amazon.com/AmazonECS/latest/userguide/container-considerations.html
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        input_image_tag: builtins.str,
        repository: _aws_cdk_aws_ecr_ceddda9d.IRepository,
        output_image_tag: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param input_image_tag: The tag of the container image you want to build index for.
        :param repository: The ECR repository your container image is stored. You can only specify a repository in the same environment (account/region). The index artifact will be uploaded to this repository.
        :param output_image_tag: The tag of the output container image embedded with SOCI index. Default: ``${inputImageTag}-soci``
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4c1647b890bfb5351778b6354dee86a5aaf1387660d9aedd6995955025b1dbda)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = SociIndexV2BuildProps(
            input_image_tag=input_image_tag,
            repository=repository,
            output_image_tag=output_image_tag,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="fromDockerImageAsset")
    @builtins.classmethod
    def from_docker_image_asset(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        image_asset: _aws_cdk_aws_ecr_assets_ceddda9d.DockerImageAsset,
    ) -> "SociIndexV2Build":
        '''A utility method to create a SociIndexBuild construct from a DockerImageAsset instance.

        :param scope: -
        :param id: -
        :param image_asset: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1c38bbcaa8fd085c8837fe0e2820457722cb3fd6a81f8aa9390ecd32dece8abc)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument image_asset", value=image_asset, expected_type=type_hints["image_asset"])
        return typing.cast("SociIndexV2Build", jsii.sinvoke(cls, "fromDockerImageAsset", [scope, id, image_asset]))

    @jsii.member(jsii_name="toEcsDockerImageCode")
    def to_ecs_docker_image_code(self) -> _aws_cdk_aws_ecs_ceddda9d.EcrImage:
        '''Get the instance of image embedded with SOCI v2 index for an ECS task definition.

        When using this image returned from this function, your deployment waits until
        the index build complete and then start deploying after the image with index ready.
        '''
        return typing.cast(_aws_cdk_aws_ecs_ceddda9d.EcrImage, jsii.invoke(self, "toEcsDockerImageCode", []))

    @builtins.property
    @jsii.member(jsii_name="outputImageTag")
    def output_image_tag(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "outputImageTag"))

    @builtins.property
    @jsii.member(jsii_name="repository")
    def repository(self) -> _aws_cdk_aws_ecr_ceddda9d.IRepository:
        return typing.cast(_aws_cdk_aws_ecr_ceddda9d.IRepository, jsii.get(self, "repository"))


@jsii.data_type(
    jsii_type="deploy-time-build.SociIndexV2BuildProps",
    jsii_struct_bases=[],
    name_mapping={
        "input_image_tag": "inputImageTag",
        "repository": "repository",
        "output_image_tag": "outputImageTag",
    },
)
class SociIndexV2BuildProps:
    def __init__(
        self,
        *,
        input_image_tag: builtins.str,
        repository: _aws_cdk_aws_ecr_ceddda9d.IRepository,
        output_image_tag: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param input_image_tag: The tag of the container image you want to build index for.
        :param repository: The ECR repository your container image is stored. You can only specify a repository in the same environment (account/region). The index artifact will be uploaded to this repository.
        :param output_image_tag: The tag of the output container image embedded with SOCI index. Default: ``${inputImageTag}-soci``
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5ed2883b1f7c70fc7b86e345c0f7b329f138abacd1ecb7a9b0ea4b72b7554928)
            check_type(argname="argument input_image_tag", value=input_image_tag, expected_type=type_hints["input_image_tag"])
            check_type(argname="argument repository", value=repository, expected_type=type_hints["repository"])
            check_type(argname="argument output_image_tag", value=output_image_tag, expected_type=type_hints["output_image_tag"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "input_image_tag": input_image_tag,
            "repository": repository,
        }
        if output_image_tag is not None:
            self._values["output_image_tag"] = output_image_tag

    @builtins.property
    def input_image_tag(self) -> builtins.str:
        '''The tag of the container image you want to build index for.'''
        result = self._values.get("input_image_tag")
        assert result is not None, "Required property 'input_image_tag' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def repository(self) -> _aws_cdk_aws_ecr_ceddda9d.IRepository:
        '''The ECR repository your container image is stored.

        You can only specify a repository in the same environment (account/region).
        The index artifact will be uploaded to this repository.
        '''
        result = self._values.get("repository")
        assert result is not None, "Required property 'repository' is missing"
        return typing.cast(_aws_cdk_aws_ecr_ceddda9d.IRepository, result)

    @builtins.property
    def output_image_tag(self) -> typing.Optional[builtins.str]:
        '''The tag of the output container image embedded with SOCI index.

        :default: ``${inputImageTag}-soci``
        '''
        result = self._values.get("output_image_tag")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "SociIndexV2BuildProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "AssetConfig",
    "ContainerImageBuild",
    "ContainerImageBuildProps",
    "LambdaDockerImageOptions",
    "NodejsBuild",
    "NodejsBuildProps",
    "SociIndexBuild",
    "SociIndexBuildProps",
    "SociIndexV2Build",
    "SociIndexV2BuildProps",
]

publication.publish()

def _typecheckingstub__b8e57ab5756054ba32d3c99212a85d1a9c6d99aadd68fa6b763c12872e443675(
    *,
    asset_hash: typing.Optional[builtins.str] = None,
    asset_hash_type: typing.Optional[_aws_cdk_ceddda9d.AssetHashType] = None,
    bundling: typing.Optional[typing.Union[_aws_cdk_ceddda9d.BundlingOptions, typing.Dict[builtins.str, typing.Any]]] = None,
    exclude: typing.Optional[typing.Sequence[builtins.str]] = None,
    follow_symlinks: typing.Optional[_aws_cdk_ceddda9d.SymlinkFollowMode] = None,
    ignore_mode: typing.Optional[_aws_cdk_ceddda9d.IgnoreMode] = None,
    deploy_time: typing.Optional[builtins.bool] = None,
    display_name: typing.Optional[builtins.str] = None,
    readers: typing.Optional[typing.Sequence[_aws_cdk_aws_iam_ceddda9d.IGrantable]] = None,
    source_kms_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey] = None,
    path: builtins.str,
    commands: typing.Optional[typing.Sequence[builtins.str]] = None,
    extract_path: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c8d9ec5e24290134189760e6d1b810fb7ee3324a2867dc530f78668f65c292d3(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    repository: typing.Optional[_aws_cdk_aws_ecr_ceddda9d.IRepository] = None,
    tag: typing.Optional[builtins.str] = None,
    tag_prefix: typing.Optional[builtins.str] = None,
    vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    zstd_compression: typing.Optional[builtins.bool] = None,
    directory: builtins.str,
    asset_name: typing.Optional[builtins.str] = None,
    build_args: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    build_secrets: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    build_ssh: typing.Optional[builtins.str] = None,
    cache_disabled: typing.Optional[builtins.bool] = None,
    cache_from: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_ecr_assets_ceddda9d.DockerCacheOption, typing.Dict[builtins.str, typing.Any]]]] = None,
    cache_to: typing.Optional[typing.Union[_aws_cdk_aws_ecr_assets_ceddda9d.DockerCacheOption, typing.Dict[builtins.str, typing.Any]]] = None,
    display_name: typing.Optional[builtins.str] = None,
    file: typing.Optional[builtins.str] = None,
    invalidation: typing.Optional[typing.Union[_aws_cdk_aws_ecr_assets_ceddda9d.DockerImageAssetInvalidationOptions, typing.Dict[builtins.str, typing.Any]]] = None,
    network_mode: typing.Optional[_aws_cdk_aws_ecr_assets_ceddda9d.NetworkMode] = None,
    outputs: typing.Optional[typing.Sequence[builtins.str]] = None,
    platform: typing.Optional[_aws_cdk_aws_ecr_assets_ceddda9d.Platform] = None,
    target: typing.Optional[builtins.str] = None,
    extra_hash: typing.Optional[builtins.str] = None,
    exclude: typing.Optional[typing.Sequence[builtins.str]] = None,
    follow_symlinks: typing.Optional[_aws_cdk_ceddda9d.SymlinkFollowMode] = None,
    ignore_mode: typing.Optional[_aws_cdk_ceddda9d.IgnoreMode] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__04b8bd65bfca7b137073a2a9bdedee6b10ff714618c0018ffcc6ba5061c7bddc(
    *,
    exclude: typing.Optional[typing.Sequence[builtins.str]] = None,
    follow_symlinks: typing.Optional[_aws_cdk_ceddda9d.SymlinkFollowMode] = None,
    ignore_mode: typing.Optional[_aws_cdk_ceddda9d.IgnoreMode] = None,
    extra_hash: typing.Optional[builtins.str] = None,
    asset_name: typing.Optional[builtins.str] = None,
    build_args: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    build_secrets: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    build_ssh: typing.Optional[builtins.str] = None,
    cache_disabled: typing.Optional[builtins.bool] = None,
    cache_from: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_ecr_assets_ceddda9d.DockerCacheOption, typing.Dict[builtins.str, typing.Any]]]] = None,
    cache_to: typing.Optional[typing.Union[_aws_cdk_aws_ecr_assets_ceddda9d.DockerCacheOption, typing.Dict[builtins.str, typing.Any]]] = None,
    display_name: typing.Optional[builtins.str] = None,
    file: typing.Optional[builtins.str] = None,
    invalidation: typing.Optional[typing.Union[_aws_cdk_aws_ecr_assets_ceddda9d.DockerImageAssetInvalidationOptions, typing.Dict[builtins.str, typing.Any]]] = None,
    network_mode: typing.Optional[_aws_cdk_aws_ecr_assets_ceddda9d.NetworkMode] = None,
    outputs: typing.Optional[typing.Sequence[builtins.str]] = None,
    platform: typing.Optional[_aws_cdk_aws_ecr_assets_ceddda9d.Platform] = None,
    target: typing.Optional[builtins.str] = None,
    directory: builtins.str,
    repository: typing.Optional[_aws_cdk_aws_ecr_ceddda9d.IRepository] = None,
    tag: typing.Optional[builtins.str] = None,
    tag_prefix: typing.Optional[builtins.str] = None,
    vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    zstd_compression: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__75351adc28bf90e2070c8c4b8712f8b6a18be2f433af14f5004f50b4ac0fe6bd(
    *,
    cmd: typing.Optional[typing.Sequence[builtins.str]] = None,
    entrypoint: typing.Optional[typing.Sequence[builtins.str]] = None,
    working_directory: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3c71280e3aba0c9512a180cd9b287eb9fa61158e0b247676de51e6b48a0b58d3(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    assets: typing.Sequence[typing.Union[AssetConfig, typing.Dict[builtins.str, typing.Any]]],
    destination_bucket: _aws_cdk_aws_s3_ceddda9d.IBucket,
    output_source_directory: builtins.str,
    build_commands: typing.Optional[typing.Sequence[builtins.str]] = None,
    build_environment: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    destination_key_prefix: typing.Optional[builtins.str] = None,
    distribution: typing.Optional[_aws_cdk_aws_cloudfront_ceddda9d.IDistribution] = None,
    exclude_common_files: typing.Optional[builtins.bool] = None,
    nodejs_version: typing.Optional[jsii.Number] = None,
    output_env_file: typing.Optional[builtins.bool] = None,
    working_directory: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3ad4ac39ec4adf96af9bc19519711c6c5d0d566e989bcafec2dac62ce03d3294(
    *,
    assets: typing.Sequence[typing.Union[AssetConfig, typing.Dict[builtins.str, typing.Any]]],
    destination_bucket: _aws_cdk_aws_s3_ceddda9d.IBucket,
    output_source_directory: builtins.str,
    build_commands: typing.Optional[typing.Sequence[builtins.str]] = None,
    build_environment: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    destination_key_prefix: typing.Optional[builtins.str] = None,
    distribution: typing.Optional[_aws_cdk_aws_cloudfront_ceddda9d.IDistribution] = None,
    exclude_common_files: typing.Optional[builtins.bool] = None,
    nodejs_version: typing.Optional[jsii.Number] = None,
    output_env_file: typing.Optional[builtins.bool] = None,
    working_directory: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__96c9f98c6307010e55fc9821910e21e80021318519921a9cd9371c8e3551dc20(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    image_tag: builtins.str,
    repository: _aws_cdk_aws_ecr_ceddda9d.IRepository,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__379044f417588697cb394f0bbb2af9baa69f581f01fe14f37a5e9f01ea6c57f3(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    image_asset: _aws_cdk_aws_ecr_assets_ceddda9d.DockerImageAsset,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8ad6c57fd92a51686139131b933189975e9f3ea79f0e01e3cdb6be816eed7cb1(
    *,
    image_tag: builtins.str,
    repository: _aws_cdk_aws_ecr_ceddda9d.IRepository,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4c1647b890bfb5351778b6354dee86a5aaf1387660d9aedd6995955025b1dbda(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    input_image_tag: builtins.str,
    repository: _aws_cdk_aws_ecr_ceddda9d.IRepository,
    output_image_tag: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1c38bbcaa8fd085c8837fe0e2820457722cb3fd6a81f8aa9390ecd32dece8abc(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    image_asset: _aws_cdk_aws_ecr_assets_ceddda9d.DockerImageAsset,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5ed2883b1f7c70fc7b86e345c0f7b329f138abacd1ecb7a9b0ea4b72b7554928(
    *,
    input_image_tag: builtins.str,
    repository: _aws_cdk_aws_ecr_ceddda9d.IRepository,
    output_image_tag: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass
