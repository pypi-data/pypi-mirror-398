import { d as defineComponent, l as computed, e as createElementBlock, p as createBaseVNode, c as openBlock, _ as _export_sfc } from "./index-5429bbf8.js";
const _hoisted_1 = { class: "doc-wrapper" };
const _hoisted_2 = ["src"];
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "documentation",
  setup(__props) {
    const docsUrl = computed(
      () => "https://edwardvaneechoud.github.io/Flowfile/"
    );
    const openFlowfile = () => {
      window.open(docsUrl.value);
    };
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", _hoisted_1, [
        createBaseVNode("iframe", {
          src: docsUrl.value,
          class: "iframe-docs"
        }, null, 8, _hoisted_2),
        createBaseVNode("button", {
          class: "flowfile-button",
          onClick: openFlowfile
        }, _cache[0] || (_cache[0] = [
          createBaseVNode("i", { class: "fas fa-up-right-from-square" }, null, -1)
        ]))
      ]);
    };
  }
});
const documentation_vue_vue_type_style_index_0_scoped_3ea9235d_lang = "";
const documentation = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-3ea9235d"]]);
export {
  documentation as default
};
