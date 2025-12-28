import { a as axios, d as defineComponent, r as ref, l as computed, n as onMounted, m as watch, b as resolveComponent, c as openBlock, e as createElementBlock, p as createBaseVNode, f as createVNode, w as withCtx, i as createCommentVNode, t as toDisplayString, a8 as withDirectives, a9 as vModelText, h as createBlock, u as unref, _ as _export_sfc } from "./index-5429bbf8.js";
import { C as ColumnSelector } from "./dropDown-614b998d.js";
import { C as CodeLoader } from "./vue-content-loader.es-2c8e608f.js";
const getXlsxSheetNamesForPath = async (path) => {
  const response = await axios.get(`/api/get_xlsx_sheet_names?path=${path}`);
  return response.data;
};
const _hoisted_1 = { key: 0 };
const _hoisted_2 = { class: "table" };
const _hoisted_3 = {
  key: 0,
  class: "selectors"
};
const _hoisted_4 = { class: "row" };
const _hoisted_5 = { class: "input-wrapper" };
const _hoisted_6 = {
  key: 0,
  class: "warning-sign"
};
const _hoisted_7 = { class: "row" };
const _hoisted_8 = { class: "button-container" };
const _hoisted_9 = {
  key: 0,
  class: "optional-section"
};
const _hoisted_10 = { class: "row" };
const _hoisted_11 = { class: "input-wrapper" };
const _hoisted_12 = { class: "input-wrapper" };
const _hoisted_13 = { class: "row" };
const _hoisted_14 = { class: "input-wrapper" };
const _hoisted_15 = { class: "input-wrapper" };
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "readExcel",
  props: {
    modelValue: {},
    path: {}
  },
  emits: ["update:modelValue"],
  setup(__props, { emit: __emit }) {
    const props = __props;
    const isLoaded = ref(false);
    const emit = __emit;
    const localExcelTable = ref({ ...props.modelValue });
    const showOptionalSettings = ref(false);
    const sheetNames = ref([]);
    const sheetNamesLoaded = ref(false);
    const getSheetNames = async () => {
      sheetNames.value = await getXlsxSheetNamesForPath(props.path);
      sheetNamesLoaded.value = true;
    };
    const toggleOptionalSettings = () => {
      showOptionalSettings.value = !showOptionalSettings.value;
    };
    const showWarning = computed(() => {
      if (!sheetNamesLoaded.value || !localExcelTable.value.sheet_name) {
        return false;
      }
      return !sheetNames.value.includes(localExcelTable.value.sheet_name);
    });
    onMounted(() => {
      if (props.path) {
        getSheetNames();
      }
      isLoaded.value = true;
    });
    watch(
      () => localExcelTable.value,
      (newValue) => {
        emit("update:modelValue", { ...newValue });
      },
      { deep: true }
    );
    return (_ctx, _cache) => {
      const _component_el_row = resolveComponent("el-row");
      const _component_el_checkbox = resolveComponent("el-checkbox");
      return isLoaded.value ? (openBlock(), createElementBlock("div", _hoisted_1, [
        createBaseVNode("div", _hoisted_2, [
          localExcelTable.value ? (openBlock(), createElementBlock("div", _hoisted_3, [
            createBaseVNode("div", _hoisted_4, [
              createVNode(_component_el_row, null, {
                default: withCtx(() => [
                  createBaseVNode("div", _hoisted_5, [
                    _cache[7] || (_cache[7] = createBaseVNode("label", null, "Sheet Name", -1)),
                    createVNode(ColumnSelector, {
                      modelValue: localExcelTable.value.sheet_name,
                      "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => localExcelTable.value.sheet_name = $event),
                      placeholder: "Select or type sheet name",
                      "column-options": sheetNames.value,
                      "is-loading": !sheetNamesLoaded.value
                    }, null, 8, ["modelValue", "column-options", "is-loading"]),
                    showWarning.value ? (openBlock(), createElementBlock("span", _hoisted_6, "⚠️")) : createCommentVNode("", true)
                  ])
                ]),
                _: 1
              })
            ]),
            createBaseVNode("div", _hoisted_7, [
              createVNode(_component_el_checkbox, {
                modelValue: localExcelTable.value.has_headers,
                "onUpdate:modelValue": _cache[1] || (_cache[1] = ($event) => localExcelTable.value.has_headers = $event),
                label: "Has headers",
                size: "large"
              }, null, 8, ["modelValue"]),
              createVNode(_component_el_checkbox, {
                modelValue: localExcelTable.value.type_inference,
                "onUpdate:modelValue": _cache[2] || (_cache[2] = ($event) => localExcelTable.value.type_inference = $event),
                label: "Type inference",
                size: "large"
              }, null, 8, ["modelValue"])
            ]),
            _cache[15] || (_cache[15] = createBaseVNode("hr", { class: "section-divider" }, null, -1)),
            createBaseVNode("div", _hoisted_8, [
              createBaseVNode("button", {
                class: "toggle-button",
                onClick: toggleOptionalSettings
              }, toDisplayString(showOptionalSettings.value ? "Hide" : "Show") + " Optional Settings ", 1)
            ]),
            showOptionalSettings.value ? (openBlock(), createElementBlock("div", _hoisted_9, [
              _cache[12] || (_cache[12] = createBaseVNode("hr", { class: "section-divider" }, null, -1)),
              _cache[13] || (_cache[13] = createBaseVNode("div", { class: "table-sizes" }, "Table sizes", -1)),
              createBaseVNode("div", _hoisted_10, [
                createBaseVNode("div", _hoisted_11, [
                  _cache[8] || (_cache[8] = createBaseVNode("label", { for: "start-row" }, "Start Row", -1)),
                  withDirectives(createBaseVNode("input", {
                    id: "start-row",
                    "onUpdate:modelValue": _cache[3] || (_cache[3] = ($event) => localExcelTable.value.start_row = $event),
                    type: "number",
                    class: "compact-input"
                  }, null, 512), [
                    [
                      vModelText,
                      localExcelTable.value.start_row,
                      void 0,
                      { number: true }
                    ]
                  ])
                ]),
                createBaseVNode("div", _hoisted_12, [
                  _cache[9] || (_cache[9] = createBaseVNode("label", { for: "end-row" }, "End Row", -1)),
                  withDirectives(createBaseVNode("input", {
                    id: "end-row",
                    "onUpdate:modelValue": _cache[4] || (_cache[4] = ($event) => localExcelTable.value.end_row = $event),
                    type: "number",
                    class: "compact-input"
                  }, null, 512), [
                    [
                      vModelText,
                      localExcelTable.value.end_row,
                      void 0,
                      { number: true }
                    ]
                  ])
                ])
              ]),
              _cache[14] || (_cache[14] = createBaseVNode("hr", { class: "section-divider" }, null, -1)),
              createBaseVNode("div", _hoisted_13, [
                createBaseVNode("div", _hoisted_14, [
                  _cache[10] || (_cache[10] = createBaseVNode("label", { for: "start-column" }, "Start Column", -1)),
                  withDirectives(createBaseVNode("input", {
                    id: "start-column",
                    "onUpdate:modelValue": _cache[5] || (_cache[5] = ($event) => localExcelTable.value.start_column = $event),
                    type: "number",
                    class: "compact-input"
                  }, null, 512), [
                    [
                      vModelText,
                      localExcelTable.value.start_column,
                      void 0,
                      { number: true }
                    ]
                  ])
                ]),
                createBaseVNode("div", _hoisted_15, [
                  _cache[11] || (_cache[11] = createBaseVNode("label", { for: "end-column" }, "End Column", -1)),
                  withDirectives(createBaseVNode("input", {
                    id: "end-column",
                    "onUpdate:modelValue": _cache[6] || (_cache[6] = ($event) => localExcelTable.value.end_column = $event),
                    type: "number",
                    class: "compact-input"
                  }, null, 512), [
                    [
                      vModelText,
                      localExcelTable.value.end_column,
                      void 0,
                      { number: true }
                    ]
                  ])
                ])
              ])
            ])) : createCommentVNode("", true)
          ])) : createCommentVNode("", true)
        ])
      ])) : (openBlock(), createBlock(unref(CodeLoader), { key: 1 }));
    };
  }
});
const readExcel_vue_vue_type_style_index_0_scoped_13a180bf_lang = "";
const ExcelTableConfig = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-13a180bf"]]);
export {
  ExcelTableConfig as default
};
