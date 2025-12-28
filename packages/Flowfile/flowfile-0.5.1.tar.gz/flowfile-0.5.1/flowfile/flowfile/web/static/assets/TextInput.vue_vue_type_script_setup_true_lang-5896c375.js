import { d as defineComponent, b as resolveComponent, c as openBlock, e as createElementBlock, p as createBaseVNode, t as toDisplayString, f as createVNode } from "./index-5429bbf8.js";
const _hoisted_1 = { class: "component-container" };
const _hoisted_2 = { class: "listbox-subtitle" };
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "TextInput",
  props: {
    schema: {
      type: Object,
      required: true
    },
    modelValue: String
  },
  emits: ["update:modelValue"],
  setup(__props) {
    return (_ctx, _cache) => {
      const _component_el_input = resolveComponent("el-input");
      return openBlock(), createElementBlock("div", _hoisted_1, [
        createBaseVNode("label", _hoisted_2, toDisplayString(__props.schema.label), 1),
        createVNode(_component_el_input, {
          "model-value": __props.modelValue,
          placeholder: __props.schema.placeholder || "Enter value...",
          clearable: "",
          size: "large",
          "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => _ctx.$emit("update:modelValue", $event))
        }, null, 8, ["model-value", "placeholder"])
      ]);
    };
  }
});
export {
  _sfc_main as _
};
