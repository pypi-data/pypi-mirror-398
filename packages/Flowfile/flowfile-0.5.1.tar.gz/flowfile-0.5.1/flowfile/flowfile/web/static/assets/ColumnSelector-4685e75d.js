import { d as defineComponent, l as computed, b as resolveComponent, c as openBlock, e as createElementBlock, p as createBaseVNode, g as createTextVNode, t as toDisplayString, i as createCommentVNode, f as createVNode, w as withCtx, F as Fragment, q as renderList, h as createBlock, _ as _export_sfc } from "./index-5429bbf8.js";
const _hoisted_1 = { class: "component-container" };
const _hoisted_2 = { class: "listbox-subtitle" };
const _hoisted_3 = {
  key: 0,
  class: "required-indicator"
};
const _hoisted_4 = { class: "column-type" };
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "ColumnSelector",
  props: {
    schema: {
      type: Object,
      required: true
    },
    modelValue: {
      type: [String, Array],
      default: () => []
    },
    incomingColumns: {
      type: Array,
      default: () => []
    }
  },
  emits: ["update:modelValue"],
  setup(__props) {
    const props = __props;
    const filteredColumns = computed(() => {
      console.log("props.schem.data_types", props.schema);
      console.log("incoming columns", props.incomingColumns);
      if (!props.schema.data_types || props.schema.data_types === "ALL") {
        return props.incomingColumns;
      }
      if (Array.isArray(props.schema.data_types)) {
        return props.incomingColumns.filter((column) => {
          return props.schema.data_types.includes(column.data_type);
        });
      }
      return props.incomingColumns;
    });
    return (_ctx, _cache) => {
      const _component_el_option = resolveComponent("el-option");
      const _component_el_select = resolveComponent("el-select");
      return openBlock(), createElementBlock("div", _hoisted_1, [
        createBaseVNode("label", _hoisted_2, [
          createTextVNode(toDisplayString(__props.schema.label) + " ", 1),
          __props.schema.required ? (openBlock(), createElementBlock("span", _hoisted_3, "*")) : createCommentVNode("", true)
        ]),
        createVNode(_component_el_select, {
          "model-value": __props.modelValue,
          multiple: __props.schema.multiple,
          filterable: "",
          placeholder: __props.schema.multiple ? "Select columns..." : "Select a column...",
          style: { "width": "100%" },
          size: "large",
          "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => _ctx.$emit("update:modelValue", $event))
        }, {
          default: withCtx(() => [
            (openBlock(true), createElementBlock(Fragment, null, renderList(filteredColumns.value, (column) => {
              return openBlock(), createBlock(_component_el_option, {
                key: column.name,
                label: column.name,
                value: column.name
              }, {
                default: withCtx(() => [
                  createBaseVNode("span", null, toDisplayString(column.name), 1),
                  createBaseVNode("span", _hoisted_4, toDisplayString(column.data_type), 1)
                ]),
                _: 2
              }, 1032, ["label", "value"]);
            }), 128))
          ]),
          _: 1
        }, 8, ["model-value", "multiple", "placeholder"])
      ]);
    };
  }
});
const ColumnSelector_vue_vue_type_style_index_0_scoped_ee9d221e_lang = "";
const ColumnSelector = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-ee9d221e"]]);
export {
  ColumnSelector as default
};
