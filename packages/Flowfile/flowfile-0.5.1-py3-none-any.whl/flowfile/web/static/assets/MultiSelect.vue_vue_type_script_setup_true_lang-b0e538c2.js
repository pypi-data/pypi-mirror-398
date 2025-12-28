import { d as defineComponent, l as computed, b as resolveComponent, c as openBlock, e as createElementBlock, p as createBaseVNode, t as toDisplayString, f as createVNode, w as withCtx, F as Fragment, q as renderList, h as createBlock } from "./index-5429bbf8.js";
const _hoisted_1 = { class: "component-container" };
const _hoisted_2 = { class: "listbox-subtitle" };
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "MultiSelect",
  props: {
    schema: {
      type: Object,
      required: true
    },
    modelValue: {
      type: Array,
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
    const options = computed(() => {
      if (props.schema.options && !Array.isArray(props.schema.options) && props.schema.options.__type__ === "IncomingColumns") {
        return props.incomingColumns;
      }
      if (Array.isArray(props.schema.options)) {
        return props.schema.options;
      }
      return [];
    });
    return (_ctx, _cache) => {
      const _component_el_option = resolveComponent("el-option");
      const _component_el_select = resolveComponent("el-select");
      return openBlock(), createElementBlock("div", _hoisted_1, [
        createBaseVNode("label", _hoisted_2, toDisplayString(__props.schema.label), 1),
        createVNode(_component_el_select, {
          "model-value": __props.modelValue,
          multiple: "",
          filterable: "",
          placeholder: "Select one or more options",
          style: { "width": "100%" },
          size: "large",
          "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => _ctx.$emit("update:modelValue", $event))
        }, {
          default: withCtx(() => [
            (openBlock(true), createElementBlock(Fragment, null, renderList(options.value, (item) => {
              return openBlock(), createBlock(_component_el_option, {
                key: Array.isArray(item) ? item[0] : item,
                label: Array.isArray(item) ? item[1] : item,
                value: Array.isArray(item) ? item[0] : item
              }, null, 8, ["label", "value"]);
            }), 128))
          ]),
          _: 1
        }, 8, ["model-value"])
      ]);
    };
  }
});
export {
  _sfc_main as _
};
