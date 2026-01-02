r'''
# CDK Aspect Git Tagger

This is a CDK Aspect that will tag your CDK Stacks with the current git repo location for easier identification of
deployed stacks. Will create a `.git-url-tagger.json` file in the root of your project to store the git url.  This file
will be used to determine the git url for the stack.

### How to install

```shell
npm install @jjrawlins/cdk-git-tagger
```

or

```shell
yarn add @jjrawlins/cdk-git-tagger
```

### How to use

```python
import { GitUrlTagger } from '@jjrawlins/cdk-git-tagger';
import { App, Aspects, Stack, StackProps } from 'aws-cdk-lib';
import { Topic } from 'aws-cdk-lib/aws-sns';
import { Construct } from 'constructs';

export class MyStack extends Stack {
    constructor(scope: Construct, id: string, props: StackProps = {}) {
        super(scope, id, props);
        // define resources here...
        new Topic(this, 'MyTopic');
    }
}

const app = new App();

new MyStack(app, 'cdk-aspect-git-tagger-tester');
Aspects.of(app).add(new GitUrlTagger());
app.synth();
```

### Example Output

```json
{
  "Resources": {
    "MyTopic86869434": {
      "Type": "AWS::SNS::Topic",
      "Properties": {
        "Tags": [
          {
            "Key": "GitUrl",
            "Value": "https://github.com/jjrawlins/cdk-cool-construct.git"
          }
        ]
      }
    }
  }
}
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
import constructs as _constructs_77d1e7e8


@jsii.implements(_aws_cdk_ceddda9d.IAspect)
class GitUrlTagger(
    metaclass=jsii.JSIIMeta,
    jsii_type="@jjrawlins/cdk-git-tagger.GitUrlTagger",
):
    def __init__(
        self,
        *,
        normalize_url: typing.Optional[builtins.bool] = None,
        tag_name: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param normalize_url: A flag on whether to try to normalize the URL found in the git config If enabled, it will turn ssh urls into https urls. Default: true
        :param tag_name: The Tag key/name to use. Default: 'GitUrl'
        '''
        props = GitUrlTaggerProps(normalize_url=normalize_url, tag_name=tag_name)

        jsii.create(self.__class__, self, [props])

    @jsii.member(jsii_name="findGitDirectory")
    def find_git_directory(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.invoke(self, "findGitDirectory", []))

    @jsii.member(jsii_name="putGitUrlInFile")
    def put_git_url_in_file(self, git_url: builtins.str) -> None:
        '''
        :param git_url: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bfe8425e1e4c03cc1548c421d438d45256e3cac23249648206a5ac0f0b5965ad)
            check_type(argname="argument git_url", value=git_url, expected_type=type_hints["git_url"])
        return typing.cast(None, jsii.invoke(self, "putGitUrlInFile", [git_url]))

    @jsii.member(jsii_name="retrieveGitUrl")
    def retrieve_git_url(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.invoke(self, "retrieveGitUrl", []))

    @jsii.member(jsii_name="visit")
    def visit(self, construct: "_constructs_77d1e7e8.IConstruct") -> None:
        '''All aspects can visit an IConstruct.

        :param construct: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__71500cdbf403e21d08a6a265b3447941a8543c5d55a8f853464a69818b467aa0)
            check_type(argname="argument construct", value=construct, expected_type=type_hints["construct"])
        return typing.cast(None, jsii.invoke(self, "visit", [construct]))


@jsii.data_type(
    jsii_type="@jjrawlins/cdk-git-tagger.GitUrlTaggerProps",
    jsii_struct_bases=[],
    name_mapping={"normalize_url": "normalizeUrl", "tag_name": "tagName"},
)
class GitUrlTaggerProps:
    def __init__(
        self,
        *,
        normalize_url: typing.Optional[builtins.bool] = None,
        tag_name: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param normalize_url: A flag on whether to try to normalize the URL found in the git config If enabled, it will turn ssh urls into https urls. Default: true
        :param tag_name: The Tag key/name to use. Default: 'GitUrl'
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ad218a0e5bdc7467a18c7bea11c99cb2cb7e13be8df2331af6b48a54da39fe12)
            check_type(argname="argument normalize_url", value=normalize_url, expected_type=type_hints["normalize_url"])
            check_type(argname="argument tag_name", value=tag_name, expected_type=type_hints["tag_name"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if normalize_url is not None:
            self._values["normalize_url"] = normalize_url
        if tag_name is not None:
            self._values["tag_name"] = tag_name

    @builtins.property
    def normalize_url(self) -> typing.Optional[builtins.bool]:
        '''A flag on whether to try to normalize the URL found in the git config If enabled, it will turn ssh urls into https urls.

        :default: true
        '''
        result = self._values.get("normalize_url")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def tag_name(self) -> typing.Optional[builtins.str]:
        '''The Tag key/name to use.

        :default: 'GitUrl'
        '''
        result = self._values.get("tag_name")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "GitUrlTaggerProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "GitUrlTagger",
    "GitUrlTaggerProps",
]

publication.publish()

def _typecheckingstub__bfe8425e1e4c03cc1548c421d438d45256e3cac23249648206a5ac0f0b5965ad(
    git_url: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__71500cdbf403e21d08a6a265b3447941a8543c5d55a8f853464a69818b467aa0(
    construct: _constructs_77d1e7e8.IConstruct,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ad218a0e5bdc7467a18c7bea11c99cb2cb7e13be8df2331af6b48a54da39fe12(
    *,
    normalize_url: typing.Optional[builtins.bool] = None,
    tag_name: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass
