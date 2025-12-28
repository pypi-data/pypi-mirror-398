import { a as axios, d as defineComponent, r as ref, c as openBlock, e as createElementBlock, p as createBaseVNode, g as createTextVNode, t as toDisplayString, f as createVNode, w as withCtx, F as Fragment, q as renderList, a8 as withDirectives, af as vShow, i as createCommentVNode, h as createBlock, _ as _export_sfc } from "./index-5429bbf8.js";
import { u as useNodeStore } from "./vue-codemirror.esm-41b0e0d7.js";
import { G as GenericNodeSettings } from "./genericNodeSettings-4fe5f36b.js";
import { _ as _sfc_main$3 } from "./MultiSelect.vue_vue_type_script_setup_true_lang-b0e538c2.js";
import { _ as _sfc_main$5 } from "./ToggleSwitch.vue_vue_type_script_setup_true_lang-38478c20.js";
import { _ as _sfc_main$1 } from "./TextInput.vue_vue_type_script_setup_true_lang-5896c375.js";
import { _ as _sfc_main$2 } from "./NumericInput.vue_vue_type_script_setup_true_lang-e0edeccc.js";
import SliderInput from "./SliderInput-7cb93e62.js";
import { _ as _sfc_main$4 } from "./SingleSelect.vue_vue_type_script_setup_true_lang-33e3ff9b.js";
import ColumnSelector from "./ColumnSelector-4685e75d.js";
import "./designer-9633482a.js";
async function getCustomNodeSchema(flowId, nodeId) {
  const response = await axios.get(
    `/user_defined_components/custom-node-schema`,
    {
      params: { flow_id: flowId, node_id: nodeId },
      headers: { accept: "application/json" }
    }
  );
  return response.data;
}
const _hoisted_1 = {
  key: 0,
  class: "p-4 text-center text-gray-500"
};
const _hoisted_2 = {
  key: 1,
  class: "p-4 text-red-600 bg-red-100 rounded-md"
};
const _hoisted_3 = {
  key: 2,
  class: "custom-node-wrapper"
};
const _hoisted_4 = { class: "listbox-subtitle" };
const _hoisted_5 = {
  key: 0,
  class: "section-description"
};
const _hoisted_6 = { class: "components-container" };
const _hoisted_7 = {
  key: 7,
  class: "text-red-500 text-xs"
};
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "CustomNode",
  setup(__props, { expose: __expose }) {
    const schema = ref(null);
    const formData = ref(null);
    const loading = ref(true);
    const error = ref("");
    const nodeStore = useNodeStore();
    const nodeData = ref(null);
    const availableColumns = ref([]);
    const currentNodeId = ref(null);
    const nodeUserDefined = ref(null);
    const columnTypes = ref([]);
    const loadNodeData = async (nodeId) => {
      var _a, _b, _c;
      loading.value = true;
      error.value = "";
      currentNodeId.value = nodeId;
      try {
        const inputNodeData = await nodeStore.getNodeData(nodeId, false);
        if (!inputNodeData) {
          return;
        }
        const [schemaData] = await Promise.all([getCustomNodeSchema(nodeStore.flow_id, nodeId)]);
        console.log("schemaData", schemaData);
        schema.value = schemaData;
        nodeData.value = inputNodeData;
        nodeUserDefined.value = (_a = nodeData.value) == null ? void 0 : _a.setting_input;
        if (!((_b = nodeData.value) == null ? void 0 : _b.setting_input.is_setup) && nodeUserDefined.value) {
          nodeUserDefined.value.settings = {};
        }
        if ((_c = inputNodeData == null ? void 0 : inputNodeData.main_input) == null ? void 0 : _c.columns) {
          availableColumns.value = inputNodeData.main_input.columns;
          columnTypes.value = inputNodeData.main_input.table_schema;
        } else {
          console.warn(
            `No main_input or columns found for node ${nodeId}. Select components may be empty.`
          );
        }
        initializeFormData(schemaData, inputNodeData == null ? void 0 : inputNodeData.setting_input);
      } catch (err) {
        error.value = err.message || "An unknown error occurred while loading node data.";
      } finally {
        loading.value = false;
      }
    };
    const pushNodeData = async () => {
      if (!nodeData.value || currentNodeId.value === null) {
        console.warn("Cannot push data: node data or ID is not available.");
        return;
      }
      if (nodeUserDefined.value) {
        nodeUserDefined.value.settings = formData.value;
        nodeUserDefined.value.is_user_defined = true;
        nodeUserDefined.value.is_setup = true;
      }
      console.log(JSON.stringify(formData.value, null, 2));
      nodeStore.updateUserDefinedSettings(nodeUserDefined);
    };
    function initializeFormData(schemaData, savedSettings) {
      var _a;
      const data = {};
      for (const sectionKey in schemaData.settings_schema) {
        data[sectionKey] = {};
        const section = schemaData.settings_schema[sectionKey];
        for (const componentKey in section.components) {
          const component = section.components[componentKey];
          const savedValue = (_a = savedSettings == null ? void 0 : savedSettings[sectionKey]) == null ? void 0 : _a[componentKey];
          if (savedValue !== void 0) {
            data[sectionKey][componentKey] = savedValue;
          } else if (component.value !== void 0) {
            data[sectionKey][componentKey] = component.value;
          } else {
            let defaultValue = component.default ?? null;
            if (component.input_type === "array" && defaultValue === null) {
              defaultValue = [];
            }
            data[sectionKey][componentKey] = defaultValue;
          }
        }
      }
      formData.value = data;
    }
    __expose({
      loadNodeData,
      pushNodeData
    });
    return (_ctx, _cache) => {
      return loading.value ? (openBlock(), createElementBlock("div", _hoisted_1, "Loading Node UI...")) : error.value ? (openBlock(), createElementBlock("div", _hoisted_2, [
        _cache[1] || (_cache[1] = createBaseVNode("strong", null, "Error:", -1)),
        createTextVNode(" " + toDisplayString(error.value), 1)
      ])) : schema.value && formData.value && nodeUserDefined.value ? (openBlock(), createElementBlock("div", _hoisted_3, [
        createVNode(GenericNodeSettings, {
          modelValue: nodeUserDefined.value,
          "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => nodeUserDefined.value = $event)
        }, {
          default: withCtx(() => [
            (openBlock(true), createElementBlock(Fragment, null, renderList(schema.value.settings_schema, (section, sectionKey) => {
              return withDirectives((openBlock(), createElementBlock("div", {
                key: sectionKey,
                class: "listbox-wrapper"
              }, [
                createBaseVNode("div", _hoisted_4, toDisplayString(section.title || sectionKey.toString().replace(/_/g, " ")), 1),
                section.description ? (openBlock(), createElementBlock("p", _hoisted_5, toDisplayString(section.description), 1)) : createCommentVNode("", true),
                createBaseVNode("div", _hoisted_6, [
                  (openBlock(true), createElementBlock(Fragment, null, renderList(section.components, (component, componentKey) => {
                    return openBlock(), createElementBlock("div", {
                      key: componentKey,
                      class: "component-item"
                    }, [
                      component.component_type === "TextInput" ? (openBlock(), createBlock(_sfc_main$1, {
                        key: 0,
                        modelValue: formData.value[sectionKey][componentKey],
                        "onUpdate:modelValue": ($event) => formData.value[sectionKey][componentKey] = $event,
                        schema: component
                      }, null, 8, ["modelValue", "onUpdate:modelValue", "schema"])) : component.component_type === "NumericInput" ? (openBlock(), createBlock(_sfc_main$2, {
                        key: 1,
                        modelValue: formData.value[sectionKey][componentKey],
                        "onUpdate:modelValue": ($event) => formData.value[sectionKey][componentKey] = $event,
                        schema: component
                      }, null, 8, ["modelValue", "onUpdate:modelValue", "schema"])) : component.component_type === "SliderInput" ? (openBlock(), createBlock(SliderInput, {
                        key: 2,
                        modelValue: formData.value[sectionKey][componentKey],
                        "onUpdate:modelValue": ($event) => formData.value[sectionKey][componentKey] = $event,
                        schema: component
                      }, null, 8, ["modelValue", "onUpdate:modelValue", "schema"])) : component.component_type === "MultiSelect" ? (openBlock(), createBlock(_sfc_main$3, {
                        key: 3,
                        modelValue: formData.value[sectionKey][componentKey],
                        "onUpdate:modelValue": ($event) => formData.value[sectionKey][componentKey] = $event,
                        schema: component,
                        "incoming-columns": availableColumns.value
                      }, null, 8, ["modelValue", "onUpdate:modelValue", "schema", "incoming-columns"])) : component.component_type === "SingleSelect" ? (openBlock(), createBlock(_sfc_main$4, {
                        key: 4,
                        modelValue: formData.value[sectionKey][componentKey],
                        "onUpdate:modelValue": ($event) => formData.value[sectionKey][componentKey] = $event,
                        schema: component,
                        "incoming-columns": availableColumns.value
                      }, null, 8, ["modelValue", "onUpdate:modelValue", "schema", "incoming-columns"])) : component.component_type === "ToggleSwitch" ? (openBlock(), createBlock(_sfc_main$5, {
                        key: 5,
                        modelValue: formData.value[sectionKey][componentKey],
                        "onUpdate:modelValue": ($event) => formData.value[sectionKey][componentKey] = $event,
                        schema: component
                      }, null, 8, ["modelValue", "onUpdate:modelValue", "schema"])) : component.component_type === "ColumnSelector" ? (openBlock(), createBlock(ColumnSelector, {
                        key: 6,
                        modelValue: formData.value[sectionKey][componentKey],
                        "onUpdate:modelValue": ($event) => formData.value[sectionKey][componentKey] = $event,
                        schema: component,
                        "incoming-columns": columnTypes.value
                      }, null, 8, ["modelValue", "onUpdate:modelValue", "schema", "incoming-columns"])) : (openBlock(), createElementBlock("div", _hoisted_7, " Unknown component type: " + toDisplayString(component.component_type), 1))
                    ]);
                  }), 128))
                ])
              ])), [
                [vShow, !section.hidden]
              ]);
            }), 128))
          ]),
          _: 1
        }, 8, ["modelValue"])
      ])) : createCommentVNode("", true);
    };
  }
});
const CustomNode_vue_vue_type_style_index_0_scoped_d7137248_lang = "";
const CustomNode = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-d7137248"]]);
export {
  CustomNode as default
};
