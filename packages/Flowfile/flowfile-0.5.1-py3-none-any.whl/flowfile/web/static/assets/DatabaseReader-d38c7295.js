import { d as defineComponent, r as ref, n as onMounted, b as resolveComponent, c as openBlock, e as createElementBlock, f as createVNode, w as withCtx, p as createBaseVNode, F as Fragment, q as renderList, h as createBlock, g as createTextVNode, t as toDisplayString, u as unref, ap as ElRadio, a8 as withDirectives, ak as vModelSelect, a9 as vModelText, i as createCommentVNode, a as axios, z as ElMessage, _ as _export_sfc } from "./index-5429bbf8.js";
import { C as CodeLoader } from "./vue-content-loader.es-2c8e608f.js";
import { u as useNodeStore } from "./vue-codemirror.esm-41b0e0d7.js";
import { f as fetchDatabaseConnectionsInterfaces } from "./api-cf1221f0.js";
import DatabaseConnectionSettings from "./DatabaseConnectionSettings-6f3e4ea5.js";
import SqlQueryComponent from "./SQLQueryComponent-df51adbe.js";
import { G as GenericNodeSettings } from "./genericNodeSettings-4fe5f36b.js";
import "./secretApi-68435402.js";
import "./designer-9633482a.js";
const createNodeDatabaseReader = (flowId, nodeId) => {
  const databaseSettings = {
    query_mode: "table",
    connection_mode: "reference",
    schema_name: void 0,
    table_name: void 0,
    query: "",
    database_connection: {
      database_type: "postgresql",
      username: "",
      password_ref: "",
      host: "localhost",
      port: 4322,
      database: "",
      url: void 0
    }
  };
  const nodePolarsCode = {
    flow_id: flowId,
    node_id: nodeId,
    pos_x: 0,
    pos_y: 0,
    database_settings: databaseSettings,
    cache_results: false,
    fields: []
  };
  return nodePolarsCode;
};
const _hoisted_1 = {
  key: 0,
  class: "db-container"
};
const _hoisted_2 = { class: "listbox-wrapper" };
const _hoisted_3 = { class: "form-group" };
const _hoisted_4 = { key: 0 };
const _hoisted_5 = { key: 1 };
const _hoisted_6 = { key: 0 };
const _hoisted_7 = { key: 1 };
const _hoisted_8 = ["value"];
const _hoisted_9 = { class: "listbox-wrapper" };
const _hoisted_10 = { class: "form-group" };
const _hoisted_11 = {
  key: 0,
  class: "query-section"
};
const _hoisted_12 = { class: "form-row" };
const _hoisted_13 = { class: "form-group half" };
const _hoisted_14 = { class: "form-group half" };
const _hoisted_15 = { class: "validation-section" };
const _hoisted_16 = ["disabled"];
const _hoisted_17 = {
  key: 0,
  class: "error-box"
};
const _hoisted_18 = { class: "error-message" };
const _hoisted_19 = {
  key: 1,
  class: "success-box"
};
const _hoisted_20 = { class: "success-message" };
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "DatabaseReader",
  props: {
    nodeId: {}
  },
  setup(__props, { expose: __expose }) {
    const connectionModeOptions = ref(["inline", "reference"]);
    const connectionInterfaces = ref([]);
    const nodeStore = useNodeStore();
    const nodeDatabaseReader = ref(null);
    const dataLoaded = ref(false);
    const validationError = ref(null);
    const validationSuccess = ref(null);
    const isValidating = ref(false);
    const connectionsAreLoading = ref(false);
    const handleQueryModeChange = (event) => {
      const target = event.target;
      const selectedMode = target.value;
      validationError.value = null;
      validationSuccess.value = null;
      if (nodeDatabaseReader.value) {
        nodeDatabaseReader.value.fields = [];
        if (selectedMode === "table") {
          nodeDatabaseReader.value.database_settings.query = "";
        } else {
          nodeDatabaseReader.value.database_settings.schema_name = void 0;
          nodeDatabaseReader.value.database_settings.table_name = void 0;
        }
      }
    };
    const loadNodeData = async (nodeId) => {
      var _a;
      try {
        const nodeData = await nodeStore.getNodeData(nodeId, false);
        if (nodeData) {
          const hasValidSetup = Boolean((_a = nodeData.setting_input) == null ? void 0 : _a.is_setup);
          nodeDatabaseReader.value = hasValidSetup ? nodeData.setting_input : createNodeDatabaseReader(nodeStore.flow_id, nodeId);
        }
        dataLoaded.value = true;
      } catch (error) {
        console.error("Error loading node data:", error);
        dataLoaded.value = false;
      }
    };
    const validateQuery = () => {
      var _a, _b;
      if (!((_b = (_a = nodeDatabaseReader.value) == null ? void 0 : _a.database_settings) == null ? void 0 : _b.query)) {
        validationError.value = "Please enter a SQL query";
        validationSuccess.value = null;
        return;
      }
      validateDatabaseSettings();
    };
    const resetFields = () => {
      if (nodeDatabaseReader.value) {
        nodeDatabaseReader.value.fields = [];
      }
    };
    const validateDatabaseSettings = async () => {
      var _a;
      if (!((_a = nodeDatabaseReader.value) == null ? void 0 : _a.database_settings)) {
        validationError.value = "Database settings are incomplete";
        validationSuccess.value = null;
        return;
      }
      validationError.value = null;
      validationSuccess.value = null;
      isValidating.value = true;
      resetFields();
      try {
        const response = await axios.post(
          "/validate_db_settings",
          nodeDatabaseReader.value.database_settings
        );
        validationSuccess.value = response.data.message || "Settings are valid";
      } catch (error) {
        if (error.response && error.response.data && error.response.data.detail) {
          validationError.value = error.response.data.detail;
        } else {
          validationError.value = "An error occurred during validation";
          console.error("Validation error:", error);
        }
      } finally {
        isValidating.value = false;
      }
    };
    const pushNodeData = async () => {
      if (!nodeDatabaseReader.value || !nodeDatabaseReader.value.database_settings) {
        return;
      }
      nodeDatabaseReader.value.is_setup = true;
      nodeStore.updateSettings(nodeDatabaseReader);
      dataLoaded.value = false;
    };
    const fetchConnections = async () => {
      connectionsAreLoading.value = true;
      try {
        connectionInterfaces.value = await fetchDatabaseConnectionsInterfaces();
      } catch (error) {
        console.error("Error fetching connections:", error);
        ElMessage.error("Failed to load database connections");
      } finally {
        connectionsAreLoading.value = false;
      }
    };
    onMounted(async () => {
      await fetchConnections();
    });
    __expose({
      loadNodeData,
      pushNodeData
    });
    return (_ctx, _cache) => {
      const _component_el_radio_group = resolveComponent("el-radio-group");
      return dataLoaded.value && nodeDatabaseReader.value ? (openBlock(), createElementBlock("div", _hoisted_1, [
        createVNode(GenericNodeSettings, {
          modelValue: nodeDatabaseReader.value,
          "onUpdate:modelValue": _cache[7] || (_cache[7] = ($event) => nodeDatabaseReader.value = $event)
        }, {
          default: withCtx(() => [
            createBaseVNode("div", _hoisted_2, [
              createBaseVNode("div", _hoisted_3, [
                _cache[8] || (_cache[8] = createBaseVNode("label", null, "Connection Mode", -1)),
                createVNode(_component_el_radio_group, {
                  modelValue: nodeDatabaseReader.value.database_settings.connection_mode,
                  "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => nodeDatabaseReader.value.database_settings.connection_mode = $event)
                }, {
                  default: withCtx(() => [
                    (openBlock(true), createElementBlock(Fragment, null, renderList(connectionModeOptions.value, (option) => {
                      return openBlock(), createBlock(unref(ElRadio), {
                        key: option,
                        label: option
                      }, {
                        default: withCtx(() => [
                          createTextVNode(toDisplayString(option), 1)
                        ]),
                        _: 2
                      }, 1032, ["label"]);
                    }), 128))
                  ]),
                  _: 1
                }, 8, ["modelValue"])
              ]),
              createBaseVNode("div", null, [
                nodeDatabaseReader.value.database_settings.connection_mode == "inline" && nodeDatabaseReader.value.database_settings.database_connection ? (openBlock(), createElementBlock("div", _hoisted_4, [
                  createVNode(DatabaseConnectionSettings, {
                    modelValue: nodeDatabaseReader.value.database_settings.database_connection,
                    "onUpdate:modelValue": _cache[1] || (_cache[1] = ($event) => nodeDatabaseReader.value.database_settings.database_connection = $event),
                    onChange: resetFields
                  }, null, 8, ["modelValue"])
                ])) : (openBlock(), createElementBlock("div", _hoisted_5, [
                  connectionsAreLoading.value ? (openBlock(), createElementBlock("div", _hoisted_6, _cache[9] || (_cache[9] = [
                    createBaseVNode("div", { class: "loading-spinner" }, null, -1),
                    createBaseVNode("p", null, "Loading connections...", -1)
                  ]))) : (openBlock(), createElementBlock("div", _hoisted_7, [
                    withDirectives(createBaseVNode("select", {
                      id: "connection-select",
                      "onUpdate:modelValue": _cache[2] || (_cache[2] = ($event) => nodeDatabaseReader.value.database_settings.database_connection_name = $event),
                      class: "form-control minimal-select"
                    }, [
                      _cache[10] || (_cache[10] = createBaseVNode("option", {
                        disabled: "",
                        value: ""
                      }, "Choose a connection", -1)),
                      (openBlock(true), createElementBlock(Fragment, null, renderList(connectionInterfaces.value, (conn) => {
                        return openBlock(), createElementBlock("option", {
                          key: conn.connectionName,
                          value: conn.connectionName
                        }, toDisplayString(conn.connectionName) + " (" + toDisplayString(conn.databaseType) + " - " + toDisplayString(conn.database) + ") ", 9, _hoisted_8);
                      }), 128))
                    ], 512), [
                      [vModelSelect, nodeDatabaseReader.value.database_settings.database_connection_name]
                    ])
                  ]))
                ]))
              ])
            ]),
            createBaseVNode("div", _hoisted_9, [
              createBaseVNode("div", _hoisted_10, [
                _cache[12] || (_cache[12] = createBaseVNode("label", { for: "query-mode" }, "Query Mode", -1)),
                withDirectives(createBaseVNode("select", {
                  id: "query-mode",
                  "onUpdate:modelValue": _cache[3] || (_cache[3] = ($event) => nodeDatabaseReader.value.database_settings.query_mode = $event),
                  class: "form-control",
                  onChange: handleQueryModeChange
                }, _cache[11] || (_cache[11] = [
                  createBaseVNode("option", { value: "table" }, "Table", -1),
                  createBaseVNode("option", { value: "query" }, "Query", -1)
                ]), 544), [
                  [vModelSelect, nodeDatabaseReader.value.database_settings.query_mode]
                ])
              ]),
              nodeDatabaseReader.value.database_settings.query_mode === "table" ? (openBlock(), createElementBlock("div", _hoisted_11, [
                _cache[15] || (_cache[15] = createBaseVNode("h4", { class: "section-subtitle" }, "Table Selection", -1)),
                createBaseVNode("div", _hoisted_12, [
                  createBaseVNode("div", _hoisted_13, [
                    _cache[13] || (_cache[13] = createBaseVNode("label", { for: "schema-name" }, "Schema", -1)),
                    withDirectives(createBaseVNode("input", {
                      id: "schema-name",
                      "onUpdate:modelValue": _cache[4] || (_cache[4] = ($event) => nodeDatabaseReader.value.database_settings.schema_name = $event),
                      type: "text",
                      class: "form-control",
                      placeholder: "Enter schema name",
                      onInput: resetFields
                    }, null, 544), [
                      [vModelText, nodeDatabaseReader.value.database_settings.schema_name]
                    ])
                  ]),
                  createBaseVNode("div", _hoisted_14, [
                    _cache[14] || (_cache[14] = createBaseVNode("label", { for: "table-name" }, "Table", -1)),
                    withDirectives(createBaseVNode("input", {
                      id: "table-name",
                      "onUpdate:modelValue": _cache[5] || (_cache[5] = ($event) => nodeDatabaseReader.value.database_settings.table_name = $event),
                      type: "text",
                      class: "form-control",
                      placeholder: "Enter table name",
                      onInput: resetFields
                    }, null, 544), [
                      [vModelText, nodeDatabaseReader.value.database_settings.table_name]
                    ])
                  ])
                ])
              ])) : createCommentVNode("", true),
              nodeDatabaseReader.value.database_settings.query_mode === "query" ? (openBlock(), createBlock(SqlQueryComponent, {
                key: 1,
                modelValue: nodeDatabaseReader.value.database_settings.query,
                "onUpdate:modelValue": _cache[6] || (_cache[6] = ($event) => nodeDatabaseReader.value.database_settings.query = $event),
                onValidate: validateQuery,
                onInput: resetFields
              }, null, 8, ["modelValue"])) : createCommentVNode("", true),
              createBaseVNode("div", _hoisted_15, [
                createBaseVNode("button", {
                  class: "validate-button",
                  disabled: isValidating.value,
                  onClick: validateDatabaseSettings
                }, toDisplayString(isValidating.value ? "Validating..." : "Validate Settings"), 9, _hoisted_16),
                validationError.value ? (openBlock(), createElementBlock("div", _hoisted_17, [
                  _cache[16] || (_cache[16] = createBaseVNode("div", { class: "error-title" }, "Validation Error", -1)),
                  createBaseVNode("div", _hoisted_18, toDisplayString(validationError.value), 1)
                ])) : createCommentVNode("", true),
                validationSuccess.value ? (openBlock(), createElementBlock("div", _hoisted_19, [
                  createBaseVNode("div", _hoisted_20, toDisplayString(validationSuccess.value), 1)
                ])) : createCommentVNode("", true)
              ])
            ])
          ]),
          _: 1
        }, 8, ["modelValue"])
      ])) : (openBlock(), createBlock(unref(CodeLoader), { key: 1 }));
    };
  }
});
const DatabaseReader_vue_vue_type_style_index_0_scoped_ae4d7dc5_lang = "";
const DatabaseReader = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-ae4d7dc5"]]);
export {
  DatabaseReader as default
};
