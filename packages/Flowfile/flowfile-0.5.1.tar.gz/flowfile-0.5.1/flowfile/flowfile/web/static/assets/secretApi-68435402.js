import { a as axios } from "./index-5429bbf8.js";
const API_BASE_URL = "/secrets/secrets";
const fetchSecretsApi = async () => {
  try {
    const response = await axios.get(API_BASE_URL);
    return response.data;
  } catch (error) {
    console.error("API Error: Failed to load secrets:", error);
    throw error;
  }
};
const addSecretApi = async (secretData) => {
  var _a, _b;
  try {
    await axios.post(API_BASE_URL, secretData);
  } catch (error) {
    console.error("API Error: Failed to add secret:", error);
    const errorMsg = ((_b = (_a = error.response) == null ? void 0 : _a.data) == null ? void 0 : _b.detail) || "Failed to add secret";
    throw new Error(errorMsg);
  }
};
const getSecretValueApi = async (secretName) => {
  try {
    const response = await axios.get(
      `${API_BASE_URL}/${encodeURIComponent(secretName)}`
    );
    return response.data.value;
  } catch (error) {
    console.error("API Error: Failed to get secret value:", error);
    throw error;
  }
};
const deleteSecretApi = async (secretName) => {
  try {
    await axios.delete(`${API_BASE_URL}/${encodeURIComponent(secretName)}`);
  } catch (error) {
    console.error("API Error: Failed to delete secret:", error);
    throw error;
  }
};
export {
  addSecretApi as a,
  deleteSecretApi as d,
  fetchSecretsApi as f,
  getSecretValueApi as g
};
