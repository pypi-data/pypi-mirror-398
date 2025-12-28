import { r as ref, d as defineComponent, c as openBlock, e as createElementBlock, f as createVNode, w as withCtx, h as createBlock, u as unref } from "./index-5429bbf8.js";
import { C as CodeLoader } from "./vue-content-loader.es-2c8e608f.js";
import { u as useNodeStore } from "./vue-codemirror.esm-41b0e0d7.js";
import { s as selectDynamic } from "./selectDynamic-92e25ee3.js";
import { G as GenericNodeSettings } from "./genericNodeSettings-4fe5f36b.js";
import "./UnavailableFields-a03f512c.js";
import "./designer-9633482a.js";
const createSelectInput = (column_name, data_type = void 0, position = void 0, original_position = void 0) => {
  const selectInput = {
    old_name: column_name,
    new_name: column_name,
    data_type,
    keep: true,
    join_key: false,
    is_altered: false,
    data_type_change: false,
    is_available: true,
    position: position ?? 0,
    original_position: original_position ?? 0
  };
  return selectInput;
};
const updateNodeSelect = (nodeTable, nodeSelectRef) => {
  if (!(nodeTable == null ? void 0 : nodeTable.table_schema) || !nodeSelectRef.value)
    return;
  const existingInputMap = /* @__PURE__ */ new Map();
  nodeSelectRef.value.select_input.forEach((input) => {
    existingInputMap.set(input.old_name, input);
  });
  nodeTable.table_schema.forEach((schema, index) => {
    var _a;
    const existingInput = existingInputMap.get(schema.name);
    if (existingInput) {
      if (!existingInput.is_altered) {
        existingInput.data_type = schema.data_type;
      }
      if (!existingInput.original_position) {
        existingInput.original_position = index;
      }
    } else {
      const newInput = createSelectInput(schema.name, schema.data_type, index, index);
      (_a = nodeSelectRef.value) == null ? void 0 : _a.select_input.push(newInput);
      existingInputMap.set(schema.name, newInput);
    }
  });
};
const createNodeSelect = (flowId = -1, nodeId = -1, pos_x = 0, pos_y = 0, cache_input = false, keep_missing = false) => {
  const selectInputData = [];
  const nodeSelectRef = ref({
    flow_id: flowId,
    node_id: nodeId,
    pos_x,
    pos_y,
    cache_input,
    keep_missing,
    select_input: selectInputData,
    cache_results: false,
    sorted_by: "none"
  });
  return nodeSelectRef;
};
const _hoisted_1 = {
  key: 0,
  class: "listbox-wrapper"
};
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "Select",
  setup(__props, { expose: __expose }) {
    const keepMissing = ref(false);
    const nodeStore = useNodeStore();
    const nodeSelect = ref(createNodeSelect().value);
    const dataLoaded = ref(false);
    const loadNodeData = async (nodeId) => {
      const result = await nodeStore.getNodeData(nodeId, false);
      if (result) {
        const main_input = result.main_input;
        try {
          if (result.setting_input && main_input && result.setting_input.is_setup) {
            nodeSelect.value = result.setting_input;
            keepMissing.value = nodeSelect.value.keep_missing;
            updateNodeSelect(main_input, nodeSelect);
          } else {
            throw new Error("Setting input not available");
          }
        } catch (error) {
          if (main_input && nodeSelect.value) {
            nodeSelect.value = createNodeSelect(nodeStore.flow_id, nodeStore.node_id).value;
            nodeSelect.value.depending_on_id = main_input.node_id;
            nodeSelect.value.flow_id = nodeStore.flow_id;
            nodeSelect.value.node_id = nodeStore.node_id;
            nodeSelect.value.keep_missing = keepMissing.value;
            updateNodeSelect(main_input, nodeSelect);
          }
        }
      }
      dataLoaded.value = true;
    };
    const pushNodeData = async () => {
      nodeSelect.value.select_input.sort((a, b) => a.position - b.position);
      const originalData = nodeStore.getCurrentNodeData();
      const newColumnSettings = nodeSelect.value.select_input;
      nodeSelect.value.keep_missing = keepMissing.value;
      if (originalData) {
        newColumnSettings.forEach((newColumnSetting, index) => {
          var _a, _b;
          let original_index = (_a = originalData.main_input) == null ? void 0 : _a.table_schema.findIndex(
            (column) => column.name === newColumnSetting.old_name
          );
          let original_object = index !== -1 ? (_b = originalData.main_input) == null ? void 0 : _b.table_schema[index] : void 0;
          if (original_object) {
            newColumnSetting.is_altered = (original_object == null ? void 0 : original_object.data_type) !== newColumnSetting.data_type;
            newColumnSetting.data_type_change = newColumnSetting.is_altered;
            newColumnSetting.position = index;
            newColumnSetting.original_position = original_index || index;
          }
        });
      }
      await nodeStore.updateSettings(nodeSelect);
    };
    const updateSelectInputsHandler = (updatedInputs) => {
      nodeSelect.value.select_input = updatedInputs;
    };
    __expose({
      loadNodeData,
      pushNodeData
    });
    return (_ctx, _cache) => {
      return dataLoaded.value ? (openBlock(), createElementBlock("div", _hoisted_1, [
        createVNode(GenericNodeSettings, {
          modelValue: nodeSelect.value,
          "onUpdate:modelValue": _cache[1] || (_cache[1] = ($event) => nodeSelect.value = $event)
        }, {
          default: withCtx(() => [
            createVNode(selectDynamic, {
              sortedBy: nodeSelect.value.sorted_by,
              "onUpdate:sortedBy": _cache[0] || (_cache[0] = ($event) => nodeSelect.value.sorted_by = $event),
              "select-inputs": nodeSelect.value.select_input,
              "show-keep-option": true,
              "show-data-type": true,
              "show-new-columns": true,
              "show-old-columns": true,
              "show-headers": true,
              "show-title": false,
              "show-data": true,
              title: "Select data",
              onUpdateSelectInputs: updateSelectInputsHandler
            }, null, 8, ["sortedBy", "select-inputs"])
          ]),
          _: 1
        }, 8, ["modelValue"])
      ])) : (openBlock(), createBlock(unref(CodeLoader), { key: 1 }));
    };
  }
});
export {
  _sfc_main as default
};
