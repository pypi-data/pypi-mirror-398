r'''
Documentation for this pattern can be found [here](https://github.com/awslabs/aws-solutions-constructs/blob/main/source/patterns/%40aws-solutions-constructs/aws-lambda-bedrockinferenceprofile/README.adoc)
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

import aws_cdk.aws_bedrock as _aws_cdk_aws_bedrock_ceddda9d
import aws_cdk.aws_ec2 as _aws_cdk_aws_ec2_ceddda9d
import aws_cdk.aws_lambda as _aws_cdk_aws_lambda_ceddda9d
import constructs as _constructs_77d1e7e8


class LambdaToBedrockinferenceprofile(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-solutions-constructs/aws-lambda-bedrockinferenceprofile.LambdaToBedrockinferenceprofile",
):
    '''
    :summary: The LambdaToBedrockinferenceprofile class.
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        bedrock_model_id: builtins.str,
        deploy_cross_region_profile: typing.Optional[builtins.bool] = None,
        deploy_vpc: typing.Optional[builtins.bool] = None,
        existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
        existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
        foundation_model_environment_variable_name: typing.Optional[builtins.str] = None,
        inference_profile_environment_variable_name: typing.Optional[builtins.str] = None,
        inference_profile_props: typing.Optional[typing.Union[_aws_cdk_aws_bedrock_ceddda9d.CfnApplicationInferenceProfileProps, typing.Dict[builtins.str, typing.Any]]] = None,
        lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
        vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param scope: - represents the scope for all the resources.
        :param id: - this is a a scope-unique id.
        :param bedrock_model_id: The foundation model to use with the inference profile. The construct will validate the model name, create the correct inference profile name based on the region and remind the developer in which regions the model must be available for this profile. Be certain that the account is granted access to the foundation model in all the regions covered by cross-region inference profile
        :param deploy_cross_region_profile: Whether to deploy a cross-region inference profile that will automatically distribute Invoke calls across multiple regions. Default: - true
        :param deploy_vpc: Whether to deploy a new VPC. Default: - false
        :param existing_lambda_obj: Optional - instance of an existing Lambda Function object, providing both this and ``lambdaFunctionProps`` will cause an error. Default: - None
        :param existing_vpc: An existing VPC for the construct to use (construct will NOT create a new VPC in this case).
        :param foundation_model_environment_variable_name: Optional Name for the Lambda function environment variable set to the Model name. Default: - BEDROCK_MODEL
        :param inference_profile_environment_variable_name: Optional Name for the Lambda function environment variable set to the inference profile arn. Default: - BEDROCK_PROFILE
        :param inference_profile_props: Properties to override constructs props values for the Inference Profile. The construct will populate inverenceProfileName - so don't override it unless you have an very good reason. The construct base IAM policies around the modelSource that it creates, so trying to send a modelSource in ths parameter will cause an error. This is where you set tags required for tracking inference calls.
        :param lambda_function_props: Optional - user provided props to override the default props for the Lambda function. Providing both this and ``existingLambdaObj`` is an error. Default: - Default properties are used.
        :param vpc_props: Properties to override default properties if deployVpc is true.

        :access: public
        :since: 0.8.0
        :summary: Constructs a new instance of the LambdaToSns class.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3f146eecba713ed1ed7bed25607c92b6cdce670262bf0c10ad465027e80d1370)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = LambdaToBedrockinferenceprofileProps(
            bedrock_model_id=bedrock_model_id,
            deploy_cross_region_profile=deploy_cross_region_profile,
            deploy_vpc=deploy_vpc,
            existing_lambda_obj=existing_lambda_obj,
            existing_vpc=existing_vpc,
            foundation_model_environment_variable_name=foundation_model_environment_variable_name,
            inference_profile_environment_variable_name=inference_profile_environment_variable_name,
            inference_profile_props=inference_profile_props,
            lambda_function_props=lambda_function_props,
            vpc_props=vpc_props,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property
    @jsii.member(jsii_name="inferenceProfile")
    def inference_profile(
        self,
    ) -> _aws_cdk_aws_bedrock_ceddda9d.CfnApplicationInferenceProfile:
        return typing.cast(_aws_cdk_aws_bedrock_ceddda9d.CfnApplicationInferenceProfile, jsii.get(self, "inferenceProfile"))

    @builtins.property
    @jsii.member(jsii_name="lambdaFunction")
    def lambda_function(self) -> _aws_cdk_aws_lambda_ceddda9d.Function:
        return typing.cast(_aws_cdk_aws_lambda_ceddda9d.Function, jsii.get(self, "lambdaFunction"))

    @builtins.property
    @jsii.member(jsii_name="vpc")
    def vpc(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc]:
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc], jsii.get(self, "vpc"))


