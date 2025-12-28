import { d as defineComponent, r as ref, b as resolveComponent, c as openBlock, e as createElementBlock, f as createVNode, w as withCtx, p as createBaseVNode, g as createTextVNode, i as createCommentVNode, u as unref, a8 as withDirectives, a9 as vModelText, h as createBlock, _ as _export_sfc } from "./index-5429bbf8.js";
import { C as CodeLoader } from "./vue-content-loader.es-2c8e608f.js";
import { C as ColumnSelector } from "./dropDown-614b998d.js";
import { u as useNodeStore } from "./vue-codemirror.esm-41b0e0d7.js";
import mainEditorRef from "./fullEditor-f7971590.js";
import { G as GenericNodeSettings } from "./genericNodeSettings-4fe5f36b.js";
import "./designer-9633482a.js";
const _hoisted_1 = { key: 0 };
const _hoisted_2 = { class: "listbox-wrapper" };
const _hoisted_3 = { style: { "border-radius": "20px" } };
const _hoisted_4 = { key: 0 };
const _hoisted_5 = { key: 1 };
const _hoisted_6 = { class: "selectors-row" };
const _hoisted_7 = { key: 0 };
const _hoisted_8 = { key: 1 };
const _hoisted_9 = { key: 2 };
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "Filter",
  setup(__props, { expose: __expose }) {
    const editorString = ref("");
    const isLoaded = ref(false);
    const isAdvancedFilter = ref(true);
    const nodeStore = useNodeStore();
    const nodeFilter = ref(null);
    const nodeData = ref(null);
    const showOptions = ref(false);
    const editorChild = ref(null);
    const comparisonMapping = {
      Equals: "=",
      "Smaller then": "<",
      "Greater then": ">",
      Contains: "contains",
      // or any other representation you prefer
      "Does not equal": "!=",
      "Smaller or equal": "<=",
      "Greater or equal": ">="
    };
    const reversedMapping = {};
    Object.entries(comparisonMapping).forEach(([key, value]) => {
      reversedMapping[value] = key;
    });
    const translateSymbolToDes = (symbol) => {
      return reversedMapping[symbol] ?? symbol;
    };
    const comparisonOptions = Object.keys(comparisonMapping);
    const handleFieldChange = (newValue) => {
      var _a;
      if ((_a = nodeFilter.value) == null ? void 0 : _a.filter_input.basic_filter) {
        nodeFilter.value.filter_input.basic_filter.field = newValue;
      }
    };
    function translateComparison(input) {
      return comparisonMapping[input] ?? input;
    }
    const handleFilterTypeChange = (newValue) => {
      var _a;
      if ((_a = nodeFilter.value) == null ? void 0 : _a.filter_input.basic_filter) {
        const symbolicType = translateComparison(newValue);
        nodeFilter.value.filter_input.basic_filter.filter_type = symbolicType;
      }
    };
    const loadNodeData = async (nodeId) => {
      var _a, _b, _c;
      nodeData.value = await nodeStore.getNodeData(nodeId, false);
      if (nodeData.value) {
        nodeFilter.value = nodeData.value.setting_input;
        if ((_a = nodeFilter.value) == null ? void 0 : _a.filter_input.advanced_filter) {
          editorString.value = (_b = nodeFilter.value) == null ? void 0 : _b.filter_input.advanced_filter;
        }
        isAdvancedFilter.value = ((_c = nodeFilter.value) == null ? void 0 : _c.filter_input.filter_type) === "advanced";
      }
      isLoaded.value = true;
    };
    const updateAdvancedFilter = () => {
      if (nodeFilter.value) {
        nodeFilter.value.filter_input.advanced_filter = nodeStore.inputCode;
        console.log(nodeFilter.value);
      }
    };
    const pushNodeData = async () => {
      if (nodeFilter.value) {
        if (isAdvancedFilter.value) {
          updateAdvancedFilter();
          nodeFilter.value.filter_input.filter_type = "advanced";
        } else {
          nodeFilter.value.filter_input.filter_type = "basic";
        }
        nodeStore.updateSettings(nodeFilter);
      }
    };
    __expose({ loadNodeData, pushNodeData });
    return (_ctx, _cache) => {
      const _component_el_switch = resolveComponent("el-switch");
      return isLoaded.value && nodeFilter.value ? (openBlock(), createElementBlock("div", _hoisted_1, [
        createVNode(GenericNodeSettings, {
          modelValue: nodeFilter.value,
          "onUpdate:modelValue": _cache[6] || (_cache[6] = ($event) => nodeFilter.value = $event)
        }, {
          default: withCtx(() => {
            var _a, _b, _c, _d, _e;
            return [
              createBaseVNode("div", _hoisted_2, [
                createBaseVNode("div", _hoisted_3, [
                  createVNode(_component_el_switch, {
                    modelValue: isAdvancedFilter.value,
                    "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => isAdvancedFilter.value = $event),
                    class: "mb-2",
                    "active-text": "Advanced filter options",
                    "inactive-text": "Basic filter"
                  }, null, 8, ["modelValue"])
                ]),
                isAdvancedFilter.value ? (openBlock(), createElementBlock("div", _hoisted_4, [
                  _cache[7] || (_cache[7] = createTextVNode(" Advanced filter ")),
                  createVNode(mainEditorRef, {
                    ref_key: "editorChild",
                    ref: editorChild,
                    "editor-string": editorString.value
                  }, null, 8, ["editor-string"])
                ])) : createCommentVNode("", true),
                !isAdvancedFilter.value ? (openBlock(), createElementBlock("div", _hoisted_5, [
                  _cache[8] || (_cache[8] = createTextVNode(" Standard Filter ")),
                  createBaseVNode("div", _hoisted_6, [
                    ((_a = nodeFilter.value) == null ? void 0 : _a.filter_input.basic_filter) ? (openBlock(), createElementBlock("div", _hoisted_7, [
                      createVNode(ColumnSelector, {
                        modelValue: nodeFilter.value.filter_input.basic_filter.field,
                        "onUpdate:modelValue": _cache[1] || (_cache[1] = ($event) => nodeFilter.value.filter_input.basic_filter.field = $event),
                        value: nodeFilter.value.filter_input.basic_filter.field,
                        "column-options": (_c = (_b = nodeData.value) == null ? void 0 : _b.main_input) == null ? void 0 : _c.columns,
                        "onUpdate:value": _cache[2] || (_cache[2] = (value) => handleFieldChange(value))
                      }, null, 8, ["modelValue", "value", "column-options"])
                    ])) : createCommentVNode("", true),
                    ((_d = nodeFilter.value) == null ? void 0 : _d.filter_input.basic_filter) ? (openBlock(), createElementBlock("div", _hoisted_8, [
                      createVNode(ColumnSelector, {
                        value: translateSymbolToDes(nodeFilter.value.filter_input.basic_filter.filter_type),
                        "column-options": unref(comparisonOptions),
                        "onUpdate:value": _cache[3] || (_cache[3] = (value) => handleFilterTypeChange(value))
                      }, null, 8, ["value", "column-options"])
                    ])) : createCommentVNode("", true),
                    ((_e = nodeFilter.value) == null ? void 0 : _e.filter_input.basic_filter) ? (openBlock(), createElementBlock("div", _hoisted_9, [
                      withDirectives(createBaseVNode("input", {
                        "onUpdate:modelValue": _cache[4] || (_cache[4] = ($event) => nodeFilter.value.filter_input.basic_filter.filter_value = $event),
                        type: "text",
                        class: "input-field",
                        onFocus: _cache[5] || (_cache[5] = ($event) => showOptions.value = true)
                      }, null, 544), [
                        [vModelText, nodeFilter.value.filter_input.basic_filter.filter_value]
                      ])
                    ])) : createCommentVNode("", true)
                  ])
                ])) : createCommentVNode("", true)
              ])
            ];
          }),
          _: 1
        }, 8, ["modelValue"])
      ])) : (openBlock(), createBlock(unref(CodeLoader), { key: 1 }));
    };
  }
});
const Filter_vue_vue_type_style_index_0_scoped_08e238c3_lang = "";
const Filter = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-08e238c3"]]);
export {
  Filter as default
};
