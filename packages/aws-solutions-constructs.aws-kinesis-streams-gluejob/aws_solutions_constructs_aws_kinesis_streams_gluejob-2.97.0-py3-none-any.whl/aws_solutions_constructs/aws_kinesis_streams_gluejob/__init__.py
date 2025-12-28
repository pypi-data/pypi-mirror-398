r'''
Documentation for this pattern can be found [here](https://github.com/awslabs/aws-solutions-constructs/blob/main/source/patterns/%40aws-solutions-constructs/aws-kinesisstreams-gluejob/README.adoc)
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

import aws_cdk.aws_cloudwatch as _aws_cdk_aws_cloudwatch_ceddda9d
import aws_cdk.aws_glue as _aws_cdk_aws_glue_ceddda9d
import aws_cdk.aws_iam as _aws_cdk_aws_iam_ceddda9d
import aws_cdk.aws_kinesis as _aws_cdk_aws_kinesis_ceddda9d
import aws_cdk.aws_s3 as _aws_cdk_aws_s3_ceddda9d
import aws_cdk.aws_s3_assets as _aws_cdk_aws_s3_assets_ceddda9d
import aws_solutions_constructs.core as _aws_solutions_constructs_core_ac4f6ab9
import constructs as _constructs_77d1e7e8


class KinesisstreamsToGluejob(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-solutions-constructs/aws-kinesisstreams-gluejob.KinesisstreamsToGluejob",
):
    '''
    :summary:

    = This construct either creates or uses the existing construct provided that can be deployed
    to perform streaming ETL operations using:

    - AWS Glue Database
    - AWS Glue Table
    - AWS Glue Job
    - Amazon Kinesis Data Streams
    - Amazon S3 Bucket (output datastore).
    The construct also configures the required role policies so that AWS Glue Job can read data from
    the streams, process it, and write to an output store.
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        create_cloud_watch_alarms: typing.Optional[builtins.bool] = None,
        database_props: typing.Optional[typing.Union[_aws_cdk_aws_glue_ceddda9d.CfnDatabaseProps, typing.Dict[builtins.str, typing.Any]]] = None,
        etl_code_asset: typing.Optional[_aws_cdk_aws_s3_assets_ceddda9d.Asset] = None,
        existing_database: typing.Optional[_aws_cdk_aws_glue_ceddda9d.CfnDatabase] = None,
        existing_glue_job: typing.Optional[_aws_cdk_aws_glue_ceddda9d.CfnJob] = None,
        existing_stream_obj: typing.Optional[_aws_cdk_aws_kinesis_ceddda9d.Stream] = None,
        existing_table: typing.Optional[_aws_cdk_aws_glue_ceddda9d.CfnTable] = None,
        field_schema: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_glue_ceddda9d.CfnTable.ColumnProperty, typing.Dict[builtins.str, typing.Any]]]] = None,
        glue_job_props: typing.Any = None,
        kinesis_stream_props: typing.Any = None,
        output_data_store: typing.Optional[typing.Union[_aws_solutions_constructs_core_ac4f6ab9.SinkDataStoreProps, typing.Dict[builtins.str, typing.Any]]] = None,
        table_props: typing.Optional[typing.Union[_aws_cdk_aws_glue_ceddda9d.CfnTableProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''Constructs a new instance of KinesisstreamsToGluejob.Based on the values set in the.

        :param scope: -
        :param id: -
        :param create_cloud_watch_alarms: Whether to create recommended CloudWatch alarms. Default: - Alarms are created
        :param database_props: The props for the Glue database that the construct should use to create. If
        :param etl_code_asset: Provide Asset instance corresponding to the code in the local filesystem, responsible for performing the Glue Job transformation. This property will override any S3 locations provided under glue.CfnJob.JobCommandProperty As of CDK V2, all ETL scripts sourced from local code should explicitly create an asset and provide that asset through this attribute. Default: - None
        :param existing_database: Glue Database for this construct. If not provided the construct will create a new Glue Database. The database is where the schema for the data in Kinesis Data Streams is stored
        :param existing_glue_job: Existing GlueJob configuration. If this property is provided, any properties provided through
        :param existing_stream_obj: Existing instance of Kineses Data Stream. If not set, it will create an instance
        :param existing_table: Glue Table for this construct, If not provided the construct will create a new Table in the database. This table should define the schema for the records in the Kinesis Data Streams. One of
        :param field_schema: Structure of the records in the Amazon Kinesis Data Streams. An example of such a definition is as below. Either Default: - None
        :param glue_job_props: User provides props to override the default props for Glue ETL Jobs. Providing both this and existingGlueJob will cause an error. This parameter is defined as ``any`` to not enforce passing the Glue Job role which is a mandatory parameter for CfnJobProps. If a role is not passed, the construct creates one for you and attaches the appropriate role policies The default props will set the Glue Version 2.0, with 2 Workers and WorkerType as G1.X. For details on defining a Glue Job, please refer the following link for documentation - https://docs.aws.amazon.com/glue/latest/webapi/API_Job.html Default: - None
        :param kinesis_stream_props: User provided props to override the default props for the Kinesis Stream. Default: - Default props are used
        :param output_data_store: The output data stores where the transformed data should be written. Current supported data stores include only S3, other potential stores may be added in the future.
        :param table_props: The table properties for the construct to create the table. One of

        :props: true
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__dbc920e59dce457bdbc70cc1e178d58faa598ae100339893765113d921508c81)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = KinesisstreamsToGluejobProps(
            create_cloud_watch_alarms=create_cloud_watch_alarms,
            database_props=database_props,
            etl_code_asset=etl_code_asset,
            existing_database=existing_database,
            existing_glue_job=existing_glue_job,
            existing_stream_obj=existing_stream_obj,
            existing_table=existing_table,
            field_schema=field_schema,
            glue_job_props=glue_job_props,
            kinesis_stream_props=kinesis_stream_props,
            output_data_store=output_data_store,
            table_props=table_props,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property
    @jsii.member(jsii_name="database")
    def database(self) -> _aws_cdk_aws_glue_ceddda9d.CfnDatabase:
        return typing.cast(_aws_cdk_aws_glue_ceddda9d.CfnDatabase, jsii.get(self, "database"))

    @builtins.property
    @jsii.member(jsii_name="glueJob")
    def glue_job(self) -> _aws_cdk_aws_glue_ceddda9d.CfnJob:
        return typing.cast(_aws_cdk_aws_glue_ceddda9d.CfnJob, jsii.get(self, "glueJob"))

    @builtins.property
    @jsii.member(jsii_name="glueJobRole")
    def glue_job_role(self) -> _aws_cdk_aws_iam_ceddda9d.IRole:
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.IRole, jsii.get(self, "glueJobRole"))

    @builtins.property
    @jsii.member(jsii_name="kinesisStream")
    def kinesis_stream(self) -> _aws_cdk_aws_kinesis_ceddda9d.Stream:
        return typing.cast(_aws_cdk_aws_kinesis_ceddda9d.Stream, jsii.get(self, "kinesisStream"))

    @builtins.property
    @jsii.member(jsii_name="table")
    def table(self) -> _aws_cdk_aws_glue_ceddda9d.CfnTable:
        return typing.cast(_aws_cdk_aws_glue_ceddda9d.CfnTable, jsii.get(self, "table"))

    @builtins.property
    @jsii.member(jsii_name="cloudwatchAlarms")
    def cloudwatch_alarms(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_cloudwatch_ceddda9d.Alarm]]:
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_cloudwatch_ceddda9d.Alarm]], jsii.get(self, "cloudwatchAlarms"))

    @builtins.property
    @jsii.member(jsii_name="outputBucket")
    def output_bucket(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_s3_ceddda9d.Bucket]]:
        '''This property is only set if the Glue Job is created by the construct.

        If an existing Glue Job
        configuration is supplied, the construct does not create an S3 bucket and hence the

        :outputBucket: property is undefined
        '''
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_s3_ceddda9d.Bucket]], jsii.get(self, "outputBucket"))


