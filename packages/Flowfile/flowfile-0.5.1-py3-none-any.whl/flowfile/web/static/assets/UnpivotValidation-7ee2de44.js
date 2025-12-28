import { d as defineComponent, l as computed, c as openBlock, h as createBlock, w as withCtx, f as createVNode, p as createBaseVNode, u as unref, ar as ElIcon, e as createElementBlock, i as createCommentVNode, as as ElPopover, _ as _export_sfc } from "./index-5429bbf8.js";
const _hoisted_1 = { class: "validation-wrapper" };
const _hoisted_2 = {
  key: 0,
  class: "error-message"
};
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "UnpivotValidation",
  props: {
    unpivotInput: {}
  },
  setup(__props) {
    const props = __props;
    const showValidationMessages = computed(() => {
      return !(props.unpivotInput.index_columns.length === 0);
    });
    return (_ctx, _cache) => {
      return showValidationMessages.value ? (openBlock(), createBlock(unref(ElPopover), {
        key: 0,
        placement: "top",
        width: "200",
        trigger: "hover",
        content: "Some required fields are missing"
      }, {
        reference: withCtx(() => [
          createVNode(unref(ElIcon), {
            color: "#FF6B6B",
            class: "warning-icon"
          }, {
            default: withCtx(() => _cache[0] || (_cache[0] = [
              createBaseVNode("i", { class: "el-icon-warning" }, null, -1)
            ])),
            _: 1,
            __: [0]
          })
        ]),
        default: withCtx(() => [
          createBaseVNode("div", _hoisted_1, [
            !_ctx.unpivotInput.index_columns ? (openBlock(), createElementBlock("p", _hoisted_2, "Index Column cannot be empty.")) : createCommentVNode("", true)
          ])
        ]),
        _: 1
      })) : createCommentVNode("", true);
    };
  }
});
const UnpivotValidation_vue_vue_type_style_index_0_scoped_1575257f_lang = "";
const UnpivotValidation = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-1575257f"]]);
export {
  UnpivotValidation as default
};
