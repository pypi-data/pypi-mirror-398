import { a as axios } from "./index-5429bbf8.js";
const API_BASE_URL = "/cloud_connections";
const toPythonFormat = (connection) => {
  return {
    storage_type: connection.storageType,
    auth_method: connection.authMethod,
    connection_name: connection.connectionName,
    // AWS S3
    aws_region: connection.awsRegion,
    aws_access_key_id: connection.awsAccessKeyId,
    aws_secret_access_key: connection.awsSecretAccessKey,
    aws_role_arn: connection.awsRoleArn,
    aws_allow_unsafe_html: connection.awsAllowUnsafeHtml,
    // Azure ADLS
    azure_account_name: connection.azureAccountName,
    azure_account_key: connection.azureAccountKey,
    azure_tenant_id: connection.azureTenantId,
    azure_client_id: connection.azureClientId,
    azure_client_secret: connection.azureClientSecret,
    // Common
    endpoint_url: connection.endpointUrl,
    verify_ssl: connection.verifySsl
  };
};
const fetchCloudStorageConnectionsInterfaces = async () => {
  try {
    const response = await axios.get(
      API_BASE_URL + "/cloud_connections"
    );
    return response.data.map(convertConnectionInterfacePytoTs);
  } catch (error) {
    console.error("API Error: Failed to load cloud storage connections:", error);
    throw error;
  }
};
const convertConnectionInterfacePytoTs = (pythonConnectionInterface) => {
  return {
    storageType: pythonConnectionInterface.storage_type,
    authMethod: pythonConnectionInterface.auth_method,
    connectionName: pythonConnectionInterface.connection_name,
    // AWS S3
    awsRegion: pythonConnectionInterface.aws_region,
    awsAccessKeyId: pythonConnectionInterface.aws_access_key_id,
    awsRoleArn: pythonConnectionInterface.aws_role_arn,
    awsAllowUnsafeHtml: pythonConnectionInterface.aws_allow_unsafe_html,
    // Azure ADLS
    azureAccountName: pythonConnectionInterface.azure_account_name,
    azureTenantId: pythonConnectionInterface.azure_tenant_id,
    azureClientId: pythonConnectionInterface.azure_client_id,
    // Common
    endpointUrl: pythonConnectionInterface.endpoint_url,
    verifySsl: pythonConnectionInterface.verify_ssl
  };
};
const createCloudStorageConnectionApi = async (connectionData) => {
  var _a, _b;
  try {
    const pythonFormattedData = toPythonFormat(connectionData);
    await axios.post(API_BASE_URL + "/cloud_connection", pythonFormattedData);
  } catch (error) {
    console.error("API Error: Failed to create cloud storage connection:", error);
    const errorMsg = ((_b = (_a = error.response) == null ? void 0 : _a.data) == null ? void 0 : _b.detail) || "Failed to create cloud storage connection";
    throw new Error(errorMsg);
  }
};
const deleteCloudStorageConnectionApi = async (connectionName) => {
  try {
    await axios.delete(
      `${API_BASE_URL}/cloud_connection?connection_name=${encodeURIComponent(connectionName)}`
    );
  } catch (error) {
    console.error("API Error: Failed to delete cloud storage connection:", error);
    throw error;
  }
};
export {
  createCloudStorageConnectionApi as c,
  deleteCloudStorageConnectionApi as d,
  fetchCloudStorageConnectionsInterfaces as f
};