@jsii.data_type(
    jsii_type="@aws-solutions-constructs/aws-kinesisstreams-gluejob.KinesisstreamsToGluejobProps",
    jsii_struct_bases=[],
    name_mapping={
        "create_cloud_watch_alarms": "createCloudWatchAlarms",
        "database_props": "databaseProps",
        "etl_code_asset": "etlCodeAsset",
        "existing_database": "existingDatabase",
        "existing_glue_job": "existingGlueJob",
        "existing_stream_obj": "existingStreamObj",
        "existing_table": "existingTable",
        "field_schema": "fieldSchema",
        "glue_job_props": "glueJobProps",
        "kinesis_stream_props": "kinesisStreamProps",
        "output_data_store": "outputDataStore",
        "table_props": "tableProps",
    },
)
class KinesisstreamsToGluejobProps:
    def __init__(
        self,
        *,
        create_cloud_watch_alarms: typing.Optional[builtins.bool] = None,
        database_props: typing.Optional[typing.Union[_aws_cdk_aws_glue_ceddda9d.CfnDatabaseProps, typing.Dict[builtins.str, typing.Any]]] = None,
        etl_code_asset: typing.Optional[_aws_cdk_aws_s3_assets_ceddda9d.Asset] = None,
        existing_database: typing.Optional[_aws_cdk_aws_glue_ceddda9d.CfnDatabase] = None,
        existing_glue_job: typing.Optional[_aws_cdk_aws_glue_ceddda9d.CfnJob] = None,
        existing_stream_obj: typing.Optional[_aws_cdk_aws_kinesis_ceddda9d.Stream] = None,
        existing_table: typing.Optional[_aws_cdk_aws_glue_ceddda9d.CfnTable] = None,
        field_schema: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_glue_ceddda9d.CfnTable.ColumnProperty, typing.Dict[builtins.str, typing.Any]]]] = None,
        glue_job_props: typing.Any = None,
        kinesis_stream_props: typing.Any = None,
        output_data_store: typing.Optional[typing.Union[_aws_solutions_constructs_core_ac4f6ab9.SinkDataStoreProps, typing.Dict[builtins.str, typing.Any]]] = None,
        table_props: typing.Optional[typing.Union[_aws_cdk_aws_glue_ceddda9d.CfnTableProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param create_cloud_watch_alarms: Whether to create recommended CloudWatch alarms. Default: - Alarms are created
        :param database_props: The props for the Glue database that the construct should use to create. If
        :param etl_code_asset: Provide Asset instance corresponding to the code in the local filesystem, responsible for performing the Glue Job transformation. This property will override any S3 locations provided under glue.CfnJob.JobCommandProperty As of CDK V2, all ETL scripts sourced from local code should explicitly create an asset and provide that asset through this attribute. Default: - None
        :param existing_database: Glue Database for this construct. If not provided the construct will create a new Glue Database. The database is where the schema for the data in Kinesis Data Streams is stored
        :param existing_glue_job: Existing GlueJob configuration. If this property is provided, any properties provided through
        :param existing_stream_obj: Existing instance of Kineses Data Stream. If not set, it will create an instance
        :param existing_table: Glue Table for this construct, If not provided the construct will create a new Table in the database. This table should define the schema for the records in the Kinesis Data Streams. One of
        :param field_schema: Structure of the records in the Amazon Kinesis Data Streams. An example of such a definition is as below. Either Default: - None
        :param glue_job_props: User provides props to override the default props for Glue ETL Jobs. Providing both this and existingGlueJob will cause an error. This parameter is defined as ``any`` to not enforce passing the Glue Job role which is a mandatory parameter for CfnJobProps. If a role is not passed, the construct creates one for you and attaches the appropriate role policies The default props will set the Glue Version 2.0, with 2 Workers and WorkerType as G1.X. For details on defining a Glue Job, please refer the following link for documentation - https://docs.aws.amazon.com/glue/latest/webapi/API_Job.html Default: - None
        :param kinesis_stream_props: User provided props to override the default props for the Kinesis Stream. Default: - Default props are used
        :param output_data_store: The output data stores where the transformed data should be written. Current supported data stores include only S3, other potential stores may be added in the future.
        :param table_props: The table properties for the construct to create the table. One of
        '''
        if isinstance(database_props, dict):
            database_props = _aws_cdk_aws_glue_ceddda9d.CfnDatabaseProps(**database_props)
        if isinstance(output_data_store, dict):
            output_data_store = _aws_solutions_constructs_core_ac4f6ab9.SinkDataStoreProps(**output_data_store)
        if isinstance(table_props, dict):
            table_props = _aws_cdk_aws_glue_ceddda9d.CfnTableProps(**table_props)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__91a198df6179cded6ae11eff1b4291dd59c1d093700b7c0be1e7e553641b564e)
            check_type(argname="argument create_cloud_watch_alarms", value=create_cloud_watch_alarms, expected_type=type_hints["create_cloud_watch_alarms"])
            check_type(argname="argument database_props", value=database_props, expected_type=type_hints["database_props"])
            check_type(argname="argument etl_code_asset", value=etl_code_asset, expected_type=type_hints["etl_code_asset"])
            check_type(argname="argument existing_database", value=existing_database, expected_type=type_hints["existing_database"])
            check_type(argname="argument existing_glue_job", value=existing_glue_job, expected_type=type_hints["existing_glue_job"])
            check_type(argname="argument existing_stream_obj", value=existing_stream_obj, expected_type=type_hints["existing_stream_obj"])
            check_type(argname="argument existing_table", value=existing_table, expected_type=type_hints["existing_table"])
            check_type(argname="argument field_schema", value=field_schema, expected_type=type_hints["field_schema"])
            check_type(argname="argument glue_job_props", value=glue_job_props, expected_type=type_hints["glue_job_props"])
            check_type(argname="argument kinesis_stream_props", value=kinesis_stream_props, expected_type=type_hints["kinesis_stream_props"])
            check_type(argname="argument output_data_store", value=output_data_store, expected_type=type_hints["output_data_store"])
            check_type(argname="argument table_props", value=table_props, expected_type=type_hints["table_props"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if create_cloud_watch_alarms is not None:
            self._values["create_cloud_watch_alarms"] = create_cloud_watch_alarms
        if database_props is not None:
            self._values["database_props"] = database_props
        if etl_code_asset is not None:
            self._values["etl_code_asset"] = etl_code_asset
        if existing_database is not None:
            self._values["existing_database"] = existing_database
        if existing_glue_job is not None:
            self._values["existing_glue_job"] = existing_glue_job
        if existing_stream_obj is not None:
            self._values["existing_stream_obj"] = existing_stream_obj
        if existing_table is not None:
            self._values["existing_table"] = existing_table
        if field_schema is not None:
            self._values["field_schema"] = field_schema
        if glue_job_props is not None:
            self._values["glue_job_props"] = glue_job_props
        if kinesis_stream_props is not None:
            self._values["kinesis_stream_props"] = kinesis_stream_props
        if output_data_store is not None:
            self._values["output_data_store"] = output_data_store
        if table_props is not None:
            self._values["table_props"] = table_props

    @builtins.property
    def create_cloud_watch_alarms(self) -> typing.Optional[builtins.bool]:
        '''Whether to create recommended CloudWatch alarms.

        :default: - Alarms are created
        '''
        result = self._values.get("create_cloud_watch_alarms")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def database_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_glue_ceddda9d.CfnDatabaseProps]:
        '''The props for the Glue database that the construct should use to create.

        If

        :database: and
        :databaseprops:

        is provided, the
        construct will define a GlueDatabase resource.
        '''
        result = self._values.get("database_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_glue_ceddda9d.CfnDatabaseProps], result)

    @builtins.property
    def etl_code_asset(self) -> typing.Optional[_aws_cdk_aws_s3_assets_ceddda9d.Asset]:
        '''Provide Asset instance corresponding to the code in the local filesystem, responsible for performing the Glue Job transformation.

        This property will override any S3 locations provided
        under glue.CfnJob.JobCommandProperty

        As of CDK V2, all ETL scripts sourced from local code should explicitly create an asset and provide
        that asset through this attribute.

        :default: - None
        '''
        result = self._values.get("etl_code_asset")
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_assets_ceddda9d.Asset], result)

    @builtins.property
    def existing_database(
        self,
    ) -> typing.Optional[_aws_cdk_aws_glue_ceddda9d.CfnDatabase]:
        '''Glue Database for this construct.

        If not provided the construct will create a new Glue Database.
        The database is where the schema for the data in Kinesis Data Streams is stored
        '''
        result = self._values.get("existing_database")
        return typing.cast(typing.Optional[_aws_cdk_aws_glue_ceddda9d.CfnDatabase], result)

    @builtins.property
    def existing_glue_job(self) -> typing.Optional[_aws_cdk_aws_glue_ceddda9d.CfnJob]:
        '''Existing GlueJob configuration.

        If this property is provided, any properties provided through

        :KinesisstreamsToGluejobProps: .etlCodeAsset will take higher precedence and override the JobCommandProperty.scriptLocation
        :glueJobProps:

        is ignored.
        The ETL script can be provided either under glue.CfnJob.JobCommandProperty or set as an Asset instance under
        '''
        result = self._values.get("existing_glue_job")
        return typing.cast(typing.Optional[_aws_cdk_aws_glue_ceddda9d.CfnJob], result)

    @builtins.property
    def existing_stream_obj(
        self,
    ) -> typing.Optional[_aws_cdk_aws_kinesis_ceddda9d.Stream]:
        '''Existing instance of Kineses Data Stream.

        If not set, it will create an instance
        '''
        result = self._values.get("existing_stream_obj")
        return typing.cast(typing.Optional[_aws_cdk_aws_kinesis_ceddda9d.Stream], result)

    @builtins.property
    def existing_table(self) -> typing.Optional[_aws_cdk_aws_glue_ceddda9d.CfnTable]:
        '''Glue Table for this construct, If not provided the construct will create a new Table in the database.

        This table should define the schema for the records in the Kinesis Data Streams.
        One of

        :fieldSchema: is ignored
        :table: is provided,
        :tableprops: is provided then
        '''
        result = self._values.get("existing_table")
        return typing.cast(typing.Optional[_aws_cdk_aws_glue_ceddda9d.CfnTable], result)

    @builtins.property
    def field_schema(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_glue_ceddda9d.CfnTable.ColumnProperty]]:
        '''Structure of the records in the Amazon Kinesis Data Streams.

        An example of such a  definition is as below.
        Either

        :default: - None

        :fieldSchema:

        is ignored
        "FieldSchema": [{
        "name": "id",
        "type": "int",
        "comment": "Identifier for the record"
        }, {
        "name": "name",
        "type": "string",
        "comment": "The name of the record"
        }, {
        "name": "type",
        "type": "string",
        "comment": "The type of the record"
        }, {
        "name": "numericvalue",
        "type": "int",
        "comment": "Some value associated with the record"
        },
        :table: is provided then
        '''
        result = self._values.get("field_schema")
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_glue_ceddda9d.CfnTable.ColumnProperty]], result)

    @builtins.property
    def glue_job_props(self) -> typing.Any:
        '''User provides props to override the default props for Glue ETL Jobs.

        Providing both this and
        existingGlueJob will cause an error.

        This parameter is defined as ``any`` to not enforce passing the Glue Job role which is a mandatory parameter
        for CfnJobProps. If a role is not passed, the construct creates one for you and attaches the appropriate
        role policies

        The default props will set the Glue Version 2.0, with 2 Workers and WorkerType as G1.X. For details on
        defining a Glue Job, please refer the following link for documentation - https://docs.aws.amazon.com/glue/latest/webapi/API_Job.html

        :default: - None
        '''
        result = self._values.get("glue_job_props")
        return typing.cast(typing.Any, result)

    @builtins.property
    def kinesis_stream_props(self) -> typing.Any:
        '''User provided props to override the default props for the Kinesis Stream.

        :default: - Default props are used
        '''
        result = self._values.get("kinesis_stream_props")
        return typing.cast(typing.Any, result)

    @builtins.property
    def output_data_store(
        self,
    ) -> typing.Optional[_aws_solutions_constructs_core_ac4f6ab9.SinkDataStoreProps]:
        '''The output data stores where the transformed data should be written.

        Current supported data stores
        include only S3, other potential stores may be added in the future.
        '''
        result = self._values.get("output_data_store")
        return typing.cast(typing.Optional[_aws_solutions_constructs_core_ac4f6ab9.SinkDataStoreProps], result)

    @builtins.property
    def table_props(self) -> typing.Optional[_aws_cdk_aws_glue_ceddda9d.CfnTableProps]:
        '''The table properties for the construct to create the table.

        One of

        :fieldSchema: is ignored
        :table: is provided,
        :tableprops: is provided then
        '''
        result = self._values.get("table_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_glue_ceddda9d.CfnTableProps], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "KinesisstreamsToGluejobProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "KinesisstreamsToGluejob",
    "KinesisstreamsToGluejobProps",
]

publication.publish()

def _typecheckingstub__dbc920e59dce457bdbc70cc1e178d58faa598ae100339893765113d921508c81(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    create_cloud_watch_alarms: typing.Optional[builtins.bool] = None,
    database_props: typing.Optional[typing.Union[_aws_cdk_aws_glue_ceddda9d.CfnDatabaseProps, typing.Dict[builtins.str, typing.Any]]] = None,
    etl_code_asset: typing.Optional[_aws_cdk_aws_s3_assets_ceddda9d.Asset] = None,
    existing_database: typing.Optional[_aws_cdk_aws_glue_ceddda9d.CfnDatabase] = None,
    existing_glue_job: typing.Optional[_aws_cdk_aws_glue_ceddda9d.CfnJob] = None,
    existing_stream_obj: typing.Optional[_aws_cdk_aws_kinesis_ceddda9d.Stream] = None,
    existing_table: typing.Optional[_aws_cdk_aws_glue_ceddda9d.CfnTable] = None,
    field_schema: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_glue_ceddda9d.CfnTable.ColumnProperty, typing.Dict[builtins.str, typing.Any]]]] = None,
    glue_job_props: typing.Any = None,
    kinesis_stream_props: typing.Any = None,
    output_data_store: typing.Optional[typing.Union[_aws_solutions_constructs_core_ac4f6ab9.SinkDataStoreProps, typing.Dict[builtins.str, typing.Any]]] = None,
    table_props: typing.Optional[typing.Union[_aws_cdk_aws_glue_ceddda9d.CfnTableProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__91a198df6179cded6ae11eff1b4291dd59c1d093700b7c0be1e7e553641b564e(
    *,
    create_cloud_watch_alarms: typing.Optional[builtins.bool] = None,
    database_props: typing.Optional[typing.Union[_aws_cdk_aws_glue_ceddda9d.CfnDatabaseProps, typing.Dict[builtins.str, typing.Any]]] = None,
    etl_code_asset: typing.Optional[_aws_cdk_aws_s3_assets_ceddda9d.Asset] = None,
    existing_database: typing.Optional[_aws_cdk_aws_glue_ceddda9d.CfnDatabase] = None,
    existing_glue_job: typing.Optional[_aws_cdk_aws_glue_ceddda9d.CfnJob] = None,
    existing_stream_obj: typing.Optional[_aws_cdk_aws_kinesis_ceddda9d.Stream] = None,
    existing_table: typing.Optional[_aws_cdk_aws_glue_ceddda9d.CfnTable] = None,
    field_schema: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_glue_ceddda9d.CfnTable.ColumnProperty, typing.Dict[builtins.str, typing.Any]]]] = None,
    glue_job_props: typing.Any = None,
    kinesis_stream_props: typing.Any = None,
    output_data_store: typing.Optional[typing.Union[_aws_solutions_constructs_core_ac4f6ab9.SinkDataStoreProps, typing.Dict[builtins.str, typing.Any]]] = None,
    table_props: typing.Optional[typing.Union[_aws_cdk_aws_glue_ceddda9d.CfnTableProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass
