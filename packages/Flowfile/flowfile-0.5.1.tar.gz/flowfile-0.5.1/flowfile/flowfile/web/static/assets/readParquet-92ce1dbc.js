import { d as defineComponent, c as openBlock, e as createElementBlock, p as createBaseVNode, _ as _export_sfc } from "./index-5429bbf8.js";
const _hoisted_1 = { class: "parquet-table-settings" };
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "readParquet",
  props: {
    modelValue: {}
  },
  setup(__props) {
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", _hoisted_1, _cache[0] || (_cache[0] = [
        createBaseVNode("div", { class: "message" }, [
          createBaseVNode("h2", null, "You are ready to flow!"),
          createBaseVNode("p", null, "Your Parquet table setup is complete. Enjoy the smooth data processing experience.")
        ], -1)
      ]));
    };
  }
});
const readParquet_vue_vue_type_style_index_0_scoped_6f7c2759_lang = "";
const ParquetTableConfig = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-6f7c2759"]]);
export {
  ParquetTableConfig as default
};
