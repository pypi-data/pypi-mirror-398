import { d as defineComponent, b as resolveComponent, c as openBlock, e as createElementBlock, p as createBaseVNode, t as toDisplayString, f as createVNode, _ as _export_sfc } from "./index-5429bbf8.js";
const _hoisted_1 = { class: "component-container" };
const _hoisted_2 = { class: "listbox-subtitle" };
const _hoisted_3 = { class: "slider-wrapper" };
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "SliderInput",
  props: {
    schema: {
      type: Object,
      required: true
    },
    modelValue: Number
  },
  emits: ["update:modelValue"],
  setup(__props) {
    return (_ctx, _cache) => {
      const _component_el_slider = resolveComponent("el-slider");
      return openBlock(), createElementBlock("div", _hoisted_1, [
        createBaseVNode("label", _hoisted_2, toDisplayString(__props.schema.label), 1),
        createBaseVNode("div", _hoisted_3, [
          createVNode(_component_el_slider, {
            "model-value": __props.modelValue,
            min: __props.schema.min_value,
            max: __props.schema.max_value,
            step: __props.schema.step || 1,
            "show-input": true,
            size: "large",
            style: { "width": "100%" },
            "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => _ctx.$emit("update:modelValue", $event))
          }, null, 8, ["model-value", "min", "max", "step"])
        ])
      ]);
    };
  }
});
const SliderInput_vue_vue_type_style_index_0_scoped_8182875c_lang = "";
const SliderInput = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-8182875c"]]);
export {
  SliderInput as default
};
