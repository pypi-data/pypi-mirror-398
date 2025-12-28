import { d as defineComponent, c as openBlock, e as createElementBlock, p as createBaseVNode, F as Fragment, q as renderList, s as normalizeClass, t as toDisplayString, T as normalizeStyle, _ as _export_sfc } from "./index-5429bbf8.js";
const _hoisted_1 = ["onClick"];
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "ContextMenu",
  props: {
    position: { type: Object, required: true },
    options: {
      type: Array,
      required: true
    }
  },
  emits: ["select", "close"],
  setup(__props, { emit: __emit }) {
    const emit = __emit;
    const selectOption = (action) => {
      emit("select", action);
      emit("close");
    };
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", {
        class: "context-menu",
        style: normalizeStyle({ top: __props.position.y + "px", left: __props.position.x + "px" })
      }, [
        createBaseVNode("ul", null, [
          (openBlock(true), createElementBlock(Fragment, null, renderList(__props.options, (option) => {
            return openBlock(), createElementBlock("li", {
              key: option.action,
              class: normalizeClass({ disabled: option.disabled }),
              onClick: ($event) => !option.disabled && selectOption(option.action)
            }, toDisplayString(option.label), 11, _hoisted_1);
          }), 128))
        ])
      ], 4);
    };
  }
});
const ContextMenu_vue_vue_type_style_index_0_scoped_d0286fd2_lang = "";
const ContextMenu = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-d0286fd2"]]);
export {
  ContextMenu as default
};
