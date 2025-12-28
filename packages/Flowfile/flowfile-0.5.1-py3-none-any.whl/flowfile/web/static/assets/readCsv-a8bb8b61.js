import { d as defineComponent, r as ref, m as watch, b as resolveComponent, c as openBlock, e as createElementBlock, p as createBaseVNode, f as createVNode, w as withCtx, F as Fragment, q as renderList, h as createBlock, _ as _export_sfc } from "./index-5429bbf8.js";
const _hoisted_1 = { class: "csv-table-settings" };
const _hoisted_2 = { class: "row" };
const _hoisted_3 = { class: "row" };
const _hoisted_4 = { class: "row" };
const _hoisted_5 = { class: "row" };
const _hoisted_6 = { class: "row" };
const _hoisted_7 = { class: "row" };
const _hoisted_8 = { class: "row" };
const _hoisted_9 = { class: "row" };
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "readCsv",
  props: {
    modelValue: {}
  },
  emits: ["update:modelValue"],
  setup(__props, { emit: __emit }) {
    const props = __props;
    const emit = __emit;
    const localCsvTable = ref({ ...props.modelValue });
    const updateParent = () => {
      emit("update:modelValue", localCsvTable.value);
    };
    const csv_settings = {
      delimiter_options: [",", ";", "|", "tab"],
      encoding_options: ["utf-8", "ISO-8859-1", "ASCII"],
      row_delimiter: ["\\n", "\\r\\n", "\\r"],
      quote_char: ['"', "'", "auto"]
    };
    watch(
      () => props.modelValue,
      (newVal) => {
        localCsvTable.value = newVal;
      },
      { deep: true }
    );
    return (_ctx, _cache) => {
      const _component_el_checkbox = resolveComponent("el-checkbox");
      const _component_el_option = resolveComponent("el-option");
      const _component_el_select = resolveComponent("el-select");
      const _component_el_slider = resolveComponent("el-slider");
      return openBlock(), createElementBlock("div", _hoisted_1, [
        createBaseVNode("div", _hoisted_2, [
          _cache[8] || (_cache[8] = createBaseVNode("label", { for: "has-headers" }, "Has Headers:", -1)),
          createVNode(_component_el_checkbox, {
            modelValue: localCsvTable.value.has_headers,
            "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => localCsvTable.value.has_headers = $event),
            size: "large",
            onChange: updateParent
          }, null, 8, ["modelValue"])
        ]),
        createBaseVNode("div", _hoisted_3, [
          _cache[9] || (_cache[9] = createBaseVNode("label", { for: "delimiter" }, "Delimiter:", -1)),
          createVNode(_component_el_select, {
            modelValue: localCsvTable.value.delimiter,
            "onUpdate:modelValue": _cache[1] || (_cache[1] = ($event) => localCsvTable.value.delimiter = $event),
            placeholder: "Select delimiter",
            clearable: "",
            size: "small",
            onChange: updateParent
          }, {
            default: withCtx(() => [
              (openBlock(true), createElementBlock(Fragment, null, renderList(csv_settings.delimiter_options, (option) => {
                return openBlock(), createBlock(_component_el_option, {
                  key: option,
                  label: option,
                  value: option
                }, null, 8, ["label", "value"]);
              }), 128))
            ]),
            _: 1
          }, 8, ["modelValue"])
        ]),
        createBaseVNode("div", _hoisted_4, [
          _cache[10] || (_cache[10] = createBaseVNode("label", { for: "encoding" }, "Encoding:", -1)),
          createVNode(_component_el_select, {
            modelValue: localCsvTable.value.encoding,
            "onUpdate:modelValue": _cache[2] || (_cache[2] = ($event) => localCsvTable.value.encoding = $event),
            placeholder: "Select encoding",
            clearable: "",
            size: "small",
            onChange: updateParent
          }, {
            default: withCtx(() => [
              (openBlock(true), createElementBlock(Fragment, null, renderList(csv_settings.encoding_options, (option) => {
                return openBlock(), createBlock(_component_el_option, {
                  key: option,
                  label: option,
                  value: option
                }, null, 8, ["label", "value"]);
              }), 128))
            ]),
            _: 1
          }, 8, ["modelValue"])
        ]),
        createBaseVNode("div", _hoisted_5, [
          _cache[11] || (_cache[11] = createBaseVNode("label", { for: "quote-char" }, "Quote Character:", -1)),
          createVNode(_component_el_select, {
            modelValue: localCsvTable.value.quote_char,
            "onUpdate:modelValue": _cache[3] || (_cache[3] = ($event) => localCsvTable.value.quote_char = $event),
            placeholder: "Select quote character",
            clearable: "",
            size: "small",
            onChange: updateParent
          }, {
            default: withCtx(() => [
              (openBlock(true), createElementBlock(Fragment, null, renderList(csv_settings.quote_char, (option) => {
                return openBlock(), createBlock(_component_el_option, {
                  key: option,
                  label: option,
                  value: option
                }, null, 8, ["label", "value"]);
              }), 128))
            ]),
            _: 1
          }, 8, ["modelValue"])
        ]),
        createBaseVNode("div", _hoisted_6, [
          _cache[12] || (_cache[12] = createBaseVNode("label", { for: "row-delimiter" }, "New Line Delimiter:", -1)),
          createVNode(_component_el_select, {
            modelValue: localCsvTable.value.row_delimiter,
            "onUpdate:modelValue": _cache[4] || (_cache[4] = ($event) => localCsvTable.value.row_delimiter = $event),
            placeholder: "Select new line delimiter",
            clearable: "",
            size: "small",
            onChange: updateParent
          }, {
            default: withCtx(() => [
              (openBlock(true), createElementBlock(Fragment, null, renderList(csv_settings.row_delimiter, (option) => {
                return openBlock(), createBlock(_component_el_option, {
                  key: option,
                  label: option,
                  value: option
                }, null, 8, ["label", "value"]);
              }), 128))
            ]),
            _: 1
          }, 8, ["modelValue"])
        ]),
        createBaseVNode("div", _hoisted_7, [
          _cache[13] || (_cache[13] = createBaseVNode("label", { for: "infer-schema-length" }, "Schema Infer Length:", -1)),
          createVNode(_component_el_slider, {
            modelValue: localCsvTable.value.infer_schema_length,
            "onUpdate:modelValue": _cache[5] || (_cache[5] = ($event) => localCsvTable.value.infer_schema_length = $event),
            step: 1e3,
            max: 1e5,
            min: 0,
            "show-stops": "",
            size: "small",
            onChange: updateParent
          }, null, 8, ["modelValue"])
        ]),
        createBaseVNode("div", _hoisted_8, [
          _cache[14] || (_cache[14] = createBaseVNode("label", { for: "truncate-long-lines" }, "Truncate Long Lines:", -1)),
          createVNode(_component_el_checkbox, {
            modelValue: localCsvTable.value.truncate_ragged_lines,
            "onUpdate:modelValue": _cache[6] || (_cache[6] = ($event) => localCsvTable.value.truncate_ragged_lines = $event),
            size: "large",
            onChange: updateParent
          }, null, 8, ["modelValue"])
        ]),
        createBaseVNode("div", _hoisted_9, [
          _cache[15] || (_cache[15] = createBaseVNode("label", { for: "ignore-errors" }, "Ignore Errors:", -1)),
          createVNode(_component_el_checkbox, {
            modelValue: localCsvTable.value.ignore_errors,
            "onUpdate:modelValue": _cache[7] || (_cache[7] = ($event) => localCsvTable.value.ignore_errors = $event),
            size: "large",
            onChange: updateParent
          }, null, 8, ["modelValue"])
        ])
      ]);
    };
  }
});
const readCsv_vue_vue_type_style_index_0_scoped_86748428_lang = "";
const CsvTableConfig = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-86748428"]]);
export {
  CsvTableConfig as default
};
