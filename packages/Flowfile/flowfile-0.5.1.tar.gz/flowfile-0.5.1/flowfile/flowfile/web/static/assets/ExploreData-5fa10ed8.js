import { C as CodeLoader } from "./vue-content-loader.es-2c8e608f.js";
import VueGraphicWalker from "./VueGraphicWalker-e51b9924.js";
import { a as axios, d as defineComponent, r as ref, l as computed, c as openBlock, e as createElementBlock, h as createBlock, u as unref, p as createBaseVNode, t as toDisplayString, _ as _export_sfc } from "./index-5429bbf8.js";
import { u as useNodeStore } from "./vue-codemirror.esm-41b0e0d7.js";
import { u as useItemStore } from "./designer-9633482a.js";
const fetchGraphicWalkerData = async (flowId, nodeId) => {
  var _a, _b;
  console.log(`[GraphicWalker] Fetching data for flow ${flowId}, node ${nodeId}`);
  try {
    const response = await axios.get("/analysis_data/graphic_walker_input", {
      params: { flow_id: flowId, node_id: nodeId },
      headers: { Accept: "application/json" },
      timeout: 3e4
      // Add timeout
    });
    if (!response.data || !response.data.graphic_walker_input) {
      throw new Error("Invalid response data structure");
    }
    console.log(
      `[GraphicWalker] Data fetched successfully with ${((_b = (_a = response.data.graphic_walker_input.dataModel) == null ? void 0 : _a.data) == null ? void 0 : _b.length) || 0} rows`
    );
    return response.data;
  } catch (error) {
    if (error.response) {
      console.error(`[GraphicWalker] Server error ${error.response.status}:`, error.response.data);
    } else if (error.request) {
      console.error("[GraphicWalker] No response received:", error.request);
    } else {
      console.error("[GraphicWalker] Request error:", error.message);
    }
    throw error;
  }
};
const _hoisted_1 = { class: "explore-data-container" };
const _hoisted_2 = {
  key: 1,
  class: "error-display"
};
const _hoisted_3 = {
  key: 2,
  class: "graphic-walker-wrapper"
};
const _hoisted_4 = {
  key: 1,
  class: "empty-data-message"
};
const _hoisted_5 = {
  key: 3,
  class: "fallback-message"
};
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "ExploreData",
  setup(__props, { expose: __expose }) {
    const isLoading = ref(false);
    const nodeData = ref(null);
    const chartList = ref([]);
    const data = ref([]);
    const fields = ref([]);
    const errorMessage = ref(null);
    const nodeStore = useNodeStore();
    const globalNodeId = ref(-1);
    const windowStore = useItemStore();
    const vueGraphicWalkerRef = ref(null);
    const canDisplayVisualization = computed(() => !isLoading.value && !errorMessage.value);
    const loadNodeData = async (nodeId) => {
      var _a, _b;
      isLoading.value = true;
      errorMessage.value = null;
      globalNodeId.value = nodeId;
      nodeData.value = null;
      data.value = [];
      fields.value = [];
      chartList.value = [];
      windowStore.setFullScreen("nodeSettings", true);
      try {
        const fetchedNodeData = await fetchGraphicWalkerData(nodeStore.flow_id, nodeId);
        if (!(fetchedNodeData == null ? void 0 : fetchedNodeData.graphic_walker_input))
          throw new Error("Received invalid data structure from backend.");
        nodeData.value = fetchedNodeData;
        const inputData = fetchedNodeData.graphic_walker_input;
        fields.value = ((_a = inputData.dataModel) == null ? void 0 : _a.fields) || [];
        data.value = ((_b = inputData.dataModel) == null ? void 0 : _b.data) || [];
        chartList.value = inputData.specList || [];
      } catch (error) {
        console.error("Error loading GraphicWalker data:", error);
        if (error.response && error.response.status === 422) {
          errorMessage.value = "The analysis flow has not been run yet.";
        } else if (error instanceof Error) {
          errorMessage.value = `Failed to load data: ${error.message}`;
        } else {
          errorMessage.value = "An unknown error occurred while loading data.";
        }
      } finally {
        isLoading.value = false;
      }
    };
    const getCurrentSpec = async () => {
      if (!vueGraphicWalkerRef.value) {
        console.error("Cannot get spec: GraphicWalker component reference is missing.");
        errorMessage.value = "Cannot get spec: Component reference missing.";
        return null;
      }
      try {
        const exportedCharts = await vueGraphicWalkerRef.value.exportCode();
        if (exportedCharts === null) {
          console.error("Failed to export chart specification (method returned null or failed).");
          errorMessage.value = "Failed to retrieve current chart configuration.";
          return null;
        }
        if (exportedCharts.length === 0) {
          console.log("No charts were exported from Graphic Walker.");
          return [];
        }
        return exportedCharts;
      } catch (error) {
        console.error("Error calling getCurrentSpec or processing result:", error);
        errorMessage.value = `Failed to process configuration: ${error.message || "Unknown error"}`;
        return null;
      }
    };
    const saveSpecToNodeStore = async (specsToSave) => {
      if (!nodeData.value) {
        console.error("Cannot save: Original node data context is missing.");
        errorMessage.value = "Cannot save: Missing original node data.";
        return false;
      }
      try {
        const saveData = {
          ...nodeData.value,
          graphic_walker_input: {
            ...nodeData.value.graphic_walker_input,
            specList: specsToSave,
            dataModel: { data: [], fields: [] }
          }
        };
        await nodeStore.updateSettingsDirectly(saveData);
        console.log("Node settings updated successfully.");
        return true;
      } catch (error) {
        console.error("Error saving spec to node store:", error);
        errorMessage.value = `Failed to save configuration: ${error.message || "Unknown error"}`;
        return false;
      }
    };
    const pushNodeData = async () => {
      errorMessage.value = null;
      windowStore.setFullScreen("nodeSettings", false);
      const currentSpec = await getCurrentSpec();
      if (currentSpec === null) {
        console.log("Spec retrieval failed, skipping save.");
        return;
      }
      if (currentSpec.length === 0) {
        console.log("No chart configurations exported, skipping save.");
        return;
      }
      const saveSuccess = await saveSpecToNodeStore(currentSpec);
      if (saveSuccess) {
        console.log("Save process completed successfully.");
      } else {
        console.log("Save process failed.");
      }
    };
    __expose({
      loadNodeData,
      pushNodeData
      // Expose the main save action
    });
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", _hoisted_1, [
        isLoading.value ? (openBlock(), createBlock(unref(CodeLoader), { key: 0 })) : errorMessage.value ? (openBlock(), createElementBlock("div", _hoisted_2, [
          createBaseVNode("p", null, "⚠️ Error: " + toDisplayString(errorMessage.value), 1)
        ])) : canDisplayVisualization.value ? (openBlock(), createElementBlock("div", _hoisted_3, [
          data.value.length > 0 && fields.value.length > 0 ? (openBlock(), createBlock(VueGraphicWalker, {
            key: 0,
            ref_key: "vueGraphicWalkerRef",
            ref: vueGraphicWalkerRef,
            appearance: "light",
            data: data.value,
            fields: fields.value,
            "spec-list": chartList.value
          }, null, 8, ["data", "fields", "spec-list"])) : (openBlock(), createElementBlock("div", _hoisted_4, " Data loaded, but the dataset appears to be empty or lacks defined fields. "))
        ])) : (openBlock(), createElementBlock("div", _hoisted_5, "Please load data for the node."))
      ]);
    };
  }
});
const ExploreData_vue_vue_type_style_index_0_scoped_1a3f5721_lang = "";
const ExploreData = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-1a3f5721"]]);
export {
  ExploreData as default
};
