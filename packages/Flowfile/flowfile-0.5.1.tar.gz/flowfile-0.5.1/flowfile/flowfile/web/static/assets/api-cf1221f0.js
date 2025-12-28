import { a as axios } from "./index-5429bbf8.js";
const API_BASE_URL = "/db_connection_lib";
const toPythonFormat = (connection) => {
  return {
    connection_name: connection.connectionName,
    database_type: connection.databaseType,
    username: connection.username,
    password: connection.password,
    host: connection.host,
    port: connection.port,
    database: connection.database,
    ssl_enabled: connection.sslEnabled,
    url: connection.url
  };
};
const fetchDatabaseConnectionsInterfaces = async () => {
  try {
    const response = await axios.get(API_BASE_URL);
    return response.data.map(convertConnectionInterfacePytoTs);
  } catch (error) {
    console.error("API Error: Failed to load database connections:", error);
    throw error;
  }
};
const convertConnectionInterfacePytoTs = (pythonConnectionInterface) => {
  return {
    username: pythonConnectionInterface.username,
    connectionName: pythonConnectionInterface.connection_name,
    databaseType: pythonConnectionInterface.database_type,
    host: pythonConnectionInterface.host,
    port: pythonConnectionInterface.port,
    sslEnabled: pythonConnectionInterface.ssl_enabled,
    url: pythonConnectionInterface.url,
    database: pythonConnectionInterface.database
  };
};
const createDatabaseConnectionApi = async (connectionData) => {
  var _a, _b;
  try {
    const pythonFormattedData = toPythonFormat(connectionData);
    await axios.post(API_BASE_URL, pythonFormattedData);
  } catch (error) {
    console.error("API Error: Failed to create database connection:", error);
    const errorMsg = ((_b = (_a = error.response) == null ? void 0 : _a.data) == null ? void 0 : _b.detail) || "Failed to create database connection";
    throw new Error(errorMsg);
  }
};
const deleteDatabaseConnectionApi = async (connectionName) => {
  try {
    await axios.delete(`${API_BASE_URL}?connection_name=${encodeURIComponent(connectionName)}`);
  } catch (error) {
    console.error("API Error: Failed to delete database connection:", error);
    throw error;
  }
};
export {
  createDatabaseConnectionApi as c,
  deleteDatabaseConnectionApi as d,
  fetchDatabaseConnectionsInterfaces as f
};
