import { d as defineComponent, r as ref, m as watch, c as openBlock, e as createElementBlock, _ as _export_sfc } from "./index-5429bbf8.js";
const _hoisted_1 = { class: "parquet-table-settings" };
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "outputParquet",
  props: {
    modelValue: {
      type: Object,
      required: true
    }
  },
  emits: ["update:modelValue"],
  setup(__props, { emit: __emit }) {
    const props = __props;
    const localParquetTable = ref(props.modelValue);
    watch(
      () => props.modelValue,
      (newVal) => {
        localParquetTable.value = newVal;
      },
      { deep: true }
    );
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", _hoisted_1);
    };
  }
});
const outputParquet_vue_vue_type_style_index_0_scoped_7db0128e_lang = "";
const ParquetTableConfig = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-7db0128e"]]);
export {
  ParquetTableConfig as default
};
