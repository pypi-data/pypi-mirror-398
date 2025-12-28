import { d as defineComponent, c as openBlock, e as createElementBlock, p as createBaseVNode, t as toDisplayString, g as createTextVNode, i as createCommentVNode, _ as _export_sfc } from "./index-5429bbf8.js";
const _hoisted_1 = { class: "listbox-wrapper" };
const _hoisted_2 = { class: "listbox-row" };
const _hoisted_3 = { class: "listbox-subtitle" };
const _hoisted_4 = { class: "items-container" };
const _hoisted_5 = {
  key: 0,
  class: "item-box"
};
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "SettingsSection",
  props: {
    title: { type: String, required: true },
    item: { type: String, required: true }
    // Changed to a single item
  },
  emits: ["removeItem"],
  setup(__props, { emit: __emit }) {
    const emit = __emit;
    const emitRemove = (item) => {
      emit("removeItem", item);
    };
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", _hoisted_1, [
        createBaseVNode("div", _hoisted_2, [
          createBaseVNode("div", _hoisted_3, toDisplayString(__props.title), 1),
          createBaseVNode("div", _hoisted_4, [
            __props.item !== "" ? (openBlock(), createElementBlock("div", _hoisted_5, [
              createTextVNode(toDisplayString(__props.item) + " ", 1),
              createBaseVNode("span", {
                class: "remove-btn",
                onClick: _cache[0] || (_cache[0] = ($event) => emitRemove(__props.item))
              }, "x")
            ])) : createCommentVNode("", true)
          ])
        ])
      ]);
    };
  }
});
const SettingsSection_vue_vue_type_style_index_0_scoped_43acf78a_lang = "";
const SettingsSection = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-43acf78a"]]);
export {
  SettingsSection as default
};
