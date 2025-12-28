import { P as PopOver } from "./vue-codemirror.esm-41b0e0d7.js";
import { d as defineComponent, c as openBlock, h as createBlock, w as withCtx, p as createBaseVNode, t as toDisplayString, _ as _export_sfc } from "./index-5429bbf8.js";
const _hoisted_1 = { class: "icon-wrapper" };
const _hoisted_2 = { class: "unavailable-icon" };
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "UnavailableFields",
  props: {
    iconText: {
      type: String,
      default: "!"
      // Default to '!' if no input is provided
    },
    tooltipText: {
      type: String,
      default: "Field not available"
      // Default tooltip text
    }
  },
  setup(__props) {
    return (_ctx, _cache) => {
      return openBlock(), createBlock(PopOver, { content: __props.tooltipText }, {
        default: withCtx(() => [
          createBaseVNode("div", _hoisted_1, [
            createBaseVNode("span", _hoisted_2, toDisplayString(__props.iconText), 1)
          ])
        ]),
        _: 1
      }, 8, ["content"]);
    };
  }
});
const UnavailableFields_vue_vue_type_style_index_0_scoped_8e1fe8b0_lang = "";
const unavailableField = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-8e1fe8b0"]]);
export {
  unavailableField as u
};
