import { d as defineComponent, r as ref, n as onMounted, b as resolveComponent, c as openBlock, e as createElementBlock, f as createVNode, w as withCtx, p as createBaseVNode, F as Fragment, q as renderList, h as createBlock, g as createTextVNode, t as toDisplayString, u as unref, ap as ElRadio, a8 as withDirectives, ak as vModelSelect, a9 as vModelText, z as ElMessage, _ as _export_sfc } from "./index-5429bbf8.js";
import { C as CodeLoader } from "./vue-content-loader.es-2c8e608f.js";
import { u as useNodeStore } from "./vue-codemirror.esm-41b0e0d7.js";
import { f as fetchDatabaseConnectionsInterfaces } from "./api-cf1221f0.js";
import DatabaseConnectionSettings from "./DatabaseConnectionSettings-6f3e4ea5.js";
import { G as GenericNodeSettings } from "./genericNodeSettings-4fe5f36b.js";
import "./secretApi-68435402.js";
import "./designer-9633482a.js";
const createNodeDatabaseWriter = (flowId, nodeId) => {
  const databaseWriteSettings = {
    if_exists: "replace",
    connection_mode: "reference",
    schema_name: void 0,
    table_name: void 0,
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
    database_write_settings: databaseWriteSettings,
    cache_results: false
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
const _hoisted_10 = { class: "form-row" };
const _hoisted_11 = { class: "form-group half" };
const _hoisted_12 = { class: "form-group half" };
const _hoisted_13 = { class: "listbox-wrapper" };
const _hoisted_14 = { class: "form-group" };
const _hoisted_15 = ["value"];
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "DatabaseWriter",
  props: {
    nodeId: {}
  },
  setup(__props, { expose: __expose }) {
    const props = __props;
    const nodeStore = useNodeStore();
    const connectionModeOptions = ref(["inline", "reference"]);
    const ifExistActions = ref(["append", "replace", "fail"]);
    const connectionInterfaces = ref([]);
    const nodeData = ref(null);
    const dataLoaded = ref(false);
    const connectionsAreLoading = ref(false);
    const loadNodeData = async (nodeId) => {
      var _a;
      try {
        const fetchedNodeData = await nodeStore.getNodeData(nodeId, false);
        if (fetchedNodeData) {
          const hasValidSetup = Boolean((_a = fetchedNodeData.setting_input) == null ? void 0 : _a.is_setup);
          nodeData.value = hasValidSetup ? fetchedNodeData.setting_input : createNodeDatabaseWriter(nodeStore.flow_id, nodeId);
        }
        dataLoaded.value = true;
      } catch (error) {
        console.error("Error loading node data:", error);
        dataLoaded.value = false;
        ElMessage.error("Failed to load node data");
      }
    };
    const resetFields = () => {
    };
    const pushNodeData = async () => {
      if (!nodeData.value) {
        return;
      }
      nodeData.value.is_setup = true;
      try {
        await nodeStore.updateSettings(nodeData);
      } catch (error) {
        console.error("Error saving node data:", error);
        ElMessage.error("Failed to save node settings");
      }
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
      await loadNodeData(props.nodeId);
    });
    __expose({
      loadNodeData,
      pushNodeData
    });
    return (_ctx, _cache) => {
      const _component_el_radio_group = resolveComponent("el-radio-group");
      return dataLoaded.value && nodeData.value ? (openBlock(), createElementBlock("div", _hoisted_1, [
        createVNode(GenericNodeSettings, {
          modelValue: nodeData.value,
          "onUpdate:modelValue": _cache[6] || (_cache[6] = ($event) => nodeData.value = $event)
        }, {
          default: withCtx(() => [
            createBaseVNode("div", _hoisted_2, [
              createBaseVNode("div", _hoisted_3, [
                _cache[7] || (_cache[7] = createBaseVNode("label", null, "Connection Mode", -1)),
                createVNode(_component_el_radio_group, {
                  modelValue: nodeData.value.database_write_settings.connection_mode,
                  "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => nodeData.value.database_write_settings.connection_mode = $event)
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
                nodeData.value.database_write_settings.connection_mode === "inline" && nodeData.value.database_write_settings.database_connection ? (openBlock(), createElementBlock("div", _hoisted_4, [
                  createVNode(DatabaseConnectionSettings, {
                    modelValue: nodeData.value.database_write_settings.database_connection,
                    "onUpdate:modelValue": _cache[1] || (_cache[1] = ($event) => nodeData.value.database_write_settings.database_connection = $event),
                    onChange: resetFields
                  }, null, 8, ["modelValue"])
                ])) : (openBlock(), createElementBlock("div", _hoisted_5, [
                  connectionsAreLoading.value ? (openBlock(), createElementBlock("div", _hoisted_6, _cache[8] || (_cache[8] = [
                    createBaseVNode("div", { class: "loading-spinner" }, null, -1),
                    createBaseVNode("p", null, "Loading connections...", -1)
                  ]))) : (openBlock(), createElementBlock("div", _hoisted_7, [
                    withDirectives(createBaseVNode("select", {
                      id: "connection-select",
                      "onUpdate:modelValue": _cache[2] || (_cache[2] = ($event) => nodeData.value.database_write_settings.database_connection_name = $event),
                      class: "form-control minimal-select"
                    }, [
                      _cache[9] || (_cache[9] = createBaseVNode("option", {
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
                      [vModelSelect, nodeData.value.database_write_settings.database_connection_name]
                    ])
                  ]))
                ]))
              ])
            ]),
            createBaseVNode("div", _hoisted_9, [
              _cache[12] || (_cache[12] = createBaseVNode("h4", { class: "section-subtitle" }, "Table Settings", -1)),
              createBaseVNode("div", _hoisted_10, [
                createBaseVNode("div", _hoisted_11, [
                  _cache[10] || (_cache[10] = createBaseVNode("label", { for: "schema-name" }, "Schema", -1)),
                  withDirectives(createBaseVNode("input", {
                    id: "schema-name",
                    "onUpdate:modelValue": _cache[3] || (_cache[3] = ($event) => nodeData.value.database_write_settings.schema_name = $event),
                    type: "text",
                    class: "form-control",
                    placeholder: "Enter schema name"
                  }, null, 512), [
                    [vModelText, nodeData.value.database_write_settings.schema_name]
                  ])
                ]),
                createBaseVNode("div", _hoisted_12, [
                  _cache[11] || (_cache[11] = createBaseVNode("label", { for: "table-name" }, "Table", -1)),
                  withDirectives(createBaseVNode("input", {
                    id: "table-name",
                    "onUpdate:modelValue": _cache[4] || (_cache[4] = ($event) => nodeData.value.database_write_settings.table_name = $event),
                    type: "text",
                    class: "form-control",
                    placeholder: "Enter table name"
                  }, null, 512), [
                    [vModelText, nodeData.value.database_write_settings.table_name]
                  ])
                ])
              ])
            ]),
            createBaseVNode("div", _hoisted_13, [
              createBaseVNode("div", _hoisted_14, [
                _cache[13] || (_cache[13] = createBaseVNode("label", { for: "if-exists-action" }, "If Table Exists", -1)),
                withDirectives(createBaseVNode("select", {
                  id: "if-exists-action",
                  "onUpdate:modelValue": _cache[5] || (_cache[5] = ($event) => nodeData.value.database_write_settings.if_exists = $event),
                  class: "form-control"
                }, [
                  (openBlock(true), createElementBlock(Fragment, null, renderList(ifExistActions.value, (action) => {
                    return openBlock(), createElementBlock("option", {
                      key: action,
                      value: action
                    }, toDisplayString(action.charAt(0).toUpperCase() + action.slice(1)), 9, _hoisted_15);
                  }), 128))
                ], 512), [
                  [vModelSelect, nodeData.value.database_write_settings.if_exists]
                ])
              ]),
              _cache[14] || (_cache[14] = createBaseVNode("div", { class: "form-group" }, [
                createBaseVNode("p", { class: "option-description" }, [
                  createBaseVNode("strong", null, "Append:"),
                  createTextVNode(" Add new data to existing table"),
                  createBaseVNode("br"),
                  createBaseVNode("strong", null, "Replace:"),
                  createTextVNode(" Delete existing table and create new one"),
                  createBaseVNode("br"),
                  createBaseVNode("strong", null, "Fail:"),
                  createTextVNode(" Abort if table already exists ")
                ])
              ], -1))
            ])
          ]),
          _: 1
        }, 8, ["modelValue"])
      ])) : (openBlock(), createBlock(unref(CodeLoader), { key: 1 }));
    };
  }
});
const DatabaseWriter_vue_vue_type_style_index_0_scoped_90b52fee_lang = "";
const DatabaseWriter = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-90b52fee"]]);
export {
  DatabaseWriter as default
};
