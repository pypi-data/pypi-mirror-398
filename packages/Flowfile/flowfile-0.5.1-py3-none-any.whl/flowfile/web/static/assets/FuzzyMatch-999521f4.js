import { d as defineComponent, r as ref, l as computed, n as onMounted, R as nextTick, c as openBlock, e as createElementBlock, f as createVNode, w as withCtx, p as createBaseVNode, s as normalizeClass, F as Fragment, q as renderList, h as createBlock, i as createCommentVNode, g as createTextVNode, t as toDisplayString, a8 as withDirectives, a9 as vModelText, ak as vModelSelect, u as unref, _ as _export_sfc } from "./index-5429bbf8.js";
import { u as useNodeStore } from "./vue-codemirror.esm-41b0e0d7.js";
import { C as ColumnSelector } from "./dropDown-614b998d.js";
import { s as selectDynamic } from "./selectDynamic-92e25ee3.js";
import { u as unavailableField } from "./UnavailableFields-a03f512c.js";
import { G as GenericNodeSettings } from "./genericNodeSettings-4fe5f36b.js";
import { C as CodeLoader } from "./vue-content-loader.es-2c8e608f.js";
import "./designer-9633482a.js";
const _hoisted_1 = {
  key: 0,
  class: "fuzzy-join-container"
};
const _hoisted_2 = { class: "tabs-navigation" };
const _hoisted_3 = {
  key: 0,
  class: "tab-content"
};
const _hoisted_4 = { class: "settings-card" };
const _hoisted_5 = { class: "card-content" };
const _hoisted_6 = {
  key: 0,
  class: "join-settings"
};
const _hoisted_7 = { class: "setting-header" };
const _hoisted_8 = { class: "setting-title" };
const _hoisted_9 = ["onClick"];
const _hoisted_10 = { class: "columns-grid" };
const _hoisted_11 = { class: "column-field" };
const _hoisted_12 = { class: "column-field" };
const _hoisted_13 = { class: "settings-grid" };
const _hoisted_14 = { class: "threshold-field" };
const _hoisted_15 = { class: "range-container" };
const _hoisted_16 = ["id", "onUpdate:modelValue"];
const _hoisted_17 = { class: "range-value" };
const _hoisted_18 = { class: "select-field" };
const _hoisted_19 = { class: "select-wrapper" };
const _hoisted_20 = ["id", "onUpdate:modelValue"];
const _hoisted_21 = ["value"];
const _hoisted_22 = {
  key: 1,
  class: "tab-content"
};
const _hoisted_23 = { class: "settings-card" };
const _hoisted_24 = { class: "card-content" };
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "FuzzyMatch",
  setup(__props, { expose: __expose }) {
    const activeTab = ref("match");
    const containsVal = (arr, val) => {
      return arr.includes(val);
    };
    const result = ref(null);
    const nodeStore = useNodeStore();
    const isLoaded = ref(false);
    const nodeFuzzyJoin = ref(null);
    const createSelectInput = (field) => {
      return {
        old_name: field,
        new_name: field,
        position: 0,
        keep: true,
        is_altered: false,
        data_type_change: false,
        is_available: true,
        original_position: 0
      };
    };
    const updateSelectInputsHandler = (updatedInputs, isLeft) => {
      if (isLeft && nodeFuzzyJoin.value) {
        nodeFuzzyJoin.value.join_input.left_select.renames = updatedInputs;
      } else if (nodeFuzzyJoin.value) {
        nodeFuzzyJoin.value.join_input.right_select.renames = updatedInputs;
      }
    };
    const fuzzyMatchOptions = [
      { value: "levenshtein", label: "Levenshtein" },
      { value: "jaro", label: "Jaro" },
      { value: "jaro_winkler", label: "Jaro Winkler" },
      { value: "hamming", label: "Hamming" },
      { value: "damerau_levenshtein", label: "Damerau Levenshtein" },
      { value: "indel", label: "Indel" }
    ];
    const hasInvalidFields = computed(() => {
      var _a;
      if (!((_a = nodeFuzzyJoin.value) == null ? void 0 : _a.join_input) || !result.value) {
        return false;
      }
      return nodeFuzzyJoin.value.join_input.join_mapping.some((fuzzyMap) => {
        var _a2, _b, _c, _d;
        const leftValid = containsVal(((_b = (_a2 = result.value) == null ? void 0 : _a2.main_input) == null ? void 0 : _b.columns) ?? [], fuzzyMap.left_col);
        const rightValid = containsVal(((_d = (_c = result.value) == null ? void 0 : _c.right_input) == null ? void 0 : _d.columns) ?? [], fuzzyMap.right_col);
        return !(leftValid && rightValid);
      });
    });
    const getEmptySetup = (left_fields, right_fields) => {
      return {
        join_mapping: [
          {
            left_col: "",
            right_col: "",
            threshold_score: 75,
            fuzzy_type: "levenshtein",
            valid: true
          }
        ],
        left_select: {
          renames: left_fields.map(createSelectInput)
        },
        right_select: {
          renames: right_fields.map(createSelectInput)
        },
        aggregate_output: false
      };
    };
    const loadNodeData = async (nodeId) => {
      var _a, _b, _c, _d, _e, _f;
      result.value = await nodeStore.getNodeData(nodeId, false);
      nodeFuzzyJoin.value = (_a = result.value) == null ? void 0 : _a.setting_input;
      if (!((_b = nodeFuzzyJoin.value) == null ? void 0 : _b.is_setup) && ((_c = result.value) == null ? void 0 : _c.main_input)) {
        if (nodeFuzzyJoin.value) {
          if (((_d = result.value) == null ? void 0 : _d.main_input.columns) && ((_f = (_e = result.value) == null ? void 0 : _e.right_input) == null ? void 0 : _f.columns)) {
            nodeFuzzyJoin.value.join_input = getEmptySetup(
              result.value.main_input.columns,
              result.value.right_input.columns
            );
            isLoaded.value = true;
          }
        }
      } else {
        isLoaded.value = true;
      }
      isLoaded.value = true;
    };
    const addJoinCondition = () => {
      var _a, _b;
      const newCondition = {
        left_col: "",
        right_col: "",
        threshold_score: 75,
        fuzzy_type: "levenshtein",
        valid: true
      };
      (_b = (_a = nodeFuzzyJoin.value) == null ? void 0 : _a.join_input) == null ? void 0 : _b.join_mapping.push(newCondition);
    };
    const removeJoinCondition = (index) => {
      var _a, _b;
      (_b = (_a = nodeFuzzyJoin.value) == null ? void 0 : _a.join_input) == null ? void 0 : _b.join_mapping.splice(index, 1);
    };
    const handleChange = (newValue, index, side) => {
      var _a, _b;
      if (side === "left") {
        if ((_a = nodeFuzzyJoin.value) == null ? void 0 : _a.join_input) {
          nodeFuzzyJoin.value.join_input.join_mapping[index].left_col = newValue;
        }
      } else {
        if ((_b = nodeFuzzyJoin.value) == null ? void 0 : _b.join_input) {
          nodeFuzzyJoin.value.join_input.join_mapping[index].right_col = newValue;
        }
      }
    };
    const pushNodeData = async () => {
      if (nodeFuzzyJoin.value) {
        nodeFuzzyJoin.value.is_setup = true;
      }
      nodeStore.updateSettings(nodeFuzzyJoin);
      if (hasInvalidFields.value && nodeFuzzyJoin.value) {
        nodeStore.setNodeValidation(nodeFuzzyJoin.value.node_id, {
          isValid: false,
          error: "Join fields are not valid"
        });
      } else if (nodeFuzzyJoin.value) {
        nodeStore.setNodeValidation(nodeFuzzyJoin.value.node_id, {
          isValid: true,
          error: ""
        });
      }
    };
    __expose({
      loadNodeData,
      pushNodeData,
      hasInvalidFields
    });
    onMounted(async () => {
      await nextTick();
    });
    return (_ctx, _cache) => {
      return isLoaded.value && nodeFuzzyJoin.value ? (openBlock(), createElementBlock("div", _hoisted_1, [
        createVNode(GenericNodeSettings, {
          modelValue: nodeFuzzyJoin.value,
          "onUpdate:modelValue": _cache[5] || (_cache[5] = ($event) => nodeFuzzyJoin.value = $event)
        }, {
          default: withCtx(() => {
            var _a, _b, _c, _d, _e, _f;
            return [
              createBaseVNode("div", _hoisted_2, [
                createBaseVNode("button", {
                  class: normalizeClass(["tab-button", { active: activeTab.value === "match" }]),
                  onClick: _cache[0] || (_cache[0] = ($event) => activeTab.value = "match")
                }, " Match Settings ", 2),
                createBaseVNode("button", {
                  class: normalizeClass(["tab-button", { active: activeTab.value === "fields" }]),
                  onClick: _cache[1] || (_cache[1] = ($event) => activeTab.value = "fields")
                }, " Select Fields ", 2)
              ]),
              activeTab.value === "match" ? (openBlock(), createElementBlock("div", _hoisted_3, [
                createBaseVNode("div", _hoisted_4, [
                  _cache[10] || (_cache[10] = createBaseVNode("div", { class: "card-header" }, [
                    createBaseVNode("h3", { class: "section-title" }, "Fuzzy match settings")
                  ], -1)),
                  createBaseVNode("div", _hoisted_5, [
                    ((_a = nodeFuzzyJoin.value) == null ? void 0 : _a.join_input) ? (openBlock(), createElementBlock("div", _hoisted_6, [
                      (openBlock(true), createElementBlock(Fragment, null, renderList((_b = nodeFuzzyJoin.value) == null ? void 0 : _b.join_input.join_mapping, (fuzzyMap, index) => {
                        var _a2, _b2, _c2, _d2, _e2, _f2, _g, _h, _i;
                        return openBlock(), createElementBlock("div", {
                          key: index,
                          class: "setting-panel"
                        }, [
                          createBaseVNode("div", _hoisted_7, [
                            createBaseVNode("h4", _hoisted_8, [
                              !(containsVal(((_b2 = (_a2 = result.value) == null ? void 0 : _a2.main_input) == null ? void 0 : _b2.columns) ?? [], fuzzyMap.left_col) && containsVal(((_d2 = (_c2 = result.value) == null ? void 0 : _c2.right_input) == null ? void 0 : _d2.columns) ?? [], fuzzyMap.right_col)) ? (openBlock(), createBlock(unavailableField, {
                                key: 0,
                                "tooltip-text": "Join is not valid",
                                class: "unavailable-field"
                              })) : createCommentVNode("", true),
                              createTextVNode(" Setting " + toDisplayString(index + 1), 1)
                            ]),
                            ((_e2 = nodeFuzzyJoin.value) == null ? void 0 : _e2.join_input.join_mapping.length) > 1 ? (openBlock(), createElementBlock("button", {
                              key: 0,
                              class: "remove-button",
                              type: "button",
                              "aria-label": "Remove setting",
                              onClick: ($event) => removeJoinCondition(index)
                            }, " Remove setting ", 8, _hoisted_9)) : createCommentVNode("", true)
                          ]),
                          createBaseVNode("div", _hoisted_10, [
                            createBaseVNode("div", _hoisted_11, [
                              _cache[6] || (_cache[6] = createBaseVNode("label", null, "Left column", -1)),
                              createVNode(ColumnSelector, {
                                modelValue: fuzzyMap.left_col,
                                "onUpdate:modelValue": ($event) => fuzzyMap.left_col = $event,
                                value: fuzzyMap.left_col,
                                "column-options": (_g = (_f2 = result.value) == null ? void 0 : _f2.main_input) == null ? void 0 : _g.columns,
                                "onUpdate:value": (value) => handleChange(value, index, "left")
                              }, null, 8, ["modelValue", "onUpdate:modelValue", "value", "column-options", "onUpdate:value"])
                            ]),
                            createBaseVNode("div", _hoisted_12, [
                              _cache[7] || (_cache[7] = createBaseVNode("label", null, "Right column", -1)),
                              createVNode(ColumnSelector, {
                                modelValue: fuzzyMap.right_col,
                                "onUpdate:modelValue": ($event) => fuzzyMap.right_col = $event,
                                value: fuzzyMap.right_col,
                                "column-options": (_i = (_h = result.value) == null ? void 0 : _h.right_input) == null ? void 0 : _i.columns,
                                "onUpdate:value": (value) => handleChange(value, index, "right")
                              }, null, 8, ["modelValue", "onUpdate:modelValue", "value", "column-options", "onUpdate:value"])
                            ])
                          ]),
                          createBaseVNode("div", _hoisted_13, [
                            createBaseVNode("div", _hoisted_14, [
                              _cache[8] || (_cache[8] = createBaseVNode("label", { for: "threshold-score" }, "Threshold score", -1)),
                              createBaseVNode("div", _hoisted_15, [
                                withDirectives(createBaseVNode("input", {
                                  id: `threshold-score-${index}`,
                                  "onUpdate:modelValue": ($event) => fuzzyMap.threshold_score = $event,
                                  type: "range",
                                  min: "0",
                                  max: "100",
                                  step: "1",
                                  class: "range-slider"
                                }, null, 8, _hoisted_16), [
                                  [vModelText, fuzzyMap.threshold_score]
                                ]),
                                createBaseVNode("div", _hoisted_17, toDisplayString(fuzzyMap.threshold_score) + "%", 1)
                              ])
                            ]),
                            createBaseVNode("div", _hoisted_18, [
                              _cache[9] || (_cache[9] = createBaseVNode("label", { for: "fuzzy-type" }, "Match algorithm", -1)),
                              createBaseVNode("div", _hoisted_19, [
                                withDirectives(createBaseVNode("select", {
                                  id: `fuzzy-type-${index}`,
                                  "onUpdate:modelValue": ($event) => fuzzyMap.fuzzy_type = $event,
                                  class: "select-input"
                                }, [
                                  (openBlock(), createElementBlock(Fragment, null, renderList(fuzzyMatchOptions, (option) => {
                                    return createBaseVNode("option", {
                                      key: option.value,
                                      value: option.value
                                    }, toDisplayString(option.label), 9, _hoisted_21);
                                  }), 64))
                                ], 8, _hoisted_20), [
                                  [vModelSelect, fuzzyMap.fuzzy_type]
                                ])
                              ])
                            ])
                          ])
                        ]);
                      }), 128)),
                      createBaseVNode("button", {
                        class: "add-button",
                        type: "button",
                        onClick: _cache[2] || (_cache[2] = ($event) => addJoinCondition())
                      }, " Add setting ")
                    ])) : createCommentVNode("", true)
                  ])
                ])
              ])) : createCommentVNode("", true),
              activeTab.value === "fields" ? (openBlock(), createElementBlock("div", _hoisted_22, [
                createBaseVNode("div", _hoisted_23, [
                  _cache[11] || (_cache[11] = createBaseVNode("div", { class: "card-header" }, [
                    createBaseVNode("h3", { class: "section-title" }, "Select fields to include")
                  ], -1)),
                  createBaseVNode("div", _hoisted_24, [
                    ((_c = nodeFuzzyJoin.value) == null ? void 0 : _c.join_input) ? (openBlock(), createBlock(selectDynamic, {
                      key: 0,
                      "select-inputs": (_d = nodeFuzzyJoin.value) == null ? void 0 : _d.join_input.right_select.renames,
                      "show-keep-option": true,
                      "show-headers": true,
                      "show-new-columns": false,
                      "show-title": true,
                      "show-data": true,
                      title: "Right data",
                      class: "select-section",
                      onUpdateSelectInputs: _cache[3] || (_cache[3] = (updatedInputs) => updateSelectInputsHandler(updatedInputs, false))
                    }, null, 8, ["select-inputs"])) : createCommentVNode("", true),
                    ((_e = nodeFuzzyJoin.value) == null ? void 0 : _e.join_input) ? (openBlock(), createBlock(selectDynamic, {
                      key: 1,
                      "select-inputs": (_f = nodeFuzzyJoin.value) == null ? void 0 : _f.join_input.left_select.renames,
                      "show-keep-option": true,
                      "show-title": true,
                      "show-headers": true,
                      "show-new-columns": false,
                      "show-data": true,
                      title: "Left data",
                      class: "select-section",
                      onUpdateSelectInputs: _cache[4] || (_cache[4] = (updatedInputs) => updateSelectInputsHandler(updatedInputs, true))
                    }, null, 8, ["select-inputs"])) : createCommentVNode("", true)
                  ])
                ])
              ])) : createCommentVNode("", true)
            ];
          }),
          _: 1
        }, 8, ["modelValue"])
      ])) : (openBlock(), createBlock(unref(CodeLoader), { key: 1 }));
    };
  }
});
const FuzzyMatch_vue_vue_type_style_index_0_scoped_3c562315_lang = "";
const FuzzyMatch = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-3c562315"]]);
export {
  FuzzyMatch as default
};
