import { d as defineComponent, r as ref, l as computed, n as onMounted, o as onUnmounted, m as watch, R as nextTick, c as openBlock, e as createElementBlock, p as createBaseVNode, t as toDisplayString, a8 as withDirectives, a9 as vModelText, s as normalizeClass, f as createVNode, w as withCtx, F as Fragment, q as renderList, v as withModifiers, i as createCommentVNode, ac as Transition, _ as _export_sfc } from "./index-5429bbf8.js";
const _hoisted_1 = { class: "input-wrapper" };
const _hoisted_2 = ["placeholder", "aria-expanded", "aria-controls", "aria-activedescendant", "disabled"];
const _hoisted_3 = { class: "icon-container" };
const _hoisted_4 = {
  key: 0,
  class: "spinner"
};
const _hoisted_5 = {
  key: 1,
  class: "dropdown-icon",
  viewBox: "0 0 20 20",
  fill: "currentColor"
};
const _hoisted_6 = {
  key: 0,
  class: "options-container"
};
const _hoisted_7 = ["id"];
const _hoisted_8 = ["id", "aria-selected", "onMouseenter", "onMousedown"];
const _hoisted_9 = {
  key: 0,
  class: "no-options"
};
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "dropDown",
  props: {
    modelValue: {
      type: String,
      default: ""
    },
    columnOptions: {
      type: Array,
      required: true,
      default: () => []
    },
    placeholder: {
      type: String,
      default: "Select an option"
    },
    label: {
      type: String,
      default: "Dropdown"
    },
    allowOther: {
      type: Boolean,
      default: true
    },
    isLoading: {
      type: Boolean,
      default: false
    }
  },
  emits: ["update:modelValue", "error", "update:value"],
  setup(__props, { emit: __emit }) {
    const props = __props;
    const emits = __emit;
    const isLoaded = ref(false);
    const inputValue = ref(props.modelValue);
    const selectedValue = ref(props.modelValue);
    const showOptions = ref(false);
    const activeIndex = ref(-1);
    const hasError = ref(false);
    const dropdownRef = ref(null);
    const uniqueId = `dropdown-${Math.random().toString(36).substr(2, 9)}`;
    let inputTimeout = null;
    const column_options = computed(() => props.columnOptions || []);
    const hasTyped = ref(false);
    const displayedOptions = computed(() => {
      if (!Array.isArray(column_options.value))
        return [];
      if (!hasTyped.value)
        return column_options.value;
      return column_options.value.filter(
        (option) => option.toLowerCase().includes(inputValue.value.toLowerCase())
      );
    });
    const onFocus = () => {
      showOptions.value = true;
      hasTyped.value = false;
      nextTick(() => {
        positionDropdown();
      });
    };
    const onInput = () => {
      showOptions.value = true;
      hasError.value = false;
      activeIndex.value = -1;
      hasTyped.value = true;
      if (inputTimeout)
        clearTimeout(inputTimeout);
      if (props.allowOther) {
        inputTimeout = window.setTimeout(() => {
          doUpdate();
        }, 300);
      }
      nextTick(() => {
        positionDropdown();
      });
    };
    const filteredOptions = computed(() => {
      if (!Array.isArray(column_options.value))
        return [];
      return column_options.value.filter(
        (option) => option.toLowerCase().includes(inputValue.value.toLowerCase())
      );
    });
    const activeDescendant = computed(
      () => activeIndex.value >= 0 ? `${uniqueId}-option-${activeIndex.value}` : void 0
    );
    const selectOption = (option) => {
      inputValue.value = option;
      selectedValue.value = option;
      showOptions.value = false;
      hasError.value = false;
      emits("update:modelValue", option);
      emits("update:value", option);
    };
    const doUpdate = () => {
      if (!props.allowOther && !column_options.value.includes(inputValue.value)) {
        hasError.value = true;
        emits("error", "Invalid option selected");
        inputValue.value = selectedValue.value || "";
      } else {
        hasError.value = false;
        selectedValue.value = inputValue.value;
        emits("update:modelValue", inputValue.value);
        emits("update:value", inputValue.value);
      }
    };
    const onBlur = () => {
      setTimeout(() => {
        showOptions.value = false;
        doUpdate();
      }, 150);
    };
    const onKeyDown = (event) => {
      switch (event.key) {
        case "ArrowDown":
          event.preventDefault();
          if (!showOptions.value) {
            showOptions.value = true;
            nextTick(() => {
              positionDropdown();
            });
          }
          activeIndex.value = Math.min(activeIndex.value + 1, filteredOptions.value.length - 1);
          scrollActiveOptionIntoView();
          break;
        case "ArrowUp":
          event.preventDefault();
          activeIndex.value = Math.max(activeIndex.value - 1, 0);
          scrollActiveOptionIntoView();
          break;
        case "Enter":
          if (activeIndex.value >= 0 && filteredOptions.value[activeIndex.value]) {
            event.preventDefault();
            selectOption(filteredOptions.value[activeIndex.value]);
          } else if (showOptions.value) {
            showOptions.value = false;
            doUpdate();
          } else {
            showOptions.value = true;
            nextTick(() => {
              positionDropdown();
            });
          }
          break;
        case "Escape":
          event.preventDefault();
          showOptions.value = false;
          break;
      }
    };
    const scrollActiveOptionIntoView = () => {
      nextTick(() => {
        const activeElement = document.getElementById(`${uniqueId}-option-${activeIndex.value}`);
        if (activeElement) {
          activeElement.scrollIntoView({ block: "nearest", behavior: "smooth" });
        }
      });
    };
    const positionDropdown = () => {
      var _a, _b, _c;
      const inputEl = (_a = dropdownRef.value) == null ? void 0 : _a.querySelector(".select-box");
      const dropdownEl = (_b = dropdownRef.value) == null ? void 0 : _b.querySelector(".options-container");
      if (inputEl && dropdownEl) {
        const inputRect = inputEl.getBoundingClientRect();
        const dropdownEl2 = (_c = dropdownRef.value) == null ? void 0 : _c.querySelector(".options-container");
        if (dropdownEl2) {
          dropdownEl2.style.width = `${inputRect.width}px`;
          dropdownEl2.style.top = `${inputRect.bottom}px`;
          dropdownEl2.style.left = `${inputRect.left}px`;
          const dropdownHeight = dropdownEl2.offsetHeight;
          const viewportHeight = window.innerHeight;
          const spaceBelow = viewportHeight - inputRect.bottom;
          if (dropdownHeight > spaceBelow) {
            dropdownEl2.style.top = `${inputRect.top - dropdownHeight}px`;
          }
        }
      }
    };
    const handleClickOutside = (event) => {
      if (dropdownRef.value && !dropdownRef.value.contains(event.target)) {
        showOptions.value = false;
        doUpdate();
      }
    };
    const handleScroll = () => {
      if (showOptions.value) {
        positionDropdown();
      }
    };
    onMounted(() => {
      document.addEventListener("click", handleClickOutside);
      window.addEventListener("scroll", handleScroll, true);
      window.addEventListener("resize", positionDropdown);
      isLoaded.value = true;
    });
    onUnmounted(() => {
      document.removeEventListener("click", handleClickOutside);
      window.removeEventListener("scroll", handleScroll, true);
      window.removeEventListener("resize", positionDropdown);
      if (inputTimeout) {
        clearTimeout(inputTimeout);
      }
      isLoaded.value = false;
    });
    watch(
      () => props.modelValue,
      (newValue) => {
        inputValue.value = newValue || "";
        selectedValue.value = newValue || "";
      }
    );
    watch(
      () => showOptions.value,
      (isOpen) => {
        if (isOpen) {
          nextTick(() => {
            positionDropdown();
          });
        }
      }
    );
    return (_ctx, _cache) => {
      return isLoaded.value ? (openBlock(), createElementBlock("div", {
        key: 0,
        ref_key: "dropdownRef",
        ref: dropdownRef,
        class: "dropdown-container"
      }, [
        createBaseVNode("label", {
          for: uniqueId,
          class: "sr-only"
        }, toDisplayString(__props.label), 1),
        createBaseVNode("div", _hoisted_1, [
          withDirectives(createBaseVNode("input", {
            id: uniqueId,
            "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => inputValue.value = $event),
            type: "text",
            class: normalizeClass(["select-box", { "has-error": hasError.value && !__props.isLoading }]),
            placeholder: __props.isLoading ? "Loading..." : __props.placeholder,
            "aria-expanded": showOptions.value,
            "aria-controls": `${uniqueId}-listbox`,
            "aria-activedescendant": activeDescendant.value,
            disabled: __props.isLoading,
            role: "combobox",
            onFocus,
            onInput,
            onBlur,
            onKeydown: onKeyDown
          }, null, 42, _hoisted_2), [
            [vModelText, inputValue.value]
          ]),
          createBaseVNode("div", _hoisted_3, [
            __props.isLoading ? (openBlock(), createElementBlock("div", _hoisted_4)) : (openBlock(), createElementBlock("svg", _hoisted_5, _cache[1] || (_cache[1] = [
              createBaseVNode("path", {
                "fill-rule": "evenodd",
                d: "M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z",
                "clip-rule": "evenodd"
              }, null, -1)
            ])))
          ])
        ]),
        createVNode(Transition, { name: "fade" }, {
          default: withCtx(() => [
            showOptions.value && !__props.isLoading && Array.isArray(column_options.value) ? (openBlock(), createElementBlock("div", _hoisted_6, [
              createBaseVNode("ul", {
                id: `${uniqueId}-listbox`,
                class: "options-list",
                role: "listbox"
              }, [
                (openBlock(true), createElementBlock(Fragment, null, renderList(displayedOptions.value, (option, index) => {
                  return openBlock(), createElementBlock("li", {
                    id: `${uniqueId}-option-${index}`,
                    key: option,
                    class: normalizeClass(["option-item", { "is-active": index === activeIndex.value }]),
                    role: "option",
                    "aria-selected": inputValue.value === option,
                    onMouseenter: ($event) => activeIndex.value = index,
                    onMousedown: withModifiers(($event) => selectOption(option), ["prevent"])
                  }, toDisplayString(option), 43, _hoisted_8);
                }), 128)),
                displayedOptions.value.length === 0 ? (openBlock(), createElementBlock("li", _hoisted_9, "No options found")) : createCommentVNode("", true)
              ], 8, _hoisted_7)
            ])) : createCommentVNode("", true)
          ]),
          _: 1
        })
      ], 512)) : createCommentVNode("", true);
    };
  }
});
const dropDown_vue_vue_type_style_index_0_scoped_0fe9cf29_lang = "";
const ColumnSelector = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-0fe9cf29"]]);
export {
  ColumnSelector as C
};