@jsii.data_type(
    jsii_type="@aws-solutions-constructs/aws-lambda-bedrockinferenceprofile.LambdaToBedrockinferenceprofileProps",
    jsii_struct_bases=[],
    name_mapping={
        "bedrock_model_id": "bedrockModelId",
        "deploy_cross_region_profile": "deployCrossRegionProfile",
        "deploy_vpc": "deployVpc",
        "existing_lambda_obj": "existingLambdaObj",
        "existing_vpc": "existingVpc",
        "foundation_model_environment_variable_name": "foundationModelEnvironmentVariableName",
        "inference_profile_environment_variable_name": "inferenceProfileEnvironmentVariableName",
        "inference_profile_props": "inferenceProfileProps",
        "lambda_function_props": "lambdaFunctionProps",
        "vpc_props": "vpcProps",
    },
)
class LambdaToBedrockinferenceprofileProps:
    def __init__(
        self,
        *,
        bedrock_model_id: builtins.str,
        deploy_cross_region_profile: typing.Optional[builtins.bool] = None,
        deploy_vpc: typing.Optional[builtins.bool] = None,
        existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
        existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
        foundation_model_environment_variable_name: typing.Optional[builtins.str] = None,
        inference_profile_environment_variable_name: typing.Optional[builtins.str] = None,
        inference_profile_props: typing.Optional[typing.Union[_aws_cdk_aws_bedrock_ceddda9d.CfnApplicationInferenceProfileProps, typing.Dict[builtins.str, typing.Any]]] = None,
        lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
        vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param bedrock_model_id: The foundation model to use with the inference profile. The construct will validate the model name, create the correct inference profile name based on the region and remind the developer in which regions the model must be available for this profile. Be certain that the account is granted access to the foundation model in all the regions covered by cross-region inference profile
        :param deploy_cross_region_profile: Whether to deploy a cross-region inference profile that will automatically distribute Invoke calls across multiple regions. Default: - true
        :param deploy_vpc: Whether to deploy a new VPC. Default: - false
        :param existing_lambda_obj: Optional - instance of an existing Lambda Function object, providing both this and ``lambdaFunctionProps`` will cause an error. Default: - None
        :param existing_vpc: An existing VPC for the construct to use (construct will NOT create a new VPC in this case).
        :param foundation_model_environment_variable_name: Optional Name for the Lambda function environment variable set to the Model name. Default: - BEDROCK_MODEL
        :param inference_profile_environment_variable_name: Optional Name for the Lambda function environment variable set to the inference profile arn. Default: - BEDROCK_PROFILE
        :param inference_profile_props: Properties to override constructs props values for the Inference Profile. The construct will populate inverenceProfileName - so don't override it unless you have an very good reason. The construct base IAM policies around the modelSource that it creates, so trying to send a modelSource in ths parameter will cause an error. This is where you set tags required for tracking inference calls.
        :param lambda_function_props: Optional - user provided props to override the default props for the Lambda function. Providing both this and ``existingLambdaObj`` is an error. Default: - Default properties are used.
        :param vpc_props: Properties to override default properties if deployVpc is true.

        :summary: The properties for the LambdaToSns class.
        '''
        if isinstance(inference_profile_props, dict):
            inference_profile_props = _aws_cdk_aws_bedrock_ceddda9d.CfnApplicationInferenceProfileProps(**inference_profile_props)
        if isinstance(lambda_function_props, dict):
            lambda_function_props = _aws_cdk_aws_lambda_ceddda9d.FunctionProps(**lambda_function_props)
        if isinstance(vpc_props, dict):
            vpc_props = _aws_cdk_aws_ec2_ceddda9d.VpcProps(**vpc_props)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__dbd286561a19e8bd53f160f75f50f6ccc70ee89235d93c7e43431b10d35bd16c)
            check_type(argname="argument bedrock_model_id", value=bedrock_model_id, expected_type=type_hints["bedrock_model_id"])
            check_type(argname="argument deploy_cross_region_profile", value=deploy_cross_region_profile, expected_type=type_hints["deploy_cross_region_profile"])
            check_type(argname="argument deploy_vpc", value=deploy_vpc, expected_type=type_hints["deploy_vpc"])
            check_type(argname="argument existing_lambda_obj", value=existing_lambda_obj, expected_type=type_hints["existing_lambda_obj"])
            check_type(argname="argument existing_vpc", value=existing_vpc, expected_type=type_hints["existing_vpc"])
            check_type(argname="argument foundation_model_environment_variable_name", value=foundation_model_environment_variable_name, expected_type=type_hints["foundation_model_environment_variable_name"])
            check_type(argname="argument inference_profile_environment_variable_name", value=inference_profile_environment_variable_name, expected_type=type_hints["inference_profile_environment_variable_name"])
            check_type(argname="argument inference_profile_props", value=inference_profile_props, expected_type=type_hints["inference_profile_props"])
            check_type(argname="argument lambda_function_props", value=lambda_function_props, expected_type=type_hints["lambda_function_props"])
            check_type(argname="argument vpc_props", value=vpc_props, expected_type=type_hints["vpc_props"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "bedrock_model_id": bedrock_model_id,
        }
        if deploy_cross_region_profile is not None:
            self._values["deploy_cross_region_profile"] = deploy_cross_region_profile
        if deploy_vpc is not None:
            self._values["deploy_vpc"] = deploy_vpc
        if existing_lambda_obj is not None:
            self._values["existing_lambda_obj"] = existing_lambda_obj
        if existing_vpc is not None:
            self._values["existing_vpc"] = existing_vpc
        if foundation_model_environment_variable_name is not None:
            self._values["foundation_model_environment_variable_name"] = foundation_model_environment_variable_name
        if inference_profile_environment_variable_name is not None:
            self._values["inference_profile_environment_variable_name"] = inference_profile_environment_variable_name
        if inference_profile_props is not None:
            self._values["inference_profile_props"] = inference_profile_props
        if lambda_function_props is not None:
            self._values["lambda_function_props"] = lambda_function_props
        if vpc_props is not None:
            self._values["vpc_props"] = vpc_props

    @builtins.property
    def bedrock_model_id(self) -> builtins.str:
        '''The foundation model to use with the inference profile.

        The construct
        will validate the model name, create the correct inference profile name
        based on the region and remind the developer in which regions the model
        must be available for this profile. Be certain that the account is granted
        access to the foundation model in all the regions covered by cross-region
        inference profile
        '''
        result = self._values.get("bedrock_model_id")
        assert result is not None, "Required property 'bedrock_model_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def deploy_cross_region_profile(self) -> typing.Optional[builtins.bool]:
        '''Whether to deploy a cross-region inference profile that will automatically distribute Invoke calls across multiple regions.

        :default: - true
        '''
        result = self._values.get("deploy_cross_region_profile")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def deploy_vpc(self) -> typing.Optional[builtins.bool]:
        '''Whether to deploy a new VPC.

        :default: - false
        '''
        result = self._values.get("deploy_vpc")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def existing_lambda_obj(
        self,
    ) -> typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function]:
        '''Optional - instance of an existing Lambda Function object, providing both this and ``lambdaFunctionProps`` will cause an error.

        :default: - None
        '''
        result = self._values.get("existing_lambda_obj")
        return typing.cast(typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function], result)

    @builtins.property
    def existing_vpc(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc]:
        '''An existing VPC for the construct to use (construct will NOT create a new VPC in this case).'''
        result = self._values.get("existing_vpc")
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc], result)

    @builtins.property
    def foundation_model_environment_variable_name(
        self,
    ) -> typing.Optional[builtins.str]:
        '''Optional Name for the Lambda function environment variable set to the Model name.

        :default: - BEDROCK_MODEL
        '''
        result = self._values.get("foundation_model_environment_variable_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def inference_profile_environment_variable_name(
        self,
    ) -> typing.Optional[builtins.str]:
        '''Optional Name for the Lambda function environment variable set to the inference profile arn.

        :default: - BEDROCK_PROFILE
        '''
        result = self._values.get("inference_profile_environment_variable_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def inference_profile_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_bedrock_ceddda9d.CfnApplicationInferenceProfileProps]:
        '''Properties to override constructs props values for the Inference Profile.

        The construct will populate inverenceProfileName - so don't override it
        unless you have an very good reason.  The construct base IAM policies around
        the modelSource that it creates, so trying to send a modelSource in ths
        parameter will cause an error. This is where you set tags required for
        tracking inference calls.
        '''
        result = self._values.get("inference_profile_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_bedrock_ceddda9d.CfnApplicationInferenceProfileProps], result)

    @builtins.property
    def lambda_function_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_lambda_ceddda9d.FunctionProps]:
        '''Optional - user provided props to override the default props for the Lambda function.

        Providing both this and ``existingLambdaObj`` is an error.

        :default: - Default properties are used.
        '''
        result = self._values.get("lambda_function_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_lambda_ceddda9d.FunctionProps], result)

    @builtins.property
    def vpc_props(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.VpcProps]:
        '''Properties to override default properties if deployVpc is true.'''
        result = self._values.get("vpc_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.VpcProps], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "LambdaToBedrockinferenceprofileProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "LambdaToBedrockinferenceprofile",
    "LambdaToBedrockinferenceprofileProps",
]

publication.publish()

def _typecheckingstub__3f146eecba713ed1ed7bed25607c92b6cdce670262bf0c10ad465027e80d1370(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    bedrock_model_id: builtins.str,
    deploy_cross_region_profile: typing.Optional[builtins.bool] = None,
    deploy_vpc: typing.Optional[builtins.bool] = None,
    existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
    existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    foundation_model_environment_variable_name: typing.Optional[builtins.str] = None,
    inference_profile_environment_variable_name: typing.Optional[builtins.str] = None,
    inference_profile_props: typing.Optional[typing.Union[_aws_cdk_aws_bedrock_ceddda9d.CfnApplicationInferenceProfileProps, typing.Dict[builtins.str, typing.Any]]] = None,
    lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
    vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__dbd286561a19e8bd53f160f75f50f6ccc70ee89235d93c7e43431b10d35bd16c(
    *,
    bedrock_model_id: builtins.str,
    deploy_cross_region_profile: typing.Optional[builtins.bool] = None,
    deploy_vpc: typing.Optional[builtins.bool] = None,
    existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
    existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    foundation_model_environment_variable_name: typing.Optional[builtins.str] = None,
    inference_profile_environment_variable_name: typing.Optional[builtins.str] = None,
    inference_profile_props: typing.Optional[typing.Union[_aws_cdk_aws_bedrock_ceddda9d.CfnApplicationInferenceProfileProps, typing.Dict[builtins.str, typing.Any]]] = None,
    lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
    vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass
