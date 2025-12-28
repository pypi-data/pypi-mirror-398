import { d as defineComponent, r as ref, m as watch, c as openBlock, e as createElementBlock, p as createBaseVNode, f as createVNode, w as withCtx, F as Fragment, q as renderList, h as createBlock, u as unref, at as ElOption, au as ElSelect, _ as _export_sfc } from "./index-5429bbf8.js";
const _hoisted_1 = { class: "csv-table-settings" };
const _hoisted_2 = { class: "input-group" };
const _hoisted_3 = { class: "input-group" };
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "outputCsv",
  props: {
    modelValue: {
      type: Object,
      required: true
    }
  },
  emits: ["update:modelValue"],
  setup(__props, { emit: __emit }) {
    const props = __props;
    const emit = __emit;
    const localCsvTable = ref(props.modelValue);
    const csv_settings = {
      delimiter_options: [",", ";", "|", "tab"],
      encoding_options: ["utf-8", "ISO-8859-1", "ASCII"]
    };
    const updateParent = () => {
      emit("update:modelValue", localCsvTable.value);
    };
    watch(
      () => props.modelValue,
      (newVal) => {
        localCsvTable.value = newVal;
      },
      { deep: true }
    );
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", _hoisted_1, [
        createBaseVNode("div", _hoisted_2, [
          _cache[2] || (_cache[2] = createBaseVNode("label", { for: "delimiter" }, "File delimiter:", -1)),
          createVNode(unref(ElSelect), {
            modelValue: localCsvTable.value.delimiter,
            "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => localCsvTable.value.delimiter = $event),
            placeholder: "Select delimiter",
            size: "small",
            style: { "max-width": "200px" },
            onChange: updateParent
          }, {
            default: withCtx(() => [
              (openBlock(true), createElementBlock(Fragment, null, renderList(csv_settings.delimiter_options, (option) => {
                return openBlock(), createBlock(unref(ElOption), {
                  key: option,
                  label: option,
                  value: option
                }, null, 8, ["label", "value"]);
              }), 128))
            ]),
            _: 1
          }, 8, ["modelValue"])
        ]),
        createBaseVNode("div", _hoisted_3, [
          _cache[3] || (_cache[3] = createBaseVNode("label", { for: "encoding" }, "File encoding:", -1)),
          createVNode(unref(ElSelect), {
            modelValue: localCsvTable.value.encoding,
            "onUpdate:modelValue": _cache[1] || (_cache[1] = ($event) => localCsvTable.value.encoding = $event),
            placeholder: "Select encoding",
            size: "small",
            style: { "max-width": "200px" },
            onChange: updateParent
          }, {
            default: withCtx(() => [
              (openBlock(true), createElementBlock(Fragment, null, renderList(csv_settings.encoding_options, (option) => {
                return openBlock(), createBlock(unref(ElOption), {
                  key: option,
                  label: option,
                  value: option
                }, null, 8, ["label", "value"]);
              }), 128))
            ]),
            _: 1
          }, 8, ["modelValue"])
        ])
      ]);
    };
  }
});
const outputCsv_vue_vue_type_style_index_0_scoped_9ecfb42a_lang = "";
const CsvTableConfig = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-9ecfb42a"]]);
export {
  CsvTableConfig as default
};
