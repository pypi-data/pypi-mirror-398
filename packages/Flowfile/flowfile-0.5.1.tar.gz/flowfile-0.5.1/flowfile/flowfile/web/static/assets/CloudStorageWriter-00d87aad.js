import { d as defineComponent, r as ref, c as openBlock, e as createElementBlock, f as createVNode, w as withCtx, p as createBaseVNode, a8 as withDirectives, ak as vModelSelect, F as Fragment, q as renderList, t as toDisplayString, g as createTextVNode, i as createCommentVNode, a9 as vModelText, h as createBlock, u as unref, z as ElMessage, _ as _export_sfc } from "./index-5429bbf8.js";
import { C as CodeLoader } from "./vue-content-loader.es-2c8e608f.js";
import { u as useNodeStore } from "./vue-codemirror.esm-41b0e0d7.js";
import { f as fetchCloudStorageConnectionsInterfaces } from "./api-c1bad5ca.js";
import { G as GenericNodeSettings } from "./genericNodeSettings-4fe5f36b.js";
import "./designer-9633482a.js";
const createNodeCloudStorageWriter = (flowId, nodeId) => {
  const cloudStorageWriteSettings = {
    auth_mode: "aws-cli",
    // Default to local credentials
    connection_name: void 0,
    resource_path: "",
    write_mode: "overwrite",
    file_format: "parquet",
    // Parquet is a common, efficient default
    parquet_compression: "snappy",
    csv_delimiter: ",",
    csv_encoding: "utf8"
  };
  const nodeWriter = {
    flow_id: flowId,
    node_id: nodeId,
    pos_x: 0,
    pos_y: 0,
    cloud_storage_settings: cloudStorageWriteSettings,
    cache_results: false
  };
  return nodeWriter;
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
const _hoisted_11 = { class: "form-group" };
const _hoisted_12 = {
  key: 0,
  value: "append"
};
const _hoisted_13 = {
  key: 0,
  class: "format-options"
};
const _hoisted_14 = { class: "form-row" };
const _hoisted_15 = { class: "form-group half" };
const _hoisted_16 = { class: "form-group half" };
const _hoisted_17 = {
  key: 1,
  class: "format-options"
};
const _hoisted_18 = { class: "form-group" };
const _hoisted_19 = {
  key: 2,
  class: "info-box info-warn"
};
const _hoisted_20 = {
  key: 3,
  class: "info-box"
};
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "CloudStorageWriter",
  props: {
    nodeId: {}
  },
  setup(__props, { expose: __expose }) {
    const nodeStore = useNodeStore();
    const dataLoaded = ref(false);
    const nodeCloudStorageWriter = ref(null);
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
      if (nodeCloudStorageWriter.value) {
        const settings = nodeCloudStorageWriter.value.cloud_storage_settings;
        const format = settings.file_format;
        if (format !== "delta") {
          settings.write_mode = "overwrite";
        }
        if (format === "parquet" && !settings.parquet_compression) {
          settings.parquet_compression = "snappy";
        } else if (format === "csv" && !settings.csv_delimiter) {
          settings.csv_delimiter = ",";
          settings.csv_encoding = "utf8";
        }
        if (format !== "parquet") {
          settings.parquet_compression = "snappy";
        }
        if (format !== "csv") {
          settings.csv_delimiter = ";";
          settings.csv_encoding = "utf8-lossy";
        }
      }
    };
    const updateConnection = () => {
      if (nodeCloudStorageWriter.value) {
        if (!selectedConnection.value) {
          nodeCloudStorageWriter.value.cloud_storage_settings.auth_mode = "aws-cli";
          nodeCloudStorageWriter.value.cloud_storage_settings.connection_name = void 0;
        } else {
          nodeCloudStorageWriter.value.cloud_storage_settings.auth_mode = selectedConnection.value.authMethod;
          nodeCloudStorageWriter.value.cloud_storage_settings.connection_name = selectedConnection.value.connectionName;
        }
      }
    };
    const setConnectionOnConnectionName = async (connectionName) => {
      selectedConnection.value = connectionInterfaces.value.find((ci) => ci.connectionName === connectionName) || null;
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
          nodeCloudStorageWriter.value = hasValidSetup ? nodeData.setting_input : createNodeCloudStorageWriter(nodeStore.flow_id, nodeId);
          if ((_b = nodeCloudStorageWriter.value) == null ? void 0 : _b.cloud_storage_settings.connection_name) {
            await setConnectionOnConnectionName(
              nodeCloudStorageWriter.value.cloud_storage_settings.connection_name
            );
          } else {
            selectedConnection.value = null;
          }
        }
        dataLoaded.value = true;
      } catch (error) {
        console.error("Error loading node data:", error);
        ElMessage.error("Failed to load node settings.");
        dataLoaded.value = false;
      }
    };
    const pushNodeData = async () => {
      if (!nodeCloudStorageWriter.value || !nodeCloudStorageWriter.value.cloud_storage_settings) {
        return;
      }
      console.log(nodeCloudStorageWriter);
      nodeCloudStorageWriter.value.is_setup = true;
      nodeStore.updateSettings(nodeCloudStorageWriter);
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
      return dataLoaded.value && nodeCloudStorageWriter.value ? (openBlock(), createElementBlock("div", _hoisted_1, [
        createVNode(GenericNodeSettings, {
          modelValue: nodeCloudStorageWriter.value,
          "onUpdate:modelValue": _cache[7] || (_cache[7] = ($event) => nodeCloudStorageWriter.value = $event)
        }, {
          default: withCtx(() => [
            createBaseVNode("div", _hoisted_2, [
              createBaseVNode("div", _hoisted_3, [
                _cache[11] || (_cache[11] = createBaseVNode("label", { for: "connection-select" }, "Cloud Storage Connection", -1)),
                connectionsAreLoading.value ? (openBlock(), createElementBlock("div", _hoisted_4, _cache[8] || (_cache[8] = [
                  createBaseVNode("div", { class: "loading-spinner" }, null, -1),
                  createBaseVNode("p", null, "Loading connections...", -1)
                ]))) : (openBlock(), createElementBlock("div", _hoisted_5, [
                  withDirectives(createBaseVNode("select", {
                    id: "connection-select",
                    "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => selectedConnection.value = $event),
                    class: "form-control",
                    onChange: updateConnection
                  }, [
                    _cache[9] || (_cache[9] = createBaseVNode("option", { value: null }, "No connection (use local credentials)", -1)),
                    (openBlock(true), createElementBlock(Fragment, null, renderList(connectionInterfaces.value, (conn) => {
                      return openBlock(), createElementBlock("option", {
                        key: conn.connectionName,
                        value: conn
                      }, toDisplayString(conn.connectionName) + " (" + toDisplayString(getStorageTypeLabel(conn.storageType)) + " - " + toDisplayString(getAuthMethodLabel(conn.authMethod)) + ") ", 9, _hoisted_6);
                    }), 128))
                  ], 544), [
                    [vModelSelect, selectedConnection.value]
                  ]),
                  !nodeCloudStorageWriter.value.cloud_storage_settings.connection_name ? (openBlock(), createElementBlock("div", _hoisted_7, _cache[10] || (_cache[10] = [
                    createBaseVNode("i", { class: "fa-solid fa-info-circle" }, null, -1),
                    createTextVNode(" Will use local AWS CLI credentials or environment variables ")
                  ]))) : createCommentVNode("", true)
                ]))
              ])
            ]),
            createBaseVNode("div", _hoisted_8, [
              _cache[26] || (_cache[26] = createBaseVNode("h4", { class: "section-subtitle" }, "File Settings", -1)),
              createBaseVNode("div", _hoisted_9, [
                _cache[12] || (_cache[12] = createBaseVNode("label", { for: "file-path" }, "File Path", -1)),
                withDirectives(createBaseVNode("input", {
                  id: "file-path",
                  "onUpdate:modelValue": _cache[1] || (_cache[1] = ($event) => nodeCloudStorageWriter.value.cloud_storage_settings.resource_path = $event),
                  type: "text",
                  class: "form-control",
                  placeholder: "e.g., bucket-name/folder/file.parquet"
                }, null, 512), [
                  [vModelText, nodeCloudStorageWriter.value.cloud_storage_settings.resource_path]
                ])
              ]),
              createBaseVNode("div", _hoisted_10, [
                _cache[14] || (_cache[14] = createBaseVNode("label", { for: "file-format" }, "File Format", -1)),
                withDirectives(createBaseVNode("select", {
                  id: "file-format",
                  "onUpdate:modelValue": _cache[2] || (_cache[2] = ($event) => nodeCloudStorageWriter.value.cloud_storage_settings.file_format = $event),
                  class: "form-control",
                  onChange: handleFileFormatChange
                }, _cache[13] || (_cache[13] = [
                  createBaseVNode("option", { value: "parquet" }, "Parquet", -1),
                  createBaseVNode("option", { value: "csv" }, "CSV", -1),
                  createBaseVNode("option", { value: "json" }, "JSON", -1),
                  createBaseVNode("option", { value: "delta" }, "Delta Lake", -1)
                ]), 544), [
                  [vModelSelect, nodeCloudStorageWriter.value.cloud_storage_settings.file_format]
                ])
              ]),
              createBaseVNode("div", _hoisted_11, [
                _cache[16] || (_cache[16] = createBaseVNode("label", { for: "write-mode" }, "Write Mode", -1)),
                withDirectives(createBaseVNode("select", {
                  id: "write-mode",
                  "onUpdate:modelValue": _cache[3] || (_cache[3] = ($event) => nodeCloudStorageWriter.value.cloud_storage_settings.write_mode = $event),
                  class: "form-control"
                }, [
                  _cache[15] || (_cache[15] = createBaseVNode("option", { value: "overwrite" }, "Overwrite", -1)),
                  nodeCloudStorageWriter.value.cloud_storage_settings.file_format === "delta" ? (openBlock(), createElementBlock("option", _hoisted_12, " Append ")) : createCommentVNode("", true)
                ], 512), [
                  [vModelSelect, nodeCloudStorageWriter.value.cloud_storage_settings.write_mode]
                ])
              ]),
              nodeCloudStorageWriter.value.cloud_storage_settings.file_format === "csv" ? (openBlock(), createElementBlock("div", _hoisted_13, [
                _cache[20] || (_cache[20] = createBaseVNode("h5", { class: "subsection-title" }, "CSV Options", -1)),
                createBaseVNode("div", _hoisted_14, [
                  createBaseVNode("div", _hoisted_15, [
                    _cache[17] || (_cache[17] = createBaseVNode("label", { for: "csv-delimiter" }, "Delimiter", -1)),
                    withDirectives(createBaseVNode("input", {
                      id: "csv-delimiter",
                      "onUpdate:modelValue": _cache[4] || (_cache[4] = ($event) => nodeCloudStorageWriter.value.cloud_storage_settings.csv_delimiter = $event),
                      type: "text",
                      class: "form-control",
                      placeholder: ",",
                      maxlength: "1"
                    }, null, 512), [
                      [vModelText, nodeCloudStorageWriter.value.cloud_storage_settings.csv_delimiter]
                    ])
                  ]),
                  createBaseVNode("div", _hoisted_16, [
                    _cache[19] || (_cache[19] = createBaseVNode("label", { for: "csv-encoding" }, "Encoding", -1)),
                    withDirectives(createBaseVNode("select", {
                      id: "csv-encoding",
                      "onUpdate:modelValue": _cache[5] || (_cache[5] = ($event) => nodeCloudStorageWriter.value.cloud_storage_settings.csv_encoding = $event),
                      class: "form-control"
                    }, _cache[18] || (_cache[18] = [
                      createBaseVNode("option", { value: "utf8" }, "UTF-8", -1),
                      createBaseVNode("option", { value: "utf8-lossy" }, "UTF-8 Lossy", -1)
                    ]), 512), [
                      [vModelSelect, nodeCloudStorageWriter.value.cloud_storage_settings.csv_encoding]
                    ])
                  ])
                ])
              ])) : createCommentVNode("", true),
              nodeCloudStorageWriter.value.cloud_storage_settings.file_format === "parquet" ? (openBlock(), createElementBlock("div", _hoisted_17, [
                _cache[23] || (_cache[23] = createBaseVNode("h5", { class: "subsection-title" }, "Parquet Options", -1)),
                createBaseVNode("div", _hoisted_18, [
                  _cache[22] || (_cache[22] = createBaseVNode("label", { for: "parquet-compression" }, "Compression", -1)),
                  withDirectives(createBaseVNode("select", {
                    id: "parquet-compression",
                    "onUpdate:modelValue": _cache[6] || (_cache[6] = ($event) => nodeCloudStorageWriter.value.cloud_storage_settings.parquet_compression = $event),
                    class: "form-control"
                  }, _cache[21] || (_cache[21] = [
                    createBaseVNode("option", { value: "snappy" }, "Snappy", -1),
                    createBaseVNode("option", { value: "gzip" }, "Gzip", -1),
                    createBaseVNode("option", { value: "brotli" }, "Brotli", -1),
                    createBaseVNode("option", { value: "lz4" }, "LZ4", -1),
                    createBaseVNode("option", { value: "zstd" }, "Zstd", -1)
                  ]), 512), [
                    [vModelSelect, nodeCloudStorageWriter.value.cloud_storage_settings.parquet_compression]
                  ])
                ])
              ])) : createCommentVNode("", true),
              nodeCloudStorageWriter.value.cloud_storage_settings.write_mode === "overwrite" ? (openBlock(), createElementBlock("div", _hoisted_19, _cache[24] || (_cache[24] = [
                createBaseVNode("i", { class: "fa-solid fa-triangle-exclamation" }, null, -1),
                createBaseVNode("div", null, [
                  createBaseVNode("p", null, [
                    createBaseVNode("strong", null, "Overwrite mode:"),
                    createTextVNode(" If a file or data at the target path exists, it will be replaced. ")
                  ])
                ], -1)
              ]))) : createCommentVNode("", true),
              nodeCloudStorageWriter.value.cloud_storage_settings.write_mode === "append" ? (openBlock(), createElementBlock("div", _hoisted_20, _cache[25] || (_cache[25] = [
                createBaseVNode("i", { class: "fa-solid fa-info-circle" }, null, -1),
                createBaseVNode("div", null, [
                  createBaseVNode("p", null, [
                    createBaseVNode("strong", null, "Append mode:"),
                    createTextVNode(" New data will be added. The schema of the new data must match the existing data. ")
                  ])
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
const CloudStorageWriter_vue_vue_type_style_index_0_scoped_9ee12e64_lang = "";
const CloudStorageWriter = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-9ee12e64"]]);
export {
  CloudStorageWriter as default
};
