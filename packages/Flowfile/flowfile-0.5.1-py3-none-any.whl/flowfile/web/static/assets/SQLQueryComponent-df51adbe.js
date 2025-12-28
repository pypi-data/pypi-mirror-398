import { d as defineComponent, c as openBlock, e as createElementBlock, p as createBaseVNode, _ as _export_sfc } from "./index-5429bbf8.js";
const _hoisted_1 = { class: "query-section" };
const _hoisted_2 = { class: "form-group" };
const _hoisted_3 = ["value"];
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "SQLQueryComponent",
  props: {
    modelValue: {}
  },
  emits: ["update:modelValue"],
  setup(__props, { emit: __emit }) {
    const emit = __emit;
    const onInput = (event) => {
      const target = event.target;
      emit("update:modelValue", target.value);
    };
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", _hoisted_1, [
        _cache[0] || (_cache[0] = createBaseVNode("h4", { class: "section-subtitle" }, "SQL Query", -1)),
        createBaseVNode("div", _hoisted_2, [
          createBaseVNode("textarea", {
            id: "query",
            value: _ctx.modelValue,
            class: "form-control textarea",
            placeholder: "Enter SQL query",
            rows: "4",
            onInput
          }, null, 40, _hoisted_3)
        ])
      ]);
    };
  }
});
const SQLQueryComponent_vue_vue_type_style_index_0_scoped_29602f2f_lang = "";
const SqlQueryComponent = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-29602f2f"]]);
export {
  SqlQueryComponent as default
};
