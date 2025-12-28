import { d as defineComponent, r as ref, c as openBlock, e as createElementBlock, f as createVNode, w as withCtx, p as createBaseVNode, a8 as withDirectives, ak as vModelSelect, F as Fragment, q as renderList, t as toDisplayString, g as createTextVNode, i as createCommentVNode, a9 as vModelText, am as vModelCheckbox, h as createBlock, u as unref, z as ElMessage, _ as _export_sfc } from "./index-5429bbf8.js";
import { C as CodeLoader } from "./vue-content-loader.es-2c8e608f.js";
import { u as useNodeStore } from "./vue-codemirror.esm-41b0e0d7.js";
import { f as fetchCloudStorageConnectionsInterfaces } from "./api-c1bad5ca.js";
import { G as GenericNodeSettings } from "./genericNodeSettings-4fe5f36b.js";
import "./designer-9633482a.js";
const createNodeCloudStorageReader = (flowId, nodeId) => {
  const cloudStorageReadSettings = {
    auth_mode: "aws-cli",
    scan_mode: "directory",
    resource_path: "",
    file_format: void 0,
    csv_has_header: false,
    csv_encoding: "utf8",
    delta_version: void 0
  };
  const nodePolarsCode = {
    flow_id: flowId,
    node_id: nodeId,
    pos_x: 0,
    pos_y: 0,
    cloud_storage_settings: cloudStorageReadSettings,
    cache_results: false,
    fields: []
  };
  return nodePolarsCode;
};
const _hoisted_1 = {
  key: 0,
  class: "cloud-storage-container"
};
const _hoisted_2 = { class: "listbox-wrapper" };
const _hoisted_3 = { class: "form-group" };
const _hoisted_4 = {
  key: 0,
  class: "loading-state"
};
const _hoisted_5 = { key: 1 };
const _hoisted_6 = ["value"];
const _hoisted_7 = {
  key: 0,
  class: "helper-text"
};
const _hoisted_8 = { class: "listbox-wrapper" };
const _hoisted_9 = { class: "form-group" };
const _hoisted_10 = { class: "form-group" };
const _hoisted_11 = {
  key: 0,
  class: "form-group"
};
const _hoisted_12 = {
  key: 1,
  class: "format-options"
};
const _hoisted_13 = { class: "form-group" };
const _hoisted_14 = { class: "checkbox-container" };
const _hoisted_15 = { class: "form-row" };
const _hoisted_16 = { class: "form-group half" };
const _hoisted_17 = { class: "form-group half" };
const _hoisted_18 = {
  key: 2,
  class: "format-options"
};
const _hoisted_19 = { class: "form-group" };
const _hoisted_20 = {
  key: 3,
  class: "info-box"
};
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "CloudStorageReader",
  props: {
    nodeId: {}
  },
  setup(__props, { expose: __expose }) {
    const nodeStore = useNodeStore();
    const dataLoaded = ref(false);
    const nodeCloudStorageReader = ref(null);
    const connectionInterfaces = ref([]);
    const connectionsAreLoading = ref(false);
    const selectedConnection = ref(null);
    const getStorageTypeLabel = (storageType) => {
      switch (storageType) {
        case "s3":
          return "AWS S3";
        case "adls":
          return "Azure ADLS";
        case "gcs":
          return "Google Cloud Storage";
        default:
          return storageType.toUpperCase();
      }
    };
    const getAuthMethodLabel = (authMethod) => {
      switch (authMethod) {
        case "access_key":
          return "Access Key";
        case "iam_role":
          return "IAM Role";
        case "service_principal":
          return "Service Principal";
        case "managed_identity":
          return "Managed Identity";
        case "sas_token":
          return "SAS Token";
        case "aws-cli":
          return "AWS CLI";
        case "auto":
          return "Auto";
        default:
          return authMethod;
      }
    };
    const handleFileFormatChange = () => {
      resetFields();
      if (nodeCloudStorageReader.value) {
        const format = nodeCloudStorageReader.value.cloud_storage_settings.file_format;
        if (format === "csv") {
          if (nodeCloudStorageReader.value.cloud_storage_settings.csv_has_header === void 0) {
            nodeCloudStorageReader.value.cloud_storage_settings.csv_has_header = true;
          }
          if (!nodeCloudStorageReader.value.cloud_storage_settings.csv_delimiter) {
            nodeCloudStorageReader.value.cloud_storage_settings.csv_delimiter = ",";
          }
          if (!nodeCloudStorageReader.value.cloud_storage_settings.csv_encoding) {
            nodeCloudStorageReader.value.cloud_storage_settings.csv_encoding = "utf8";
          }
        } else {
          nodeCloudStorageReader.value.cloud_storage_settings.csv_has_header = void 0;
          nodeCloudStorageReader.value.cloud_storage_settings.csv_delimiter = void 0;
          nodeCloudStorageReader.value.cloud_storage_settings.csv_encoding = void 0;
        }
        if (format !== "delta") {
          nodeCloudStorageReader.value.cloud_storage_settings.delta_version = void 0;
        }
      }
    };
    const resetFields = () => {
      if (nodeCloudStorageReader.value) {
        nodeCloudStorageReader.value.fields = [];
        if (!selectedConnection.value) {
          nodeCloudStorageReader.value.cloud_storage_settings.auth_mode = "aws-cli";
          nodeCloudStorageReader.value.cloud_storage_settings.connection_name = void 0;
        } else {
          nodeCloudStorageReader.value.cloud_storage_settings.auth_mode = selectedConnection.value.authMethod;
          nodeCloudStorageReader.value.cloud_storage_settings.connection_name = selectedConnection.value.connectionName;
        }
      }
    };
    const setConnectionOnConnectionName = async (connectionName) => {
      selectedConnection.value = connectionInterfaces.value.find(
        (connectionInterface) => connectionInterface.connectionName === connectionName
        // Use '===' for strict equality
      ) || null;
    };
    const loadNodeData = async (nodeId) => {
      var _a, _b;
      try {
        const [nodeData] = await Promise.all([
          nodeStore.getNodeData(nodeId, false),
          fetchConnections()
        ]);
        if (nodeData) {
          const hasValidSetup = Boolean((_a = nodeData.setting_input) == null ? void 0 : _a.is_setup);
          nodeCloudStorageReader.value = hasValidSetup ? nodeData.setting_input : createNodeCloudStorageReader(nodeStore.flow_id, nodeId);
          if ((_b = nodeCloudStorageReader.value) == null ? void 0 : _b.cloud_storage_settings.connection_name) {
            await setConnectionOnConnectionName(
              nodeCloudStorageReader.value.cloud_storage_settings.connection_name
            );
          } else {
            selectedConnection.value = null;
          }
        }
        dataLoaded.value = true;
      } catch (error) {
        console.error("Error loading node data:", error);
        dataLoaded.value = false;
      }
    };
    const pushNodeData = async () => {
      if (!nodeCloudStorageReader.value || !nodeCloudStorageReader.value.cloud_storage_settings) {
        console.log("Returning without pushing");
        return;
      }
      nodeCloudStorageReader.value.is_setup = true;
      nodeStore.updateSettings(nodeCloudStorageReader);
      dataLoaded.value = false;
    };
    const fetchConnections = async () => {
      connectionsAreLoading.value = true;
      try {
        connectionInterfaces.value = await fetchCloudStorageConnectionsInterfaces();
      } catch (error) {
        console.error("Error fetching connections:", error);
        ElMessage.error("Failed to load cloud storage connections");
      } finally {
        connectionsAreLoading.value = false;
      }
    };
    __expose({
      loadNodeData,
      pushNodeData
    });
    return (_ctx, _cache) => {
      return dataLoaded.value && nodeCloudStorageReader.value ? (openBlock(), createElementBlock("div", _hoisted_1, [
        createVNode(GenericNodeSettings, {
          modelValue: nodeCloudStorageReader.value,
          "onUpdate:modelValue": _cache[8] || (_cache[8] = ($event) => nodeCloudStorageReader.value = $event)
        }, {
          default: withCtx(() => [
            createBaseVNode("div", _hoisted_2, [
              createBaseVNode("div", _hoisted_3, [
                _cache[12] || (_cache[12] = createBaseVNode("label", { for: "connection-select" }, "Cloud Storage Connection", -1)),
                connectionsAreLoading.value ? (openBlock(), createElementBlock("div", _hoisted_4, _cache[9] || (_cache[9] = [
                  createBaseVNode("div", { class: "loading-spinner" }, null, -1),
                  createBaseVNode("p", null, "Loading connections...", -1)
                ]))) : (openBlock(), createElementBlock("div", _hoisted_5, [
                  withDirectives(createBaseVNode("select", {
                    id: "connection-select",
                    "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => selectedConnection.value = $event),
                    class: "form-control minimal-select",
                    onChange: resetFields
                  }, [
                    _cache[10] || (_cache[10] = createBaseVNode("option", { value: null }, "No connection (use local credentials)", -1)),
                    (openBlock(true), createElementBlock(Fragment, null, renderList(connectionInterfaces.value, (conn) => {
                      return openBlock(), createElementBlock("option", {
                        key: conn.connectionName,
                        value: conn
                      }, toDisplayString(conn.connectionName) + " (" + toDisplayString(getStorageTypeLabel(conn.storageType)) + " - " + toDisplayString(getAuthMethodLabel(conn.authMethod)) + ") ", 9, _hoisted_6);
                    }), 128))
                  ], 544), [
                    [vModelSelect, selectedConnection.value]
                  ]),
                  !nodeCloudStorageReader.value.cloud_storage_settings.connection_name ? (openBlock(), createElementBlock("div", _hoisted_7, _cache[11] || (_cache[11] = [
                    createBaseVNode("i", { class: "fa-solid fa-info-circle" }, null, -1),
                    createTextVNode(" Will use local AWS CLI credentials or environment variables ")
                  ]))) : createCommentVNode("", true)
                ]))
              ])
            ]),
            createBaseVNode("div", _hoisted_8, [
              _cache[26] || (_cache[26] = createBaseVNode("h4", { class: "section-subtitle" }, "File Settings", -1)),
              createBaseVNode("div", _hoisted_9, [
                _cache[13] || (_cache[13] = createBaseVNode("label", { for: "file-path" }, "File Path", -1)),
                withDirectives(createBaseVNode("input", {
                  id: "file-path",
                  "onUpdate:modelValue": _cache[1] || (_cache[1] = ($event) => nodeCloudStorageReader.value.cloud_storage_settings.resource_path = $event),
                  type: "text",
                  class: "form-control",
                  placeholder: "e.g., bucket-name/folder/file.csv or bucket-name/folder/",
                  onInput: resetFields
                }, null, 544), [
                  [vModelText, nodeCloudStorageReader.value.cloud_storage_settings.resource_path]
                ])
              ]),
              createBaseVNode("div", _hoisted_10, [
                _cache[15] || (_cache[15] = createBaseVNode("label", { for: "file-format" }, "File Format", -1)),
                withDirectives(createBaseVNode("select", {
                  id: "file-format",
                  "onUpdate:modelValue": _cache[2] || (_cache[2] = ($event) => nodeCloudStorageReader.value.cloud_storage_settings.file_format = $event),
                  class: "form-control",
                  onChange: handleFileFormatChange
                }, _cache[14] || (_cache[14] = [
                  createBaseVNode("option", { value: "csv" }, "CSV", -1),
                  createBaseVNode("option", { value: "parquet" }, "Parquet", -1),
                  createBaseVNode("option", { value: "json" }, "JSON", -1),
                  createBaseVNode("option", { value: "delta" }, "Delta Lake", -1)
                ]), 544), [
                  [vModelSelect, nodeCloudStorageReader.value.cloud_storage_settings.file_format]
                ])
              ]),
              nodeCloudStorageReader.value.cloud_storage_settings.file_format !== "delta" ? (openBlock(), createElementBlock("div", _hoisted_11, [
                _cache[17] || (_cache[17] = createBaseVNode("label", { for: "scan-mode" }, "Scan Mode", -1)),
                withDirectives(createBaseVNode("select", {
                  id: "scan-mode",
                  "onUpdate:modelValue": _cache[3] || (_cache[3] = ($event) => nodeCloudStorageReader.value.cloud_storage_settings.scan_mode = $event),
                  class: "form-control"
                }, _cache[16] || (_cache[16] = [
                  createBaseVNode("option", { value: "single_file" }, "Single File", -1),
                  createBaseVNode("option", { value: "directory" }, "Directory", -1)
                ]), 512), [
                  [vModelSelect, nodeCloudStorageReader.value.cloud_storage_settings.scan_mode]
                ])
              ])) : createCommentVNode("", true),
              nodeCloudStorageReader.value.cloud_storage_settings.file_format === "csv" ? (openBlock(), createElementBlock("div", _hoisted_12, [
                _cache[22] || (_cache[22] = createBaseVNode("h5", { class: "subsection-title" }, "CSV Options", -1)),
                createBaseVNode("div", _hoisted_13, [
                  createBaseVNode("div", _hoisted_14, [
                    withDirectives(createBaseVNode("input", {
                      id: "csv-has-header",
                      "onUpdate:modelValue": _cache[4] || (_cache[4] = ($event) => nodeCloudStorageReader.value.cloud_storage_settings.csv_has_header = $event),
                      type: "checkbox",
                      class: "checkbox-input"
                    }, null, 512), [
                      [vModelCheckbox, nodeCloudStorageReader.value.cloud_storage_settings.csv_has_header]
                    ]),
                    _cache[18] || (_cache[18] = createBaseVNode("label", {
                      for: "csv-has-header",
                      class: "checkbox-label"
                    }, "First row contains headers", -1))
                  ])
                ]),
                createBaseVNode("div", _hoisted_15, [
                  createBaseVNode("div", _hoisted_16, [
                    _cache[19] || (_cache[19] = createBaseVNode("label", { for: "csv-delimiter" }, "Delimiter", -1)),
                    withDirectives(createBaseVNode("input", {
                      id: "csv-delimiter",
                      "onUpdate:modelValue": _cache[5] || (_cache[5] = ($event) => nodeCloudStorageReader.value.cloud_storage_settings.csv_delimiter = $event),
                      type: "text",
                      class: "form-control",
                      placeholder: ",",
                      maxlength: "1"
                    }, null, 512), [
                      [vModelText, nodeCloudStorageReader.value.cloud_storage_settings.csv_delimiter]
                    ])
                  ]),
                  createBaseVNode("div", _hoisted_17, [
                    _cache[21] || (_cache[21] = createBaseVNode("label", { for: "csv-encoding" }, "Encoding", -1)),
                    withDirectives(createBaseVNode("select", {
                      id: "csv-encoding",
                      "onUpdate:modelValue": _cache[6] || (_cache[6] = ($event) => nodeCloudStorageReader.value.cloud_storage_settings.csv_encoding = $event),
                      class: "form-control"
                    }, _cache[20] || (_cache[20] = [
                      createBaseVNode("option", { value: "utf8" }, "UTF-8", -1),
                      createBaseVNode("option", { value: "utf8-lossy" }, "UTF-8 Lossy", -1)
                    ]), 512), [
                      [vModelSelect, nodeCloudStorageReader.value.cloud_storage_settings.csv_encoding]
                    ])
                  ])
                ])
              ])) : createCommentVNode("", true),
              nodeCloudStorageReader.value.cloud_storage_settings.file_format === "delta" ? (openBlock(), createElementBlock("div", _hoisted_18, [
                _cache[24] || (_cache[24] = createBaseVNode("h5", { class: "subsection-title" }, "Delta Lake Options", -1)),
                createBaseVNode("div", _hoisted_19, [
                  _cache[23] || (_cache[23] = createBaseVNode("label", { for: "delta-version" }, "Version (optional)", -1)),
                  withDirectives(createBaseVNode("input", {
                    id: "delta-version",
                    "onUpdate:modelValue": _cache[7] || (_cache[7] = ($event) => nodeCloudStorageReader.value.cloud_storage_settings.delta_version = $event),
                    type: "number",
                    class: "form-control",
                    placeholder: "Latest version",
                    min: "0"
                  }, null, 512), [
                    [
                      vModelText,
                      nodeCloudStorageReader.value.cloud_storage_settings.delta_version,
                      void 0,
                      { number: true }
                    ]
                  ])
                ])
              ])) : createCommentVNode("", true),
              nodeCloudStorageReader.value.cloud_storage_settings.scan_mode === "directory" ? (openBlock(), createElementBlock("div", _hoisted_20, _cache[25] || (_cache[25] = [
                createBaseVNode("i", { class: "fa-solid fa-info-circle" }, null, -1),
                createBaseVNode("div", null, [
                  createBaseVNode("p", null, " Directory scan will read all files matching the selected format in the specified path. ")
                ], -1)
              ]))) : createCommentVNode("", true)
            ])
          ]),
          _: 1
        }, 8, ["modelValue"])
      ])) : (openBlock(), createBlock(unref(CodeLoader), { key: 1 }));
    };
  }
});
const CloudStorageReader_vue_vue_type_style_index_0_scoped_8f1c7f30_lang = "";
const CloudStorageReader = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-8f1c7f30"]]);
export {
  CloudStorageReader as default
};
